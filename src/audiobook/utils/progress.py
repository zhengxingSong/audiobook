"""Progress tracking and dashboard utilities for audiobook conversion.

This module provides real-time progress tracking with SSE (Server-Sent Events)
support for web-based dashboards.

Core components:
- ProgressInfo: Data structure for progress information
- ProgressTracker: Tracks and reports conversion progress
- SSE support for real-time updates
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Generator, Optional


@dataclass
class ProgressStats:
    """Statistics for progress tracking.

    Attributes:
        completed: Number of completed fragments.
        in_progress: Number of fragments currently being processed.
        pending: Number of pending fragments.
        failed: Number of failed fragments.
    """

    completed: int = 0
    in_progress: int = 0
    pending: int = 0
    failed: int = 0

    @property
    def total(self) -> int:
        """Total number of fragments."""
        return self.completed + self.in_progress + self.pending + self.failed


@dataclass
class TimeInfo:
    """Time tracking information.

    Attributes:
        elapsed_seconds: Elapsed time in seconds.
        estimated_remaining_seconds: Estimated remaining time in seconds.
    """

    elapsed_seconds: int = 0
    estimated_remaining_seconds: int = 0

    def elapsed_formatted(self) -> str:
        """Format elapsed time as HH:MM:SS."""
        return self._format_time(self.elapsed_seconds)

    def remaining_formatted(self) -> str:
        """Format remaining time as HH:MM:SS."""
        return self._format_time(self.estimated_remaining_seconds)

    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format seconds as HH:MM:SS."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


@dataclass
class CurrentTask:
    """Information about the current task being processed.

    Attributes:
        chapter: Current chapter number.
        stage: Current processing stage.
        character: Current character being processed.
        emotion: Current emotion being synthesized.
    """

    chapter: str = ""
    stage: str = ""
    character: str = ""
    emotion: str = ""


@dataclass
class ProgressInfo:
    """Complete progress information for conversion.

    This is the main data structure for progress tracking and reporting.

    Attributes:
        job_id: Unique identifier for this conversion job.
        novel_name: Name of the novel being converted.
        total_chapters: Total number of chapters.
        current_chapter: Current chapter being processed.
        total_fragments: Total number of fragments.
        processed_fragments: Number of processed fragments.
        failed_fragments: Number of failed fragments.
        start_time: When the conversion started.
        current_stage: Current processing stage.
        current_character: Current character being processed.
        current_emotion: Current emotion being synthesized.
        processing_speed: Processing speed in fragments/minute.
    """

    job_id: str
    novel_name: str = ""
    total_chapters: int = 0
    current_chapter: int = 0
    total_fragments: int = 0
    processed_fragments: int = 0
    failed_fragments: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    current_stage: str = "初始化"
    current_character: str = ""
    current_emotion: str = ""
    processing_speed: float = 0.0

    @property
    def elapsed_seconds(self) -> int:
        """Elapsed time in seconds."""
        delta = datetime.now() - self.start_time
        return int(delta.total_seconds())

    @property
    def estimated_remaining_seconds(self) -> int:
        """Estimated remaining time in seconds."""
        if self.processing_speed <= 0 or self.processed_fragments <= 0:
            return 0

        remaining_fragments = self.total_fragments - self.processed_fragments
        if remaining_fragments <= 0:
            return 0

        # Estimate: remaining fragments / (fragments per second)
        fragments_per_second = self.processing_speed / 60.0
        if fragments_per_second <= 0:
            return 0

        return int(remaining_fragments / fragments_per_second)

    @property
    def percent_complete(self) -> float:
        """Percentage complete (0-100)."""
        if self.total_fragments <= 0:
            return 0.0
        return round(self.processed_fragments / self.total_fragments * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of progress info.
        """
        return {
            "job_id": self.job_id,
            "novel_name": self.novel_name,
            "progress": {
                "percent": self.percent_complete,
                "progress_bar": self._generate_progress_bar(),
            },
            "chapters": {
                "current": self.current_chapter,
                "total": self.total_chapters,
                "text": f"第 {self.current_chapter} 章 / 共 {self.total_chapters} 章",
            },
            "stats": {
                "completed": self.processed_fragments,
                "in_progress": 1 if self.current_stage != "完成" else 0,
                "pending": self.total_fragments - self.processed_fragments,
                "failed": self.failed_fragments,
            },
            "time": {
                "elapsed": TimeInfo._format_time(self.elapsed_seconds),
                "remaining": TimeInfo._format_time(self.estimated_remaining_seconds),
            },
            "current": {
                "chapter": f"第 {self.current_chapter} 章",
                "stage": self.current_stage,
                "character": self.current_character,
                "emotion": self.current_emotion,
            },
            "speed": {
                "fragments_per_minute": round(self.processing_speed, 1),
                "text": f"处理速度: ~{round(self.processing_speed, 1)} 片段/分钟",
            },
        }

    def _generate_progress_bar(self, width: int = 30) -> str:
        """Generate a text-based progress bar.

        Args:
            width: Width of the progress bar in characters.

        Returns:
            Progress bar string.
        """
        if self.total_fragments <= 0:
            return "░" * width

        filled = int(self.percent_complete / 100 * width)
        empty = width - filled
        return "█" * filled + "░" * empty


