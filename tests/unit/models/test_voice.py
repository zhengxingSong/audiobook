"""Unit tests for voice-related data models."""

import pytest

from audiobook.models.voice import Voice, VoiceCandidate, VoiceParams


class TestVoiceParams:
    """Tests for VoiceParams dataclass."""

    def test_create_with_defaults(self) -> None:
        """Test creating VoiceParams with default values."""
        params = VoiceParams()
        assert params.base_speed == 1.0
        assert params.base_pitch == "中性"
        assert params.feature_anchors == []

    def test_create_with_custom_values(self) -> None:
        """Test creating VoiceParams with custom values."""
        anchors = [{"position": 0.5, "feature": "excited"}]
        params = VoiceParams(
            base_speed=1.2, base_pitch="高", feature_anchors=anchors
        )
        assert params.base_speed == 1.2
        assert params.base_pitch == "高"
        assert params.feature_anchors == anchors

    def test_feature_anchors_mutable(self) -> None:
        """Test that feature_anchors can be modified."""
        params = VoiceParams()
        params.feature_anchors.append({"position": 0.0, "feature": "calm"})
        assert len(params.feature_anchors) == 1


class TestVoice:
    """Tests for Voice dataclass."""

    def test_create_with_required_fields(self) -> None:
        """Test creating Voice with required fields only."""
        voice = Voice(
            voice_id="v001",
            name="小明",
            gender="男",
            age_range="青年",
        )
        assert voice.voice_id == "v001"
        assert voice.name == "小明"
        assert voice.gender == "男"
        assert voice.age_range == "青年"
        assert voice.tags == []
        assert voice.description == ""
        assert voice.embedding is None
        assert voice.audio_path == ""

    def test_create_with_all_fields(self) -> None:
        """Test creating Voice with all fields."""
        embedding = [0.1, 0.2, 0.3, 0.4]
        voice = Voice(
            voice_id="v002",
            name="小红",
            gender="女",
            age_range="少年",
            tags=["温柔", "活泼"],
            description="适合青春小说",
            embedding=embedding,
            audio_path="/voices/v002.wav",
        )
        assert voice.voice_id == "v002"
        assert voice.name == "小红"
        assert voice.gender == "女"
        assert voice.age_range == "少年"
        assert voice.tags == ["温柔", "活泼"]
        assert voice.description == "适合青春小说"
        assert voice.embedding == embedding
        assert voice.audio_path == "/voices/v002.wav"

    def test_gender_values(self) -> None:
        """Test that gender accepts valid Literal values."""
        male_voice = Voice(voice_id="m1", name="男声", gender="男", age_range="成年")
        female_voice = Voice(voice_id="f1", name="女声", gender="女", age_range="成年")
        neutral_voice = Voice(voice_id="n1", name="中性", gender="中性", age_range="成年")

        assert male_voice.gender == "男"
        assert female_voice.gender == "女"
        assert neutral_voice.gender == "中性"

    def test_tags_mutable(self) -> None:
        """Test that tags can be modified."""
        voice = Voice(voice_id="v1", name="测试", gender="男", age_range="成年")
        voice.tags.append("低沉")
        assert "低沉" in voice.tags


class TestVoiceCandidate:
    """Tests for VoiceCandidate dataclass."""

    def test_create_with_voice_only(self) -> None:
        """Test creating VoiceCandidate with voice only."""
        voice = Voice(voice_id="v1", name="测试", gender="男", age_range="成年")
        candidate = VoiceCandidate(voice=voice)
        assert candidate.voice == voice
        assert candidate.confidence == 0.0
        assert candidate.match_reasons == []

    def test_create_with_all_fields(self) -> None:
        """Test creating VoiceCandidate with all fields."""
        voice = Voice(voice_id="v1", name="测试", gender="男", age_range="成年")
        reasons = ["性别匹配", "年龄范围匹配"]
        candidate = VoiceCandidate(
            voice=voice,
            confidence=0.85,
            match_reasons=reasons,
        )
        assert candidate.voice == voice
        assert candidate.confidence == 0.85
        assert candidate.match_reasons == reasons

    def test_match_reasons_mutable(self) -> None:
        """Test that match_reasons can be modified."""
        voice = Voice(voice_id="v1", name="测试", gender="男", age_range="成年")
        candidate = VoiceCandidate(voice=voice)
        candidate.match_reasons.append("新理由")
        assert "新理由" in candidate.match_reasons

    def test_confidence_range(self) -> None:
        """Test that confidence can be set to various values."""
        voice = Voice(voice_id="v1", name="测试", gender="男", age_range="成年")

        low = VoiceCandidate(voice=voice, confidence=0.0)
        high = VoiceCandidate(voice=voice, confidence=1.0)
        mid = VoiceCandidate(voice=voice, confidence=0.5)

        assert low.confidence == 0.0
        assert high.confidence == 1.0
        assert mid.confidence == 0.5