"""Tests for job repository persistence."""

from pathlib import Path

from audiobook.repositories import JobRepository
from audiobook.schemas.jobs import JobRecord, JobStatus


class TestJobRepository:
    """Repository behavior for stored jobs."""

    def test_save_and_get_round_trip(self, temp_dir: Path) -> None:
        repository = JobRepository(temp_dir / "jobs")
        record = JobRecord(
            job_id="job_001",
            status=JobStatus.PENDING,
            novel_name="Novel",
            input_path=str(temp_dir / "input.txt"),
            output_path=str(temp_dir / "output.wav"),
            report_path=str(temp_dir / "report.json"),
            output_name="output.wav",
        )

        repository.save(record)
        loaded = repository.get("job_001")

        assert loaded is not None
        assert loaded.job_id == "job_001"
        assert loaded.novel_name == "Novel"

    def test_list_returns_newest_first(self, temp_dir: Path) -> None:
        repository = JobRepository(temp_dir / "jobs")
        first = JobRecord(
            job_id="job_001",
            novel_name="First",
            input_path=str(temp_dir / "first.txt"),
            output_path=str(temp_dir / "first.wav"),
            report_path=str(temp_dir / "first.json"),
            output_name="first.wav",
        )
        second = JobRecord(
            job_id="job_002",
            novel_name="Second",
            input_path=str(temp_dir / "second.txt"),
            output_path=str(temp_dir / "second.wav"),
            report_path=str(temp_dir / "second.json"),
            output_name="second.wav",
        )

        repository.save(first)
        repository.save(second)

        jobs = repository.list()

        assert [job.job_id for job in jobs] == ["job_002", "job_001"]
