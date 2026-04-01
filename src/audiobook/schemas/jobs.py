"""Schema definitions for conversion jobs."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""
    return datetime.now(timezone.utc)


class JobStatus(str, Enum):
    """Lifecycle states for conversion jobs."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobProgressUpdate(BaseModel):
    """Progress payload emitted while a job is running."""

    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    current_stage: str = ""
    current_character: str = ""


class JobRunResult(BaseModel):
    """Result returned by a conversion runner."""

    success: bool
    output_path: Optional[str] = None
    report_path: str
    errors: list[str] = Field(default_factory=list)
    total_blocks: int = 0
    processed_blocks: int = 0
    total_fragments: int = 0
    failed_blocks: list[str] = Field(default_factory=list)
    processing_time: float = 0.0


class JobRecord(BaseModel):
    """Persistent state for a conversion job."""

    job_id: str
    status: JobStatus = JobStatus.PENDING
    novel_name: str
    input_path: str
    output_path: str
    report_path: str
    tts_endpoint: str = "http://localhost:9880"
    output_name: str
    errors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    current_stage: str = "Queued"
    current_character: str = ""
    total_blocks: int = 0
    processed_blocks: int = 0
    total_fragments: int = 0
    failed_fragments: int = 0
    failed_blocks: list[str] = Field(default_factory=list)
    processing_time: float = 0.0
    cancel_supported: bool = False

    def touch(self) -> "JobRecord":
        """Refresh the update timestamp."""
        self.updated_at = utc_now()
        return self
