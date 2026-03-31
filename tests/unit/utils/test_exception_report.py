"""Tests for Exception Report utilities."""

from pathlib import Path

import pytest

from audiobook.utils.exception_report import (
    ErrorSeverity,
    ErrorType,
    ExceptionReport,
    ExceptionSummary,
    FragmentException,
    OriginalTextLocator,
    TextLocation,
    create_exception,
)


class TestErrorType:
    """Tests for ErrorType enum."""

    def test_error_type_values(self) -> None:
        """Test that error types have expected values."""
        assert ErrorType.CONSISTENCY_CHECK_ERROR.value == "一致性检查错误"
        assert ErrorType.SYNTHESIS_ERROR.value == "语音合成错误"
        assert ErrorType.VOICE_MATCH_ERROR.value == "音色匹配错误"

    def test_error_type_count(self) -> None:
        """Test that all expected error types are defined."""
        assert len(ErrorType) >= 7


class TestErrorSeverity:
    """Tests for ErrorSeverity enum."""

    def test_severity_values(self) -> None:
        """Test that severities have expected values."""
        assert ErrorSeverity.CRITICAL.value == "严重"
        assert ErrorSeverity.HIGH.value == "高"
        assert ErrorSeverity.MEDIUM.value == "中"
        assert ErrorSeverity.LOW.value == "低"
        assert ErrorSeverity.WARNING.value == "警告"

    def test_severity_count(self) -> None:
        """Test that all severities are defined."""
        assert len(ErrorSeverity) == 5


class TestTextLocation:
    """Tests for TextLocation dataclass."""

    def test_default_values(self) -> None:
        """Test default location values."""
        loc = TextLocation()
        assert loc.chapter == 0
        assert loc.paragraph == 0
        assert loc.sentence == 0

    def test_custom_values(self) -> None:
        """Test custom location values."""
        loc = TextLocation(
            chapter=5,
            paragraph=3,
            sentence=2,
            start_char=100,
            end_char=150,
        )
        assert loc.chapter == 5
        assert loc.paragraph == 3
        assert loc.sentence == 2

    def test_to_string(self) -> None:
        """Test location string formatting."""
        loc = TextLocation(chapter=5, paragraph=3, sentence=2)
        assert loc.to_string() == "第5章 第3段 第2句"

    def test_to_string_partial(self) -> None:
        """Test location string with partial information."""
        loc = TextLocation(chapter=5)
        assert loc.to_string() == "第5章"

    def test_to_string_empty(self) -> None:
        """Test location string with no information."""
        loc = TextLocation()
        assert loc.to_string() == "未知位置"


class TestFragmentException:
    """Tests for FragmentException dataclass."""

    @pytest.fixture
    def sample_exception(self) -> FragmentException:
        """Create a sample exception for testing."""
        return FragmentException(
            fragment_id="frag_001",
            location=TextLocation(chapter=5, paragraph=3, sentence=2),
            original_text="张三愤怒地拍桌而起...",
            error_type=ErrorType.CONSISTENCY_CHECK_ERROR,
            error_message="一致性得分 0.72 < 阈值 0.75",
            severity=ErrorSeverity.WARNING,
            suggested_action="重新合成或手动确认音色",
        )

    def test_exception_creation(self, sample_exception: FragmentException) -> None:
        """Test exception creation."""
        assert sample_exception.fragment_id == "frag_001"
        assert sample_exception.error_type == ErrorType.CONSISTENCY_CHECK_ERROR
        assert sample_exception.severity == ErrorSeverity.WARNING

    def test_to_dict(self, sample_exception: FragmentException) -> None:
        """Test dictionary conversion."""
        data = sample_exception.to_dict()

        assert data["fragment_id"] == "frag_001"
        assert data["error_type"] == "一致性检查错误"
        assert data["severity"] == "警告"
        assert "original_text" in data
        assert "timestamp" in data

    def test_to_dict_truncates_long_text(self) -> None:
        """Test that long original text is truncated in to_dict."""
        exception = FragmentException(
            fragment_id="frag_001",
            location=TextLocation(),
            original_text="x" * 200,
            error_type=ErrorType.SYNTHESIS_ERROR,
            error_message="Error",
        )

        data = exception.to_dict()
        assert len(data["original_text"]) < 200
        assert data["original_text"].endswith("...")


