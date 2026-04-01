"""Job orchestration for the web service."""

from __future__ import annotations

import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from audiobook.repositories.jobs import JobRepository
from audiobook.schemas.jobs import JobProgressUpdate, JobRecord, JobRunResult, JobStatus
from audiobook.utils.progress import ProgressTracker


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(timezone.utc)


class JobRunner(Protocol):
    """Protocol implemented by concrete conversion runners."""

    def run(
        self,
        job: JobRecord,
        on_progress,
    ) -> JobRunResult: ...


class JobService:
    """Create, execute, and observe conversion jobs."""

    def __init__(
        self,
        repository: JobRepository,
        runner: JobRunner,
        run_inline: bool = False,
    ) -> None:
        self.repository = repository
        self.runner = runner
        self.run_inline = run_inline
        self.trackers: dict[str, ProgressTracker] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

        for record in self.repository.list():
            self._ensure_tracker(record)

    def _ensure_tracker(self, record: JobRecord) -> ProgressTracker:
        tracker = self.trackers.get(record.job_id)
        if tracker is None:
            tracker = ProgressTracker(job_id=record.job_id, novel_name=record.novel_name)
            tracker.start(total_fragments=max(record.total_blocks, 1), total_chapters=1)
            tracker.update(
                processed=record.processed_blocks,
                stage=record.current_stage,
                character=record.current_character,
                failed=record.failed_fragments,
            )
            tracker.info.total_fragments = max(record.total_blocks, tracker.info.total_fragments)
            self.trackers[record.job_id] = tracker
        return tracker

    def create_job_from_upload(
        self,
        filename: str,
        data: bytes,
        output_name: str | None = None,
        tts_endpoint: str = "http://localhost:9880",
    ) -> JobRecord:
        """Create a new job from uploaded content and start it."""
        job_id = f"job_{uuid.uuid4().hex[:10]}"
        job_dir = self.repository.ensure_job_dir(job_id)
        input_path = job_dir / "input" / filename
        input_path.write_bytes(data)
        return self.create_job_from_path(
            input_path=input_path,
            novel_name=Path(filename).stem or job_id,
            output_name=output_name,
            tts_endpoint=tts_endpoint,
            job_id=job_id,
        )

    def create_job_from_path(
        self,
        input_path: Path,
        novel_name: str | None = None,
        output_name: str | None = None,
        tts_endpoint: str = "http://localhost:9880",
        job_id: str | None = None,
    ) -> JobRecord:
        """Create a new job from an existing local path and start it."""
        resolved_input = Path(input_path).resolve()
        if not resolved_input.exists():
            raise FileNotFoundError(f"Novel file not found: {resolved_input}")

        effective_job_id = job_id or f"job_{uuid.uuid4().hex[:10]}"
        job_dir = self.repository.ensure_job_dir(effective_job_id)
        safe_output_name = output_name or f"{resolved_input.stem}.wav"
        output_path = job_dir / "result" / safe_output_name
        report_path = job_dir / "reports" / "conversion-report.json"

        record = JobRecord(
            job_id=effective_job_id,
            status=JobStatus.PENDING,
            novel_name=novel_name or resolved_input.stem,
            input_path=str(resolved_input),
            output_path=str(output_path),
            report_path=str(report_path),
            tts_endpoint=tts_endpoint,
            output_name=safe_output_name,
        )
        self.repository.save(record)
        self._ensure_tracker(record)
        self.start_job(record.job_id)
        return self.get_job(record.job_id)

    def start_job(self, job_id: str) -> JobRecord:
        """Start a pending job."""
        record = self.get_job(job_id)
        if record.status != JobStatus.PENDING:
            raise ValueError(f"Job {job_id} is not pending")

        if self.run_inline:
            self._run_job(job_id)
        else:
            thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
            self._threads[job_id] = thread
            thread.start()
        return self.get_job(job_id)

    def _apply_progress(self, job_id: str, progress: JobProgressUpdate) -> None:
        record = self.get_job(job_id)
        tracker = self._ensure_tracker(record)
        tracker.info.total_fragments = max(progress.total_items, tracker.info.total_fragments, 1)
        tracker.update(
            processed=progress.processed_items,
            stage=progress.current_stage or tracker.info.current_stage,
            character=progress.current_character,
            failed=progress.failed_items,
        )

        record.total_blocks = max(record.total_blocks, progress.total_items)
        record.processed_blocks = progress.processed_items
        record.failed_fragments = progress.failed_items
        record.current_stage = progress.current_stage or record.current_stage
        record.current_character = progress.current_character
        record.touch()
        self.repository.save(record)

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            record = self.get_job(job_id)
            if record.status == JobStatus.CANCELLED:
                return
            record.status = JobStatus.RUNNING
            record.started_at = utc_now()
            record.current_stage = "Starting conversion"
            record.touch()
            self.repository.save(record)
            tracker = self._ensure_tracker(record)
            tracker.start(total_fragments=max(record.total_blocks, 1), total_chapters=1)
            tracker.set_stage("Starting conversion")

        result = self.runner.run(record, lambda progress: self._apply_progress(job_id, progress))

        record = self.get_job(job_id)
        record.finished_at = utc_now()
        record.processing_time = result.processing_time
        record.total_blocks = result.total_blocks
        record.processed_blocks = result.processed_blocks
        record.total_fragments = result.total_fragments
        record.failed_fragments = len(result.failed_blocks)
        record.failed_blocks = list(result.failed_blocks)
        record.errors = list(result.errors)
        record.report_path = result.report_path
        record.output_path = result.output_path or record.output_path
        record.status = JobStatus.SUCCEEDED if result.success else JobStatus.FAILED
        record.current_stage = "Completed" if result.success else "Failed"
        record.touch()
        self.repository.save(record)

        tracker = self._ensure_tracker(record)
        tracker.info.total_fragments = max(record.total_blocks, tracker.info.total_fragments, 1)
        tracker.update(
            processed=record.processed_blocks,
            stage=record.current_stage,
            character=record.current_character,
            failed=record.failed_fragments,
        )
        tracker.finish(record.current_stage)

    def list_jobs(self) -> list[JobRecord]:
        """List all known jobs."""
        return self.repository.list()

    def get_job(self, job_id: str) -> JobRecord:
        """Get a job by id."""
        record = self.repository.get(job_id)
        if record is None:
            raise KeyError(job_id)
        return record

    def get_report(self, job_id: str) -> dict:
        """Load a job report."""
        record = self.get_job(job_id)
        report_path = Path(record.report_path)
        if not report_path.exists():
            raise FileNotFoundError(report_path)
        import json

        return json.loads(report_path.read_text(encoding="utf-8"))

    def get_result_path(self, job_id: str) -> Path:
        """Return the output file for a successful job."""
        record = self.get_job(job_id)
        path = Path(record.output_path)
        if not path.exists():
            raise FileNotFoundError(path)
        return path

    def cancel_job(self, job_id: str) -> JobRecord:
        """Cancel a pending job."""
        record = self.get_job(job_id)
        if record.status == JobStatus.PENDING:
            record.status = JobStatus.CANCELLED
            record.finished_at = utc_now()
            record.current_stage = "Cancelled"
            record.touch()
            self.repository.save(record)
            tracker = self._ensure_tracker(record)
            tracker.finish("Cancelled")
            return record
        raise ValueError("Cancellation is only supported for pending jobs.")

    def retry_job(self, job_id: str) -> JobRecord:
        """Retry a failed or cancelled job by cloning its input settings."""
        record = self.get_job(job_id)
        if record.status not in {JobStatus.FAILED, JobStatus.CANCELLED}:
            raise ValueError("Only failed or cancelled jobs can be retried.")
        return self.create_job_from_path(
            input_path=Path(record.input_path),
            novel_name=record.novel_name,
            output_name=record.output_name,
            tts_endpoint=record.tts_endpoint,
        )

    def tracker_summary(self) -> dict[str, ProgressTracker]:
        """Expose active trackers."""
        return self.trackers

    def clone_uploaded_input(self, source: Path, destination_name: str) -> Path:
        """Copy an existing input file to a new job input directory."""
        target = Path(destination_name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return target
