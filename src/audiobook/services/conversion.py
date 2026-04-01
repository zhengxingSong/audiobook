"""Conversion runner used by the web service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from audiobook.processors import AudiobookPipeline
from audiobook.processors.pipeline import PipelineProgress
from audiobook.repositories.jobs import JobRepository
from audiobook.schemas.jobs import JobProgressUpdate, JobRecord, JobRunResult
from audiobook.storage import VoiceLibrary


class AudiobookConversionRunner:
    """Execute conversion jobs through the existing pipeline."""

    def __init__(
        self,
        voice_library_path: Path,
        repository: JobRepository,
    ) -> None:
        self.voice_library_path = Path(voice_library_path)
        self.repository = repository

    def run(
        self,
        job: JobRecord,
        on_progress: Callable[[JobProgressUpdate], None],
    ) -> JobRunResult:
        """Run a conversion job and emit progress updates."""
        library = VoiceLibrary(str(self.voice_library_path))
        try:
            pipeline = AudiobookPipeline(
                voice_library=library,
                tts_endpoint=job.tts_endpoint,
            )

            def progress_callback(progress: PipelineProgress) -> None:
                on_progress(
                    JobProgressUpdate(
                        total_items=progress.total_blocks,
                        processed_items=progress.processed_blocks,
                        failed_items=progress.failed_blocks,
                        current_stage=progress.current_stage,
                        current_character=progress.current_character,
                    )
                )

            pipeline.set_progress_callback(progress_callback)
            conversion = pipeline.convert(job.input_path, job.output_path)

            report_payload = {
                "job_id": job.job_id,
                "success": conversion.success,
                "output_path": str(conversion.output_path) if conversion.output_path else None,
                "errors": conversion.errors,
                "total_blocks": conversion.total_blocks,
                "processed_blocks": conversion.processed_blocks,
                "total_fragments": conversion.total_fragments,
                "failed_blocks": conversion.failed_blocks,
                "processing_time": conversion.processing_time,
                "fragments": conversion.fragment_details,
                "character_summary": conversion.character_summary,
                "emotion_summary": conversion.emotion_summary,
            }
            report_path = Path(job.report_path)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            return JobRunResult(
                success=conversion.success and Path(job.output_path).exists(),
                output_path=job.output_path if Path(job.output_path).exists() else None,
                report_path=str(report_path),
                errors=list(conversion.errors),
                total_blocks=conversion.total_blocks,
                processed_blocks=conversion.processed_blocks,
                total_fragments=conversion.total_fragments,
                failed_blocks=list(conversion.failed_blocks),
                processing_time=conversion.processing_time,
            )
        finally:
            library.close()
