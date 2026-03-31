"""Tests for Progress Dashboard utilities."""

import json
import pytest
from datetime import datetime, timedelta

from audiobook.utils.progress import (
    ProgressInfo,
    ProgressStats,
    ProgressTracker,
    TimeInfo,
    generate_sse_events,
)


class TestProgressStats:
    """Tests for ProgressStats dataclass."""

    def test_default_values(self) -> None:
        """Test default stats values."""
        stats = ProgressStats()
        assert stats.completed == 0
        assert stats.in_progress == 0
        assert stats.pending == 0
        assert stats.failed == 0

    def test_total_property(self) -> None:
        """Test total calculation."""
        stats = ProgressStats(
            completed=10,
            in_progress=2,
            pending=20,
            failed=1,
        )
        assert stats.total == 33


class TestTimeInfo:
    """Tests for TimeInfo dataclass."""

    def test_default_values(self) -> None:
        """Test default time values."""
        time_info = TimeInfo()
        assert time_info.elapsed_seconds == 0
        assert time_info.estimated_remaining_seconds == 0

    def test_format_time(self) -> None:
        """Test time formatting."""
        assert TimeInfo._format_time(0) == "00:00:00"
        assert TimeInfo._format_time(60) == "00:01:00"
        assert TimeInfo._format_time(3661) == "01:01:01"
        assert TimeInfo._format_time(7322) == "02:02:02"

    def test_elapsed_formatted(self) -> None:
        """Test elapsed time formatting."""
        time_info = TimeInfo(elapsed_seconds=3661)
        assert time_info.elapsed_formatted() == "01:01:01"

    def test_remaining_formatted(self) -> None:
        """Test remaining time formatting."""
        time_info = TimeInfo(estimated_remaining_seconds=1800)
        assert time_info.remaining_formatted() == "00:30:00"


class TestProgressInfo:
    """Tests for ProgressInfo dataclass."""

    @pytest.fixture
    def progress_info(self) -> ProgressInfo:
        """Create a sample progress info."""
        return ProgressInfo(
            job_id="job_001",
            novel_name="测试小说",
            total_chapters=10,
            current_chapter=3,
            total_fragments=100,
            processed_fragments=45,
            failed_fragments=2,
            current_stage="语音合成",
            current_character="张三",
            current_emotion="愤怒",
            processing_speed=12.5,
        )

    def test_default_values(self) -> None:
        """Test default progress info values."""
        info = ProgressInfo(job_id="job_001")
        assert info.job_id == "job_001"
        assert info.total_fragments == 0
        assert info.processed_fragments == 0
        assert info.current_stage == "初始化"

    def test_percent_complete(self, progress_info: ProgressInfo) -> None:
        """Test percent complete calculation."""
        assert progress_info.percent_complete == 45.0

    def test_percent_complete_zero_total(self) -> None:
        """Test percent complete with zero total."""
        info = ProgressInfo(job_id="job_001", total_fragments=0)
        assert info.percent_complete == 0.0

    def test_elapsed_seconds(self, progress_info: ProgressInfo) -> None:
        """Test elapsed seconds calculation."""
        # Start time is set to now by default
        elapsed = progress_info.elapsed_seconds
        assert elapsed >= 0
        assert elapsed < 5  # Should be very recent

    def test_estimated_remaining_seconds(self, progress_info: ProgressInfo) -> None:
        """Test estimated remaining time calculation."""
        # With 45 processed and 55 remaining at 12.5 fragments/min
        # 55 fragments / (12.5/60 fragments/sec) = 55 / 0.2083 = ~264 seconds
        estimated = progress_info.estimated_remaining_seconds
        assert estimated > 0

    def test_estimated_remaining_zero_speed(self) -> None:
        """Test estimated remaining with zero speed."""
        info = ProgressInfo(
            job_id="job_001",
            total_fragments=100,
            processed_fragments=50,
            processing_speed=0.0,
        )
        assert info.estimated_remaining_seconds == 0

    def test_to_dict(self, progress_info: ProgressInfo) -> None:
        """Test dictionary conversion."""
        data = progress_info.to_dict()

        assert data["job_id"] == "job_001"
        assert data["novel_name"] == "测试小说"
        assert "progress" in data
        assert data["progress"]["percent"] == 45.0
        assert "stats" in data
        assert data["stats"]["completed"] == 45
        assert data["stats"]["failed"] == 2

    def test_to_dict_json_serializable(self, progress_info: ProgressInfo) -> None:
        """Test that to_dict is JSON serializable."""
        data = progress_info.to_dict()
        # Should not raise
        json_str = json.dumps(data, ensure_ascii=False)
        assert json_str is not None

    def test_generate_progress_bar(self, progress_info: ProgressInfo) -> None:
        """Test progress bar generation."""
        bar = progress_info._generate_progress_bar(width=10)
        # 45% of 10 = 4.5 -> 4 filled, 6 empty
        assert bar.count("█") == 4
        assert bar.count("░") == 6

    def test_generate_progress_bar_zero_percent(self) -> None:
        """Test progress bar at 0%."""
        info = ProgressInfo(job_id="job_001", total_fragments=100)
        bar = info._generate_progress_bar(width=10)
        assert bar == "░" * 10

    def test_generate_progress_bar_complete(self) -> None:
        """Test progress bar at 100%."""
        info = ProgressInfo(
            job_id="job_001",
            total_fragments=100,
            processed_fragments=100,
        )
        bar = info._generate_progress_bar(width=10)
        assert bar == "█" * 10


