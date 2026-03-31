"""Tests for Preview Player utilities."""

import pytest

from audiobook.utils.preview import (
    SAMPLE_VOICES,
    ComparisonResult,
    PreviewPlayer,
    PreviewRequest,
    PreviewResult,
    VoiceCandidate,
)


class TestPreviewRequest:
    """Tests for PreviewRequest dataclass."""

    def test_creation_minimal(self) -> None:
        """Test creating a minimal request."""
        request = PreviewRequest(
            voice_id="voice_001",
            text="测试文本",
        )
        assert request.voice_id == "voice_001"
        assert request.text == "测试文本"
        assert request.emotion is None

    def test_creation_with_emotion(self) -> None:
        """Test creating a request with emotion."""
        request = PreviewRequest(
            voice_id="voice_001",
            text="测试文本",
            emotion="angry",
            emotion_intensity="强烈",
        )
        assert request.emotion == "angry"
        assert request.emotion_intensity == "强烈"


class TestPreviewResult:
    """Tests for PreviewResult dataclass."""

    def test_default_values(self) -> None:
        """Test default result values."""
        result = PreviewResult(voice_id="voice_001")
        assert result.voice_id == "voice_001"
        assert result.audio_data == b""
        assert result.duration == 0.0
        assert result.audio_url is None

    def test_custom_values(self) -> None:
        """Test custom result values."""
        result = PreviewResult(
            voice_id="voice_001",
            audio_data=b"fake_audio",
            duration=5.0,
            audio_url="/preview/voice_001.wav",
            format="mp3",
        )
        assert result.audio_data == b"fake_audio"
        assert result.duration == 5.0
        assert result.audio_url == "/preview/voice_001.wav"


class TestVoiceCandidate:
    """Tests for VoiceCandidate dataclass."""

    def test_creation(self) -> None:
        """Test creating a voice candidate."""
        candidate = VoiceCandidate(
            voice_id="voice_001",
            name="青年男声",
            match_score=90,
            match_reasons=["声音温润", "适合主角"],
        )
        assert candidate.voice_id == "voice_001"
        assert candidate.match_score == 90
        assert len(candidate.match_reasons) == 2

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        candidate = VoiceCandidate(
            voice_id="voice_001",
            name="青年男声",
            match_score=90,
            match_reasons=["test"],
            preview=PreviewResult(
                voice_id="voice_001",
                duration=3.0,
                audio_url="/test.wav",
            ),
        )
        data = candidate.to_dict()

        assert data["voice_id"] == "voice_001"
        assert data["match_score"] == 90
        assert data["preview_url"] == "/test.wav"
        assert data["duration"] == 3.0

    def test_to_dict_no_preview(self) -> None:
        """Test to_dict with no preview."""
        candidate = VoiceCandidate(voice_id="voice_001")
        data = candidate.to_dict()

        assert data["preview_url"] is None
        assert data["duration"] == 0


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_default_values(self) -> None:
        """Test default comparison result."""
        result = ComparisonResult()
        assert len(result.candidates) == 0
        assert result.recommended is None

    def test_with_candidates(self) -> None:
        """Test result with candidates."""
        result = ComparisonResult(
            candidates=[
                VoiceCandidate(voice_id="voice_001", match_score=90),
                VoiceCandidate(voice_id="voice_002", match_score=80),
            ],
            recommended="voice_001",
            sample_text="测试文本",
        )
        assert len(result.candidates) == 2
        assert result.recommended == "voice_001"

    def test_to_dict(self) -> None:
        """Test dictionary conversion."""
        result = ComparisonResult(
            candidates=[VoiceCandidate(voice_id="voice_001")],
            sample_text="测试",
        )
        data = result.to_dict()

        assert "candidates" in data
        assert data["sample_text"] == "测试"