class ProgressTracker:
    """Tracks and reports conversion progress.

    Supports callback-based updates and SSE streaming for web dashboards.

    Example usage:
        tracker = ProgressTracker(job_id="job_001", novel_name="测试小说")
        tracker.set_callback(lambda info: print(info.to_dict()))
        tracker.start(total_fragments=100, total_chapters=10)
        tracker.update(processed=10, chapter=2, stage="语音合成")
        tracker.finish()
    """

    def __init__(
        self,
        job_id: str,
        novel_name: str = "",
    ) -> None:
        """Initialize the progress tracker.

        Args:
            job_id: Unique identifier for this conversion job.
            novel_name: Name of the novel being converted.
        """
        self.info = ProgressInfo(
            job_id=job_id,
            novel_name=novel_name,
        )
        self._callback: Optional[Callable[[ProgressInfo], None]] = None
        self._last_update_time: datetime = datetime.now()
        self._fragments_at_last_update: int = 0

    def set_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """Set a callback for progress updates.

        Args:
            callback: Function to call on each progress update.
        """
        self._callback = callback

    def start(
        self,
        total_fragments: int,
        total_chapters: int = 1,
    ) -> None:
        """Start tracking a new conversion.

        Args:
            total_fragments: Total number of fragments to process.
            total_chapters: Total number of chapters.
        """
        self.info = ProgressInfo(
            job_id=self.info.job_id,
            novel_name=self.info.novel_name,
            total_chapters=total_chapters,
            total_fragments=total_fragments,
            start_time=datetime.now(),
            current_stage="开始处理",
        )
        self._last_update_time = datetime.now()
        self._fragments_at_last_update = 0
        self._notify()

    def update(
        self,
        processed: Optional[int] = None,
        chapter: Optional[int] = None,
        stage: Optional[str] = None,
        character: Optional[str] = None,
        emotion: Optional[str] = None,
        failed: Optional[int] = None,
    ) -> None:
        """Update progress information.

        Args:
            processed: New processed fragment count.
            chapter: Current chapter number.
            stage: Current processing stage.
            character: Current character being processed.
            emotion: Current emotion being synthesized.
            failed: Number of failed fragments.
        """
        if processed is not None:
            # Calculate processing speed
            now = datetime.now()
            time_diff = (now - self._last_update_time).total_seconds()

            if time_diff >= 1.0:  # Update speed every second
                fragment_diff = processed - self._fragments_at_last_update
                if time_diff > 0 and fragment_diff >= 0:
                    # Speed in fragments per minute
                    self.info.processing_speed = (fragment_diff / time_diff) * 60
                    self._last_update_time = now
                    self._fragments_at_last_update = processed

            self.info.processed_fragments = processed

        if chapter is not None:
            self.info.current_chapter = chapter

        if stage is not None:
            self.info.current_stage = stage

        if character is not None:
            self.info.current_character = character

        if emotion is not None:
            self.info.current_emotion = emotion

        if failed is not None:
            self.info.failed_fragments = failed

        self._notify()

    def increment_processed(self) -> None:
        """Increment the processed fragment count by 1."""
        self.update(processed=self.info.processed_fragments + 1)

    def increment_failed(self) -> None:
        """Increment the failed fragment count by 1."""
        self.update(failed=self.info.failed_fragments + 1)

    def set_chapter(self, chapter: int) -> None:
        """Set the current chapter."""
        self.update(chapter=chapter)

    def set_stage(self, stage: str) -> None:
        """Set the current processing stage."""
        self.update(stage=stage)

    def set_character(self, character: str) -> None:
        """Set the current character being processed."""
        self.update(character=character)

    def set_emotion(self, emotion: str) -> None:
        """Set the current emotion being synthesized."""
        self.update(emotion=emotion)

    def finish(self) -> None:
        """Mark the conversion as complete."""
        self.info.current_stage = "完成"
        self.info.current_character = ""
        self.info.current_emotion = ""
        self._notify()

    def _notify(self) -> None:
        """Notify the callback of the current progress."""
        if self._callback:
            self._callback(self.info)

    def to_dict(self) -> dict[str, Any]:
        """Get progress info as dictionary."""
        return self.info.to_dict()

    def to_json(self) -> str:
        """Get progress info as JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)


def generate_sse_events(
    tracker: ProgressTracker,
    interval: float = 1.0,
) -> Generator[str, None, None]:
    """Generate SSE events for a progress tracker.

    This is a generator that yields SSE-formatted events for use with
    web-based dashboards.

    Args:
        tracker: ProgressTracker instance.
        interval: Update interval in seconds.

    Yields:
        SSE-formatted event strings.
    """
    while True:
        data = tracker.to_json()
        yield f"data: {data}\n\n"

        # Check if conversion is complete
        if tracker.info.current_stage == "完成":
            break

        # Wait for next update
        # Note: In production with asyncio, use asyncio.sleep
        import time
        time.sleep(interval)


async def generate_sse_events_async(
    tracker: ProgressTracker,
    interval: float = 1.0,
) -> AsyncGenerator[str, None]:
    """Async version of SSE event generation.

    Args:
        tracker: ProgressTracker instance.
        interval: Update interval in seconds.

    Yields:
        SSE-formatted event strings.
    """
    while True:
        data = tracker.to_json()
        yield f"data: {data}\n\n"

        if tracker.info.current_stage == "完成":
            break

        await asyncio.sleep(interval)




# FastAPI integration example (commented out for no dependencies)
"""
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

# Store active trackers
active_trackers: dict[str, ProgressTracker] = {}

@app.get("/api/progress/{job_id}/stream")
async def progress_stream(job_id: str):
    '''SSE endpoint for progress updates.'''
    tracker = active_trackers.get(job_id)
    if not tracker:
        return {"error": "Job not found"}

    async def event_generator():
        async for event in generate_sse_events_async(tracker):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@app.get("/api/progress/{job_id}")
async def get_progress(job_id: str):
    '''Get current progress as JSON.'''
    tracker = active_trackers.get(job_id)
    if not tracker:
        return {"error": "Job not found"}
    return tracker.to_dict()
"""