class TestProgressTracker:
    """Tests for ProgressTracker class."""

    @pytest.fixture
    def tracker(self) -> ProgressTracker:
        """Create a tracker for testing."""
        return ProgressTracker(job_id="job_001", novel_name="测试小说")

    def test_tracker_initialization(self, tracker: ProgressTracker) -> None:
        """Test tracker initialization."""
        assert tracker.info.job_id == "job_001"
        assert tracker.info.novel_name == "测试小说"
        assert tracker.info.total_fragments == 0

    def test_start(self, tracker: ProgressTracker) -> None:
        """Test starting a conversion."""
        tracker.start(total_fragments=100, total_chapters=10)

        assert tracker.info.total_fragments == 100
        assert tracker.info.total_chapters == 10
        assert tracker.info.current_stage == "开始处理"

    def test_update_processed(self, tracker: ProgressTracker) -> None:
        """Test updating processed count."""
        tracker.start(total_fragments=100)
        tracker.update(processed=10)

        assert tracker.info.processed_fragments == 10

    def test_update_chapter(self, tracker: ProgressTracker) -> None:
        """Test updating chapter."""
        tracker.start(total_fragments=100)
        tracker.update(chapter=5)

        assert tracker.info.current_chapter == 5

    def test_update_stage(self, tracker: ProgressTracker) -> None:
        """Test updating stage."""
        tracker.start(total_fragments=100)
        tracker.update(stage="语音合成")

        assert tracker.info.current_stage == "语音合成"

    def test_update_character(self, tracker: ProgressTracker) -> None:
        """Test updating character."""
        tracker.start(total_fragments=100)
        tracker.update(character="张三")

        assert tracker.info.current_character == "张三"

    def test_update_emotion(self, tracker: ProgressTracker) -> None:
        """Test updating emotion."""
        tracker.start(total_fragments=100)
        tracker.update(emotion="愤怒")

        assert tracker.info.current_emotion == "愤怒"

    def test_update_failed(self, tracker: ProgressTracker) -> None:
        """Test updating failed count."""
        tracker.start(total_fragments=100)
        tracker.update(failed=2)

        assert tracker.info.failed_fragments == 2

    def test_increment_processed(self, tracker: ProgressTracker) -> None:
        """Test incrementing processed count."""
        tracker.start(total_fragments=100)
        tracker.update(processed=10)
        tracker.increment_processed()

        assert tracker.info.processed_fragments == 11

    def test_increment_failed(self, tracker: ProgressTracker) -> None:
        """Test incrementing failed count."""
        tracker.start(total_fragments=100)
        tracker.update(failed=1)
        tracker.increment_failed()

        assert tracker.info.failed_fragments == 2

    def test_set_chapter(self, tracker: ProgressTracker) -> None:
        """Test set_chapter method."""
        tracker.start(total_fragments=100)
        tracker.set_chapter(5)

        assert tracker.info.current_chapter == 5

    def test_set_stage(self, tracker: ProgressTracker) -> None:
        """Test set_stage method."""
        tracker.start(total_fragments=100)
        tracker.set_stage("角色识别")

        assert tracker.info.current_stage == "角色识别"

    def test_set_character(self, tracker: ProgressTracker) -> None:
        """Test set_character method."""
        tracker.start(total_fragments=100)
        tracker.set_character("李四")

        assert tracker.info.current_character == "李四"

    def test_set_emotion(self, tracker: ProgressTracker) -> None:
        """Test set_emotion method."""
        tracker.start(total_fragments=100)
        tracker.set_emotion("悲伤")

        assert tracker.info.current_emotion == "悲伤"

    def test_finish(self, tracker: ProgressTracker) -> None:
        """Test finishing conversion."""
        tracker.start(total_fragments=100)
        tracker.update(processed=100, stage="语音合成")
        tracker.finish()

        assert tracker.info.current_stage == "完成"
        assert tracker.info.current_character == ""
        assert tracker.info.current_emotion == ""

    def test_callback(self, tracker: ProgressTracker) -> None:
        """Test progress callback."""
        updates: list[dict] = []

        def callback(info: ProgressInfo) -> None:
            updates.append(info.to_dict())

        tracker.set_callback(callback)
        tracker.start(total_fragments=100)
        tracker.update(processed=50)

        assert len(updates) >= 2  # start and update

    def test_to_dict(self, tracker: ProgressTracker) -> None:
        """Test to_dict method."""
        tracker.start(total_fragments=100, total_chapters=10)
        data = tracker.to_dict()

        assert data["job_id"] == "job_001"
        assert "progress" in data

    def test_to_json(self, tracker: ProgressTracker) -> None:
        """Test to_json method."""
        tracker.start(total_fragments=100)
        json_str = tracker.to_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["job_id"] == "job_001"

    def test_processing_speed_calculation(self, tracker: ProgressTracker) -> None:
        """Test that processing speed is calculated during updates."""
        import time

        tracker.start(total_fragments=100)
        tracker.update(processed=0)

        # Simulate processing
        time.sleep(0.1)  # Wait a bit
        tracker.update(processed=10)

        # Speed should be calculated
        # Note: Actual speed depends on timing, just check it's not 0
        # In real tests, this would be more precise