class TestExceptionSummary:
    """Tests for ExceptionSummary dataclass."""

    def test_default_values(self) -> None:
        """Test default summary values."""
        summary = ExceptionSummary()
        assert summary.total == 0
        assert summary.failed == 0
        assert summary.success_rate == 100.0

    def test_calculate_success_rate(self) -> None:
        """Test success rate calculation."""
        summary = ExceptionSummary(total=100, failed=3)
        summary.calculate_success_rate()
        assert summary.success_rate == 97.0

    def test_calculate_success_rate_zero_total(self) -> None:
        """Test success rate with zero total."""
        summary = ExceptionSummary(total=0, failed=0)
        summary.calculate_success_rate()
        assert summary.success_rate == 100.0

    def test_by_type_tracking(self) -> None:
        """Test tracking by error type."""
        summary = ExceptionSummary()
        summary.by_type["语音合成错误"] = 5
        summary.by_type["一致性检查错误"] = 2

        assert summary.by_type["语音合成错误"] == 5
        assert summary.by_type["一致性检查错误"] == 2


class TestExceptionReport:
    """Tests for ExceptionReport class."""

    @pytest.fixture
    def report(self) -> ExceptionReport:
        """Create a report for testing."""
        return ExceptionReport(
            report_id="report_001",
            job_id="job_001",
        )

    @pytest.fixture
    def sample_exception(self) -> FragmentException:
        """Create a sample exception."""
        return FragmentException(
            fragment_id="frag_001",
            location=TextLocation(chapter=5),
            original_text="Test text",
            error_type=ErrorType.SYNTHESIS_ERROR,
            error_message="Synthesis failed",
            severity=ErrorSeverity.HIGH,
        )

    def test_report_creation(self, report: ExceptionReport) -> None:
        """Test report creation."""
        assert report.report_id == "report_001"
        assert report.job_id == "job_001"
        assert len(report.exceptions) == 0

    def test_add_exception(
        self,
        report: ExceptionReport,
        sample_exception: FragmentException,
    ) -> None:
        """Test adding an exception to report."""
        report.add_exception(sample_exception)

        assert len(report.exceptions) == 1
        assert report.summary.failed == 1

    def test_add_multiple_exceptions(self, report: ExceptionReport) -> None:
        """Test adding multiple exceptions."""
        for i in range(3):
            exc = FragmentException(
                fragment_id=f"frag_{i:03d}",
                location=TextLocation(),
                original_text=f"Text {i}",
                error_type=ErrorType.SYNTHESIS_ERROR,
                error_message=f"Error {i}",
            )
            report.add_exception(exc)

        assert len(report.exceptions) == 3
        assert report.summary.failed == 3

    def test_summary_by_type(
        self,
        report: ExceptionReport,
        sample_exception: FragmentException,
    ) -> None:
        """Test that summary tracks by type."""
        report.add_exception(sample_exception)

        assert "语音合成错误" in report.summary.by_type
        assert report.summary.by_type["语音合成错误"] == 1

    def test_summary_by_severity(
        self,
        report: ExceptionReport,
        sample_exception: FragmentException,
    ) -> None:
        """Test that summary tracks by severity."""
        report.add_exception(sample_exception)

        assert "高" in report.summary.by_severity
        assert report.summary.by_severity["高"] == 1

    def test_to_dict(
        self,
        report: ExceptionReport,
        sample_exception: FragmentException,
    ) -> None:
        """Test report dictionary conversion."""
        report.summary.total = 100
        report.add_exception(sample_exception)

        data = report.to_dict()

        assert data["report_id"] == "report_001"
        assert data["job_id"] == "job_001"
        assert "summary" in data
        assert "exceptions" in data
        assert len(data["exceptions"]) == 1


