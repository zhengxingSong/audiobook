"""Exception handling and reporting for audiobook conversion.

This module provides comprehensive exception tracking and reporting
to help users identify and fix issues during conversion.

Core components:
- FragmentException: Details about a failed fragment
- ExceptionReport: Complete report of all exceptions
- OriginalTextLocator: Locate original text positions
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ErrorType(Enum):
    """Types of errors that can occur during conversion."""

    CONSISTENCY_CHECK_ERROR = "一致性检查错误"
    SYNTHESIS_ERROR = "语音合成错误"
    VOICE_MATCH_ERROR = "音色匹配错误"
    PARSING_ERROR = "文本解析错误"
    CHARACTER_RECOGNITION_ERROR = "角色识别错误"
    AUDIO_PROCESSING_ERROR = "音频处理错误"
    UNKNOWN_ERROR = "未知错误"


class ErrorSeverity(Enum):
    """Severity levels for exceptions."""

    CRITICAL = "严重"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"
    WARNING = "警告"


@dataclass
class TextLocation:
    """Location of text in the original novel.

    Attributes:
        chapter: Chapter number.
        paragraph: Paragraph number within chapter.
        sentence: Sentence number within paragraph.
        start_char: Starting character position.
        end_char: Ending character position.
    """

    chapter: int = 0
    paragraph: int = 0
    sentence: int = 0
    start_char: int = 0
    end_char: int = 0

    def to_string(self) -> str:
        """Format location as human-readable string."""
        parts = []
        if self.chapter > 0:
            parts.append(f"第{self.chapter}章")
        if self.paragraph > 0:
            parts.append(f"第{self.paragraph}段")
        if self.sentence > 0:
            parts.append(f"第{self.sentence}句")
        return " ".join(parts) if parts else "未知位置"


@dataclass
class FragmentException:
    """Exception details for a single fragment.

    Attributes:
        fragment_id: ID of the failed fragment.
        location: Location in original text.
        original_text: The text that caused the error.
        error_type: Type of error that occurred.
        error_message: Detailed error message.
        severity: Severity level of the error.
        suggested_action: Suggested action to fix the error.
        audio_preview_url: URL to preview the problematic audio.
        timestamp: When the error occurred.
        retry_count: Number of retry attempts.
    """

    fragment_id: str
    location: TextLocation
    original_text: str
    error_type: ErrorType
    error_message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    suggested_action: str = ""
    audio_preview_url: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "fragment_id": self.fragment_id,
            "location": self.location.to_string(),
            "original_text": self.original_text[:100] + "..."
            if len(self.original_text) > 100
            else self.original_text,
            "error_type": self.error_type.value,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "suggested_action": self.suggested_action,
            "audio_preview_url": self.audio_preview_url,
            "timestamp": self.timestamp.isoformat(),
            "retry_count": self.retry_count,
        }


@dataclass
class ExceptionSummary:
    """Summary statistics for exceptions.

    Attributes:
        total: Total number of fragments.
        failed: Number of failed fragments.
        warnings: Number of warnings.
        success_rate: Success rate as percentage.
        by_type: Count by error type.
        by_severity: Count by severity level.
    """

    total: int = 0
    failed: int = 0
    warnings: int = 0
    success_rate: float = 100.0
    by_type: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)

    def calculate_success_rate(self) -> None:
        """Calculate success rate from total and failed counts."""
        if self.total > 0:
            self.success_rate = round((self.total - self.failed) / self.total * 100, 2)
        else:
            self.success_rate = 100.0


@dataclass
class ExceptionReport:
    """Complete exception report for a conversion job.

    Attributes:
        report_id: Unique identifier for this report.
        job_id: ID of the conversion job.
        generated_at: When the report was generated.
        summary: Summary statistics.
        exceptions: List of all exceptions.
    """

    report_id: str
    job_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    summary: ExceptionSummary = field(default_factory=ExceptionSummary)
    exceptions: list[FragmentException] = field(default_factory=list)

    def add_exception(self, exception: FragmentException) -> None:
        """Add an exception to the report.

        Args:
            exception: Exception to add.
        """
        self.exceptions.append(exception)
        self.summary.failed += 1

        # Update type counts
        error_type = exception.error_type.value
        self.summary.by_type[error_type] = self.summary.by_type.get(error_type, 0) + 1

        # Update severity counts
        severity = exception.severity.value
        self.summary.by_severity[severity] = (
            self.summary.by_severity.get(severity, 0) + 1
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "report_id": self.report_id,
            "job_id": self.job_id,
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "total": self.summary.total,
                "failed": self.summary.failed,
                "warnings": self.summary.warnings,
                "success_rate": f"{self.summary.success_rate}%",
                "by_type": self.summary.by_type,
                "by_severity": self.summary.by_severity,
            },
            "exceptions": [e.to_dict() for e in self.exceptions],
        }


class OriginalTextLocator:
    """Locates and highlights text in original novel files.

    Helps users find the source of errors in their original text.
    """

    def __init__(self, novel_path: str) -> None:
        """Initialize the text locator.

        Args:
            novel_path: Path to the original novel file.
        """
        self.novel_path = Path(novel_path)
        self._content: Optional[str] = None
        self._lines: list[str] = []

    def load(self) -> None:
        """Load the novel content."""
        if self.novel_path.exists():
            self._content = self.novel_path.read_text(encoding="utf-8")
            self._lines = self._content.split("\n")

    def locate(
        self,
        chapter: int,
        paragraph: int,
        sentence: int,
    ) -> TextLocation:
        """Create a text location object.

        Args:
            chapter: Chapter number.
            paragraph: Paragraph number.
            sentence: Sentence number.

        Returns:
            TextLocation object.
        """
        return TextLocation(
            chapter=chapter,
            paragraph=paragraph,
            sentence=sentence,
        )

    def highlight(
        self,
        location: TextLocation,
        context_lines: int = 3,
    ) -> str:
        """Generate highlighted context around a location.

        Args:
            location: Location to highlight.
            context_lines: Number of context lines to show.

        Returns:
            Formatted string with highlighted location.
        """
        if not self._content:
            return "原文件未加载"

        # For MVP, just show a placeholder
        # In production, would parse chapters/paragraphs and highlight
        return f"第{location.chapter}章 第{location.paragraph}段 第{location.sentence}句"

    def get_context(
        self,
        location: TextLocation,
        context_chars: int = 200,
    ) -> str:
        """Get text context around a location.

        Args:
            location: Location to get context for.
            context_chars: Number of characters of context.

        Returns:
            Text with the location highlighted.
        """
        if not self._content:
            return ""

        # For MVP, just return a portion of the content
        start = max(0, location.start_char - context_chars)
        end = min(len(self._content), location.end_char + context_chars)

        context = self._content[start:end]

        # Add markers around the target text
        if location.start_char < len(self._content):
            target_start = location.start_char - start
            target_end = location.end_char - start
            if target_start >= 0 and target_end <= len(context):
                context = (
                    context[:target_start]
                    + ">>>"
                    + context[target_start:target_end]
                    + "<<<"
                    + context[target_end:]
                )

        return context


def create_exception(
    fragment_id: str,
    error_type: ErrorType,
    error_message: str,
    original_text: str = "",
    chapter: int = 0,
    paragraph: int = 0,
    sentence: int = 0,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
) -> FragmentException:
    """Convenience function to create a FragmentException.

    Args:
        fragment_id: ID of the failed fragment.
        error_type: Type of error.
        error_message: Error message.
        original_text: Original text that caused the error.
        chapter: Chapter number.
        paragraph: Paragraph number.
        sentence: Sentence number.
        severity: Error severity.

    Returns:
        FragmentException instance.
    """
    # Determine suggested action based on error type
    suggested_actions = {
        ErrorType.CONSISTENCY_CHECK_ERROR: "重新合成或手动确认音色",
        ErrorType.SYNTHESIS_ERROR: "重新合成",
        ErrorType.VOICE_MATCH_ERROR: "手动选择音色",
        ErrorType.PARSING_ERROR: "检查原文格式",
        ErrorType.CHARACTER_RECOGNITION_ERROR: "手动指定角色",
        ErrorType.AUDIO_PROCESSING_ERROR: "检查音频参数",
        ErrorType.UNKNOWN_ERROR: "查看详细日志",
    }

    return FragmentException(
        fragment_id=fragment_id,
        location=TextLocation(
            chapter=chapter,
            paragraph=paragraph,
            sentence=sentence,
        ),
        original_text=original_text,
        error_type=error_type,
        error_message=error_message,
        severity=severity,
        suggested_action=suggested_actions.get(error_type, "查看详情"),
    )