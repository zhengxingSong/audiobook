"""Tests for job-related web APIs."""

from pathlib import Path

from fastapi.testclient import TestClient

from audiobook.repositories import JobRepository
from audiobook.schemas.jobs import JobProgressUpdate, JobRecord, JobRunResult
from audiobook.services.jobs import JobService
from audiobook.web import create_app


class SuccessfulRunner:
    """A deterministic runner used by web tests."""

    def run(self, job: JobRecord, on_progress) -> JobRunResult:
        on_progress(JobProgressUpdate(total_items=5, processed_items=5, current_stage="Completed"))
        output_path = Path(job.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"wave")
        report_path = Path(job.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text('{"status":"ok"}', encoding="utf-8")
        return JobRunResult(
            success=True,
            output_path=str(output_path),
            report_path=str(report_path),
            total_blocks=5,
            processed_blocks=5,
            total_fragments=5,
        )


class FailedRunner:
    """A deterministic failure runner used by web tests."""

    def run(self, job: JobRecord, on_progress) -> JobRunResult:
        on_progress(JobProgressUpdate(total_items=2, processed_items=1, failed_items=1, current_stage="Failed"))
        report_path = Path(job.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text('{"status":"failed","errors":["boom"]}', encoding="utf-8")
        return JobRunResult(
            success=False,
            report_path=str(report_path),
            errors=["boom"],
            total_blocks=2,
            processed_blocks=1,
            total_fragments=1,
            failed_blocks=["block_a"],
        )


def build_client(temp_dir: Path, runner) -> TestClient:
    repository = JobRepository(temp_dir / "jobs")
    service = JobService(repository=repository, runner=runner, run_inline=True)
    app = create_app(
        job_service=service,
        output_root=temp_dir / "output",
        voice_library_path=temp_dir / "voices",
    )
    return TestClient(app)


class TestJobsApi:
    """HTTP tests for job creation and inspection."""

    def test_create_job_from_upload_and_fetch_result(self, temp_dir: Path) -> None:
        client = build_client(temp_dir, SuccessfulRunner())

        response = client.post(
            "/api/jobs",
            files={"novel_file": ("novel.txt", b"content", "text/plain")},
            data={"output_name": "result.wav"},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["status"] == "succeeded"

        detail = client.get(f"/api/jobs/{payload['job_id']}")
        assert detail.status_code == 200
        assert detail.json()["status"] == "succeeded"

        result = client.get(f"/api/jobs/{payload['job_id']}/result")
        assert result.status_code == 200

    def test_failed_job_exposes_report_and_errors(self, temp_dir: Path) -> None:
        client = build_client(temp_dir, FailedRunner())

        response = client.post(
            "/api/jobs",
            files={"novel_file": ("novel.txt", b"content", "text/plain")},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["status"] == "failed"

        report = client.get(f"/api/jobs/{payload['job_id']}/report")
        errors = client.get(f"/api/jobs/{payload['job_id']}/errors")
        result = client.get(f"/api/jobs/{payload['job_id']}/result")

        assert report.status_code == 200
        assert errors.status_code == 200
        assert errors.json()["errors"] == ["boom"]
        assert result.status_code == 404

    def test_retry_endpoint_creates_new_job(self, temp_dir: Path) -> None:
        repository = JobRepository(temp_dir / "jobs")
        service = JobService(repository=repository, runner=FailedRunner(), run_inline=True)
        app = create_app(
            job_service=service,
            output_root=temp_dir / "output",
            voice_library_path=temp_dir / "voices",
        )
        client = TestClient(app)

        created = client.post(
            "/api/jobs",
            files={"novel_file": ("novel.txt", b"content", "text/plain")},
        ).json()

        service.runner = SuccessfulRunner()
        retried = client.post(f"/api/jobs/{created['job_id']}/retry")

        assert retried.status_code == 201
        assert retried.json()["job_id"] != created["job_id"]

    def test_system_checks_endpoint(self, temp_dir: Path) -> None:
        client = build_client(temp_dir, SuccessfulRunner())

        response = client.get("/api/system/checks")

        assert response.status_code == 200
        payload = response.json()
        assert payload["checks"]["output_root"]["ok"] is True
        assert payload["checks"]["voice_library"]["ok"] is True