class TestOriginalTextLocator:
    """Tests for OriginalTextLocator class."""

    @pytest.fixture
    def locator(self, tmp_path: Path) -> OriginalTextLocator:
        """Create a locator with a test file."""
        novel_path = tmp_path / "test.txt"
        novel_path.write_text("第一章\n\n这是第一段。\n\n这是第二段。\n", encoding="utf-8")
        loc = OriginalTextLocator(str(novel_path))
        loc.load()
        return loc

    def test_locator_creation(self, tmp_path: Path) -> None:
        """Test locator creation."""
        novel_path = tmp_path / "test.txt"
        locator = OriginalTextLocator(str(novel_path))
        assert locator.novel_path.exists() is False  # Not created yet

    def test_load(self, locator: OriginalTextLocator) -> None:
        """Test loading content."""
        assert locator._content is not None
        assert "第一章" in locator._content

    def test_locate(self, locator: OriginalTextLocator) -> None:
        """Test creating a location."""
        loc = locator.locate(chapter=1, paragraph=2, sentence=1)

        assert loc.chapter == 1
        assert loc.paragraph == 2
        assert loc.sentence == 1

    def test_highlight(self, locator: OriginalTextLocator) -> None:
        """Test highlighting location."""
        loc = TextLocation(chapter=1, paragraph=1, sentence=1)
        result = locator.highlight(loc)

        # For MVP, returns formatted string
        assert "第1章" in result

    def test_get_context(self, locator: OriginalTextLocator) -> None:
        """Test getting context."""
        loc = TextLocation(start_char=5, end_char=15)
        context = locator.get_context(loc, context_chars=10)

        # Should contain the text with markers
        assert context is not None


class TestCreateException:
    """Tests for create_exception convenience function."""

    def test_create_exception_basic(self) -> None:
        """Test creating exception with basic parameters."""
        exc = create_exception(
            fragment_id="frag_001",
            error_type=ErrorType.SYNTHESIS_ERROR,
            error_message="Test error",
        )

        assert exc.fragment_id == "frag_001"
        assert exc.error_type == ErrorType.SYNTHESIS_ERROR
        assert exc.error_message == "Test error"
        assert exc.severity == ErrorSeverity.MEDIUM

    def test_create_exception_with_location(self) -> None:
        """Test creating exception with location."""
        exc = create_exception(
            fragment_id="frag_001",
            error_type=ErrorType.VOICE_MATCH_ERROR,
            error_message="No matching voice",
            chapter=5,
            paragraph=3,
            sentence=2,
        )

        assert exc.location.chapter == 5
        assert exc.location.paragraph == 3
        assert exc.location.sentence == 2

    def test_create_exception_suggested_action(self) -> None:
        """Test that suggested action is set based on error type."""
        exc = create_exception(
            fragment_id="frag_001",
            error_type=ErrorType.CONSISTENCY_CHECK_ERROR,
            error_message="Consistency failed",
        )

        assert "重新合成" in exc.suggested_action or "确认" in exc.suggested_action

    def test_create_exception_custom_severity(self) -> None:
        """Test creating exception with custom severity."""
        exc = create_exception(
            fragment_id="frag_001",
            error_type=ErrorType.SYNTHESIS_ERROR,
            error_message="Critical failure",
            severity=ErrorSeverity.CRITICAL,
        )

        assert exc.severity == ErrorSeverity.CRITICAL


class TestExceptionReportIntegration:
    """Integration tests for exception reporting."""

    def test_full_report_workflow(self) -> None:
        """Test complete exception report workflow."""
        # Create report
        report = ExceptionReport(
            report_id="report_001",
            job_id="job_001",
        )
        report.summary.total = 100

        # Add various exceptions
        errors = [
            (ErrorType.SYNTHESIS_ERROR, ErrorSeverity.HIGH),
            (ErrorType.CONSISTENCY_CHECK_ERROR, ErrorSeverity.WARNING),
            (ErrorType.VOICE_MATCH_ERROR, ErrorSeverity.MEDIUM),
            (ErrorType.SYNTHESIS_ERROR, ErrorSeverity.CRITICAL),
        ]

        for i, (error_type, severity) in enumerate(errors):
            exc = create_exception(
                fragment_id=f"frag_{i:03d}",
                error_type=error_type,
                error_message=f"Error {i}",
                severity=severity,
                chapter=i + 1,
            )
            report.add_exception(exc)

        # Verify report
        assert report.summary.failed == 4
        assert report.summary.by_type["语音合成错误"] == 2
        assert report.summary.by_severity["严重"] == 1

        # Calculate success rate
        report.summary.calculate_success_rate()
        assert report.summary.success_rate == 96.0  # (100-4)/100 * 100

        # Convert to dict for API
        data = report.to_dict()
        assert data["summary"]["failed"] == 4
        assert len(data["exceptions"]) == 4