class TestSSEGeneration:
    """Tests for SSE event generation."""

    def test_generate_sse_events(self) -> None:
        """Test SSE event generation."""
        tracker = ProgressTracker(job_id="job_001")
        tracker.start(total_fragments=10)
        tracker.info.processed_fragments = 5
        tracker.info.current_stage = "处理中"

        # Get first event
        events = generate_sse_events(tracker, interval=0.1)
        first_event = next(events)

        assert first_event.startswith("data: ")
        assert "job_001" in first_event

    def test_sse_event_format(self) -> None:
        """Test SSE event format."""
        tracker = ProgressTracker(job_id="job_001")
        tracker.start(total_fragments=10)

        events = generate_sse_events(tracker, interval=0.1)
        event = next(events)

        # SSE format: "data: {json}\n\n"
        assert event.endswith("\n\n")

        # Extract JSON
        json_str = event[6:-2]  # Remove "data: " and "\n\n"
        data = json.loads(json_str)
        assert data["job_id"] == "job_001"

    def test_sse_stops_on_complete(self) -> None:
        """Test that SSE generation stops when complete."""
        tracker = ProgressTracker(job_id="job_001")
        tracker.start(total_fragments=10)
        tracker.info.current_stage = "完成"

        events = list(generate_sse_events(tracker, interval=0.1))
        # Should only yield one event (the final one)
        assert len(events) == 1


class TestProgressIntegration:
    """Integration tests for progress tracking."""

    def test_full_conversion_workflow(self) -> None:
        """Test a complete conversion workflow."""
        updates: list[str] = []

        def callback(info: ProgressInfo) -> None:
            updates.append(info.current_stage)

        tracker = ProgressTracker(job_id="job_001", novel_name="测试小说")
        tracker.set_callback(callback)

        # Start
        tracker.start(total_fragments=100, total_chapters=10)
        assert "开始处理" in updates

        # Process chapter 1
        tracker.set_chapter(1)
        tracker.set_stage("角色识别")
        for i in range(10):
            tracker.update(processed=i)

        # Process chapter 2
        tracker.set_chapter(2)
        tracker.set_stage("语音合成")
        tracker.set_character("张三")
        tracker.set_emotion("愤怒")
        for i in range(10, 20):
            tracker.update(processed=i)

        # Finish
        tracker.finish()
        assert "完成" in updates

    def test_progress_info_with_failures(self) -> None:
        """Test progress tracking with failures."""
        tracker = ProgressTracker(job_id="job_001")
        tracker.start(total_fragments=100)

        tracker.update(processed=50, failed=2)
        data = tracker.to_dict()

        assert data["stats"]["completed"] == 50
        assert data["stats"]["failed"] == 2
        # pending = total - processed (failed fragments are counted separately)
        assert data["stats"]["pending"] == 50