class TestPreviewPlayer:
    """Tests for PreviewPlayer class."""

    @pytest.fixture
    def player(self) -> PreviewPlayer:
        """Create a player for testing."""
        return PreviewPlayer()

    def test_initialization(self, player: PreviewPlayer) -> None:
        """Test player initialization."""
        assert player.tts_endpoint is None
        assert len(player._previews) == 0

    def test_initialization_with_endpoint(self) -> None:
        """Test player with TTS endpoint."""
        player = PreviewPlayer(tts_endpoint="http://localhost:9880")
        assert player.tts_endpoint == "http://localhost:9880"

    def test_generate_preview(self, player: PreviewPlayer) -> None:
        """Test generating a single preview."""
        preview = player.generate_preview(
            voice_id="voice_001",
            text="你好，这是测试。",
        )

        assert isinstance(preview, PreviewResult)
        assert preview.voice_id == "voice_001"
        assert preview.duration > 0

    def test_generate_preview_with_emotion(self, player: PreviewPlayer) -> None:
        """Test generating preview with emotion."""
        preview = player.generate_preview(
            voice_id="voice_001",
            text="我很生气！",
            emotion="angry",
        )

        assert preview.voice_id == "voice_001"

    def test_preview_caching(self, player: PreviewPlayer) -> None:
        """Test that previews are cached."""
        preview1 = player.generate_preview(
            voice_id="voice_001",
            text="测试文本",
        )
        preview2 = player.generate_preview(
            voice_id="voice_001",
            text="测试文本",
        )

        # Should return cached result
        assert preview1 is preview2

    def test_clear_cache(self, player: PreviewPlayer) -> None:
        """Test clearing the cache."""
        player.generate_preview("voice_001", "test")
        assert len(player._previews) > 0

        player.clear_cache()
        assert len(player._previews) == 0

    def test_generate_comparison(self, player: PreviewPlayer) -> None:
        """Test generating voice comparison."""
        voices = [
            {"voice_id": "voice_001", "match_score": 90},
            {"voice_id": "voice_002", "match_score": 80},
        ]

        comparison = player.generate_comparison(
            voices=voices,
            text="测试文本",
        )

        assert isinstance(comparison, ComparisonResult)
        assert len(comparison.candidates) == 2
        assert comparison.recommended == "voice_001"  # Higher score

    def test_generate_comparison_with_sample_voices(self, player: PreviewPlayer) -> None:
        """Test comparison with sample voice data."""
        comparison = player.generate_comparison(
            voices=SAMPLE_VOICES,
            text="测试文本",
        )

        assert len(comparison.candidates) == 3
        # voice_001 should be recommended (92 score)
        assert comparison.recommended == "voice_001"

    def test_get_preview_text_default(self, player: PreviewPlayer) -> None:
        """Test getting default preview text."""
        text = player.get_preview_text()
        assert len(text) > 0
        assert "我是" in text or "你好" in text

    def test_get_preview_text_with_character(self, player: PreviewPlayer) -> None:
        """Test preview text with character name."""
        text = player.get_preview_text(character_name="张三")
        assert "张三" in text

    def test_get_preview_text_with_emotion(self, player: PreviewPlayer) -> None:
        """Test preview text for different emotions."""
        angry_text = player.get_preview_text(emotion="angry")
        assert "生气" in angry_text or "愤怒" in angry_text

        sad_text = player.get_preview_text(emotion="sad")
        assert "难过" in sad_text or "悲伤" in sad_text

    def test_get_preview_text_custom(self, player: PreviewPlayer) -> None:
        """Test custom preview text."""
        text = player.get_preview_text(custom_text="这是自定义文本")
        assert text == "这是自定义文本"


class TestSampleVoices:
    """Tests for sample voice data."""

    def test_sample_voices_structure(self) -> None:
        """Test that sample voices have expected structure."""
        for voice in SAMPLE_VOICES:
            assert "voice_id" in voice
            assert "name" in voice
            assert "match_score" in voice

    def test_sample_voices_scores(self) -> None:
        """Test that match scores are valid."""
        for voice in SAMPLE_VOICES:
            assert 0 <= voice["match_score"] <= 100


class TestPreviewIntegration:
    """Integration tests for preview functionality."""

    def test_full_preview_workflow(self) -> None:
        """Test complete preview workflow."""
        player = PreviewPlayer()

        # Get preview text
        text = player.get_preview_text(
            character_name="张三",
            emotion="angry",
        )

        # Generate preview
        preview = player.generate_preview(
            voice_id="voice_001",
            text=text,
            emotion="angry",
        )

        assert preview.voice_id == "voice_001"
        assert preview.duration > 0

    def test_comparison_workflow(self) -> None:
        """Test complete comparison workflow."""
        player = PreviewPlayer()

        # Generate comparison for character
        comparison = player.generate_comparison(
            voices=SAMPLE_VOICES,
            text="我是张三，很高兴认识你。",
        )

        # Check results
        assert len(comparison.candidates) == 3
        assert comparison.recommended is not None

        # Get recommended voice details
        recommended = next(
            c for c in comparison.candidates
            if c.voice_id == comparison.recommended
        )
        assert recommended.match_score >= 90

        # Verify all candidates have previews
        for candidate in comparison.candidates:
            assert candidate.preview is not None
            assert candidate.preview.duration > 0