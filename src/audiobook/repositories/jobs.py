"""Persistent storage for conversion job records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from audiobook.schemas.jobs import JobRecord


class JobRepository:
    """Store job metadata as JSON files under the configured jobs root."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def job_dir(self, job_id: str) -> Path:
        """Return the filesystem directory for a job."""
        return self.root / job_id

    def ensure_job_dir(self, job_id: str) -> Path:
        """Create the job directory and standard subdirectories."""
        job_dir = self.job_dir(job_id)
        for path in (
            job_dir,
            job_dir / "input",
            job_dir / "result",
            job_dir / "reports",
            job_dir / "artifacts",
        ):
            path.mkdir(parents=True, exist_ok=True)
        return job_dir

    def _record_path(self, job_id: str) -> Path:
        return self.job_dir(job_id) / "job.json"

    def save(self, record: JobRecord) -> JobRecord:
        """Persist a job record."""
        self.ensure_job_dir(record.job_id)
        payload = record.model_dump(mode="json")
        self._record_path(record.job_id).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return record

    def get(self, job_id: str) -> JobRecord | None:
        """Load a job record by id."""
        path = self._record_path(job_id)
        if not path.exists():
            return None
        return JobRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> list[JobRecord]:
        """Return all persisted jobs, newest first."""
        records: list[JobRecord] = []
        for path in self.root.glob("*/job.json"):
            records.append(JobRecord.model_validate_json(path.read_text(encoding="utf-8")))
        records.sort(key=lambda item: (item.created_at, item.job_id), reverse=True)
        return records

    def delete(self, job_id: str) -> None:
        """Delete a job record and its directory."""
        job_dir = self.job_dir(job_id)
        if not job_dir.exists():
            return
        for path in sorted(job_dir.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        job_dir.rmdir()

    def seed(self, records: Iterable[JobRecord]) -> None:
        """Persist a collection of records."""
        for record in records:
            self.save(record)
