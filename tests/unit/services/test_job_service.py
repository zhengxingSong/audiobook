"""Tests for job service orchestration."""

from pathlib import Path

from audiobook.repositories import JobRepository
from audiobook.schemas.jobs import JobProgressUpdate, JobRecord, JobRunResult, JobStatus
from audiobook.services.jobs import JobService


class SuccessfulRunner:
    """A deterministic runner that succeeds and writes output."""

    def run(self, job: JobRecord, on_progress) -> JobRunResult:
        on_progress(
            JobProgressUpdate(
                total_items=4,
                processed_items=4,
                current_stage="Completed",
            )
        )
        output_path = Path(job.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio-bytes")
        report_path = Path(job.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text('{"status":"ok"}', encoding="utf-8")
        return JobRunResult(
            success=True,
            output_path=str(output_path),
            report_path=str(report_path),
            total_blocks=4,
            processed_blocks=4,
            total_fragments=4,
        )


class FailedRunner:
    """A deterministic runner that fails with a report."""

    def run(self, job: JobRecord, on_progress) -> JobRunResult:
        on_progress(
            JobProgressUpdate(
                total_items=3,
                processed_items=2,
                failed_items=1,
                current_stage="Failed",
            )
        )
        report_path = Path(job.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text('{"status":"failed"}', encoding="utf-8")
        return JobRunResult(
            success=False,
            report_path=str(report_path),
            errors=["runner failed"],
            total_blocks=3,
            processed_blocks=2,
            total_fragments=2,
            failed_blocks=["block_001"],
        )


class TestJobService:
    """Job orchestration tests."""

    def test_create_job_from_upload_runs_to_success(self, temp_dir: Path) -> None:
        repository = JobRepository(temp_dir / "jobs")
        service = JobService(repository=repository, runner=SuccessfulRunner(), run_inline=True)

        record = service.create_job_from_upload(
            filename="novel.txt",
            data="hello".encode("utf-8"),
            output_name="result.wav",
        )

        assert record.status == JobStatus.SUCCEEDED
        assert Path(record.output_path).exists()
        assert Path(record.report_path).exists()

    def test_retry_creates_new_job(self, temp_dir: Path) -> None:
        repository = JobRepository(temp_dir / "jobs")
        service = JobService(repository=repository, runner=FailedRunner(), run_inline=True)
        failed = service.create_job_from_upload(
            filename="novel.txt",
            data="hello".encode("utf-8"),
        )

        service.runner = SuccessfulRunner()
        retried = service.retry_job(failed.job_id)

        assert retried.job_id != failed.job_id
        assert retried.status == JobStatus.SUCCEEDED

    def test_cancel_pending_job(self, temp_dir: Path) -> None:
        repository = JobRepository(temp_dir / "jobs")
        service = JobService(repository=repository, runner=SuccessfulRunner(), run_inline=False)
        record = JobRecord(
            job_id="job_cancel",
            status=JobStatus.PENDING,
            novel_name="Novel",
            input_path=str(temp_dir / "input.txt"),
            output_path=str(temp_dir / "result.wav"),
            report_path=str(temp_dir / "report.json"),
            output_name="result.wav",
        )
        repository.save(record)

        cancelled = service.cancel_job("job_cancel")

        assert cancelled.status == JobStatus.CANCELLED
