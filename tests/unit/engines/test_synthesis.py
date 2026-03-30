"""Unit tests for VoiceSynthesisEngine."""

import time
from unittest import mock

import pytest
import requests

from audiobook.engines.synthesis import (
    AudioQuality,
    SynthesisConnectionError,
    SynthesisError,
    SynthesisResult,
    SynthesisTimeoutError,
    VoiceSynthesisEngine,
)
from audiobook.models import AudioFragment, EmotionIntensity, EmotionProfile, Voice


@pytest.fixture
def engine() -> VoiceSynthesisEngine:
    """Create a VoiceSynthesisEngine instance for testing."""
    return VoiceSynthesisEngine(
        endpoint="http://localhost:9880",
        timeout=60,
        max_retries=3,
    )


@pytest.fixture
def sample_voice() -> Voice:
    """Create a sample Voice for testing."""
    return Voice(
        voice_id="voice_001",
        name="张三",
        gender="男",
        age_range="中年",
        tags=["沉稳", "磁性"],
        description="中年男性声音，沉稳有磁性",
        audio_path="/path/to/reference.wav",
    )


@pytest.fixture
def sample_emotion() -> EmotionProfile:
    """Create a sample EmotionProfile for testing."""
    return EmotionProfile(
        emotion_type="喜悦",
        intensity=EmotionIntensity.MODERATE,
        components=["兴奋", "期待"],
        scene_context="在生日派对上",
        suggested_adjustment="语调上扬",
    )


class TestVoiceSynthesisEngineInit:
    """Tests for VoiceSynthesisEngine initialization."""

    def test_init_default_params(self):
        """Test initialization with default parameters."""
        engine = VoiceSynthesisEngine()
        assert engine.endpoint == "http://localhost:9880"
        assert engine.timeout == 60
        assert engine.max_retries == 3

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        engine = VoiceSynthesisEngine(
            endpoint="http://custom:8080/",
            timeout=30,
            max_retries=5,
        )
        assert engine.endpoint == "http://custom:8080"
        assert engine.timeout == 30
        assert engine.max_retries == 5


class TestGeneratePrompt:
    """Tests for generate_prompt method."""

    def test_generate_prompt_basic(self, engine, sample_voice, sample_emotion):
        """Test basic prompt generation."""
        text = "你好，世界！"
        prompt = engine.generate_prompt(sample_voice, sample_emotion, text)

        assert "喜悦" in prompt
        assert "中等" in prompt
        assert sample_voice.description in prompt
        assert sample_emotion.scene_context in prompt

    def test_generate_prompt_with_intensity(self, engine, sample_voice):
        """Test prompt generation with different intensities."""
        text = "测试文本"

        # Test each intensity level
        for intensity in EmotionIntensity:
            emotion = EmotionProfile(
                emotion_type="喜悦",
                intensity=intensity,
            )
            prompt = engine.generate_prompt(sample_voice, emotion, text)
            assert prompt is not None
            assert len(prompt) > 0

    def test_generate_prompt_with_components(self, engine, sample_voice):
        """Test prompt generation with emotion components."""
        emotion = EmotionProfile(
            emotion_type="愤怒",
            intensity=EmotionIntensity.STRONG,
            components=["愤怒", "不满", "激动"],
        )
        text = "我不同意！"
        prompt = engine.generate_prompt(sample_voice, emotion, text)

        assert "愤怒" in prompt
        assert "强烈" in prompt

    def test_generate_prompt_minimal(self, engine):
        """Test prompt generation with minimal emotion profile."""
        voice = Voice(
            voice_id="v1",
            name="Test",
            gender="中性",
            age_range="成年",
        )
        emotion = EmotionProfile(
            emotion_type="平静",
            intensity=EmotionIntensity.LIGHT,
        )
        text = "简单的文本"
        prompt = engine.generate_prompt(voice, emotion, text)

        assert prompt is not None


class TestGetEmotionTemplate:
    """Tests for get_emotion_template method."""

    def test_get_emotion_template_chinese(self, engine):
        """Test getting Chinese emotion templates."""
        for emotion_type in ["愤怒", "悲伤", "喜悦", "恐惧", "惊讶", "平静"]:
            template = engine.get_emotion_template(emotion_type)
            assert template is not None
            assert emotion_type in template

    def test_get_emotion_template_english(self, engine):
        """Test getting English emotion templates."""
        mapping = {
            "neutral": "平静",
            "happy": "喜悦",
            "sad": "悲伤",
            "angry": "愤怒",
            "fearful": "恐惧",
            "surprised": "惊讶",
        }
        for eng_type, expected_chinese in mapping.items():
            template = engine.get_emotion_template(eng_type)
            assert template is not None
            assert expected_chinese in template

    def test_get_emotion_template_unknown(self, engine):
        """Test getting unknown emotion template."""
        template = engine.get_emotion_template("unknown_emotion")
        assert template is None


class TestBuildSynthesisParams:
    """Tests for build_synthesis_params method."""

    def test_build_synthesis_params_basic(self, engine, sample_voice, sample_emotion):
        """Test basic parameter building."""
        text = "测试文本内容"
        params = engine.build_synthesis_params(sample_voice, sample_emotion, text)

        assert params["text"] == text
        assert params["text_lang"] == "zh"
        assert params["prompt_lang"] == "zh"
        assert "ref_audio_path" in params

    def test_build_synthesis_params_with_audio_path(
        self, engine, sample_voice, sample_emotion
    ):
        """Test parameter building with reference audio path."""
        text = "测试"
        params = engine.build_synthesis_params(sample_voice, sample_emotion, text)

        assert params["ref_audio_path"] == sample_voice.audio_path

    def test_build_synthesis_params_without_audio_path(self, engine, sample_emotion):
        """Test parameter building without reference audio path."""
        voice = Voice(
            voice_id="v1",
            name="Test",
            gender="中性",
            age_range="成年",
            audio_path="",
        )
        text = "测试"
        params = engine.build_synthesis_params(voice, sample_emotion, text)

        assert "ref_audio_path" not in params or params.get("ref_audio_path") == ""


class TestSynthesize:
    """Tests for synthesize method."""

    @mock.patch("audiobook.engines.synthesis.requests.post")
    def test_synthesize_success(self, mock_post, engine, sample_voice):
        """Test successful synthesis."""
        # Create mock response with WAV-like audio data
        wav_header = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
        audio_data = wav_header + bytes([0] * 100)

        mock_response = mock.Mock()
        mock_response.content = audio_data
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = engine.synthesize(
            prompt="测试提示",
            text="测试文本",
            voice_id="voice_001",
            reference_audio="/path/to/ref.wav",
            fragment_id="frag_001",
        )

        assert isinstance(result, AudioFragment)
        assert result.fragment_id == "frag_001"
        assert result.format == "wav"
        assert result.sample_rate == 44100
        assert len(result.audio_data) > 0

    @mock.patch("audiobook.engines.synthesis.requests.post")
    def test_synthesize_timeout(self, mock_post, engine):
        """Test synthesis timeout handling."""
        mock_post.side_effect = requests.Timeout()

        with pytest.raises(SynthesisTimeoutError) as exc_info:
            engine.synthesize(
                prompt="测试提示",
                text="测试文本",
                voice_id="voice_001",
                reference_audio="/path/to/ref.wav",
            )

        assert "timeout" in str(exc_info.value).lower()

    @mock.patch("audiobook.engines.synthesis.requests.post")
    def test_synthesize_connection_error(self, mock_post, engine):
        """Test synthesis connection error handling."""
        mock_post.side_effect = requests.ConnectionError()

        with pytest.raises(SynthesisConnectionError):
            engine.synthesize(
                prompt="测试提示",
                text="测试文本",
                voice_id="voice_001",
                reference_audio="/path/to/ref.wav",
            )

    @mock.patch("audiobook.engines.synthesis.requests.post")
    def test_synthesize_retry_logic(self, mock_post, engine):
        """Test that synthesis retries on transient failures."""
        # First two calls fail, third succeeds
        wav_header = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
        audio_data = wav_header + bytes([0] * 100)

        success_response = mock.Mock()
        success_response.content = audio_data
        success_response.status_code = 200

        mock_post.side_effect = [
            requests.Timeout(),
            requests.Timeout(),
            success_response,
        ]

        result = engine.synthesize(
            prompt="测试提示",
            text="测试文本",
            voice_id="voice_001",
            reference_audio="/path/to/ref.wav",
        )

        assert isinstance(result, AudioFragment)
        assert mock_post.call_count == 3

    @mock.patch("audiobook.engines.synthesis.requests.post")
    def test_synthesize_max_retries_exceeded(self, mock_post, engine):
        """Test synthesis failure after max retries."""
        mock_post.side_effect = requests.Timeout()

        with pytest.raises(SynthesisTimeoutError):
            engine.synthesize(
                prompt="测试提示",
                text="测试文本",
                voice_id="voice_001",
                reference_audio="/path/to/ref.wav",
            )

        assert mock_post.call_count == engine.max_retries

    @mock.patch("audiobook.engines.synthesis.requests.post")
    def test_synthesize_generates_fragment_id(self, mock_post, engine):
        """Test that synthesis generates fragment_id if not provided."""
        wav_header = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
        audio_data = wav_header + bytes([0] * 100)

        mock_response = mock.Mock()
        mock_response.content = audio_data
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = engine.synthesize(
            prompt="测试提示",
            text="测试文本",
            voice_id="voice_001",
            reference_audio="/path/to/ref.wav",
        )

        assert result.fragment_id.startswith("frag_")


class TestSynthesizeText:
    """Tests for synthesize_text convenience method."""

    @mock.patch("audiobook.engines.synthesis.requests.post")
    def test_synthesize_text_success(
        self, mock_post, engine, sample_voice, sample_emotion
    ):
        """Test successful text synthesis."""
        wav_header = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
        # Generate enough audio data to match expected duration (~1.14s for "你好世界")
        # WAV format: 44100 Hz, 16-bit, mono = 88200 bytes/second
        # 1.14 * 88200 = ~100,548 bytes needed
        audio_data = wav_header + bytes([100] * 100500)  # Non-silent audio with matching duration

        mock_response = mock.Mock()
        mock_response.content = audio_data
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = engine.synthesize_text(
            voice=sample_voice,
            emotion=sample_emotion,
            text="你好世界",
        )

        assert isinstance(result, SynthesisResult)
        assert result.success is True
        assert result.audio_fragment is not None

    @mock.patch("audiobook.engines.synthesis.requests.post")
    def test_synthesize_text_failure(self, mock_post, engine, sample_voice, sample_emotion):
        """Test text synthesis failure handling."""
        mock_post.side_effect = requests.ConnectionError()

        result = engine.synthesize_text(
            voice=sample_voice,
            emotion=sample_emotion,
            text="测试文本",
        )

        assert isinstance(result, SynthesisResult)
        assert result.success is False
        assert result.audio_fragment is None
        assert len(result.error_message) > 0


class TestValidateAudio:
    """Tests for validate_audio method."""

    def test_validate_audio_success(self, engine):
        """Test successful audio validation."""
        # Create non-silent audio data
        wav_header = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
        audio_data = wav_header + bytes([100] * 4000)  # Non-silent audio

        fragment = AudioFragment(
            fragment_id="frag_001",
            audio_data=audio_data,
            duration=2.0,
            sample_rate=44100,
            format="wav",
        )

        quality = engine.validate_audio(fragment, expected_duration=2.0)

        assert isinstance(quality, AudioQuality)
        assert quality.is_valid is True
        assert quality.is_silent is False

    def test_validate_audio_silent(self, engine):
        """Test validation of silent audio."""
        # Create silent audio data (all zeros)
        wav_header = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
        audio_data = wav_header + bytes([0] * 4000)  # Silent audio

        fragment = AudioFragment(
            fragment_id="frag_001",
            audio_data=audio_data,
            duration=2.0,
            sample_rate=44100,
            format="wav",
        )

        quality = engine.validate_audio(fragment, expected_duration=2.0)

        assert quality.is_silent is True
        assert "silent" in quality.issues[0].lower()

    def test_validate_audio_duration_mismatch(self, engine):
        """Test validation with duration mismatch."""
        wav_header = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
        audio_data = wav_header + bytes([100] * 4000)

        fragment = AudioFragment(
            fragment_id="frag_001",
            audio_data=audio_data,
            duration=5.0,  # Much longer than expected
            sample_rate=44100,
            format="wav",
        )

        quality = engine.validate_audio(fragment, expected_duration=2.0)

        assert quality.duration_match is False
        assert any("Duration mismatch" in issue for issue in quality.issues)


class TestEstimateDuration:
    """Tests for _estimate_duration method."""

    def test_estimate_duration_chinese_text(self, engine):
        """Test duration estimation for Chinese text."""
        text = "你好世界"  # 4 Chinese characters
        duration = engine._estimate_duration(text)

        # Chinese chars at ~3.5 chars/sec
        expected = 4 / 3.5
        assert abs(duration - expected) < 0.1

    def test_estimate_duration_mixed_text(self, engine):
        """Test duration estimation for mixed text."""
        text = "Hello 你好 World 世界"  # Mixed English and Chinese
        duration = engine._estimate_duration(text)

        assert duration > 0

    def test_estimate_duration_empty_text(self, engine):
        """Test duration estimation for empty text."""
        duration = engine._estimate_duration("")
        assert duration == 0.5  # Minimum duration

    def test_estimate_duration_long_text(self, engine):
        """Test duration estimation for long text."""
        text = "这是一个很长的测试文本" * 10
        duration = engine._estimate_duration(text)

        assert duration > 0


class TestIsSilent:
    """Tests for _is_silent method."""

    def test_is_silent_true(self, engine):
        """Test silence detection for silent audio."""
        wav_header = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
        silent_audio = wav_header + bytes([0] * 4000)

        is_silent = engine._is_silent(silent_audio)

        assert is_silent is True

    def test_is_silent_false(self, engine):
        """Test silence detection for non-silent audio."""
        wav_header = b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
        loud_audio = wav_header + bytes([200, 200, 200, 200] * 1000)

        is_silent = engine._is_silent(loud_audio)

        assert is_silent is False

    def test_is_silent_empty_audio(self, engine):
        """Test silence detection for empty audio."""
        is_silent = engine._is_silent(b"")
        assert is_silent is True

    def test_is_silent_very_short_audio(self, engine):
        """Test silence detection for very short audio."""
        is_silent = engine._is_silent(b"short")
        assert is_silent is True


class TestHealthCheck:
    """Tests for health_check method."""

    @mock.patch("audiobook.engines.synthesis.requests.get")
    def test_health_check_healthy(self, mock_get, engine):
        """Test health check when service is healthy."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        is_healthy = engine.health_check()

        assert is_healthy is True
        mock_get.assert_called_once_with("http://localhost:9880/health", timeout=5)

    @mock.patch("audiobook.engines.synthesis.requests.get")
    def test_health_check_unhealthy(self, mock_get, engine):
        """Test health check when service is unhealthy."""
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        is_healthy = engine.health_check()

        assert is_healthy is False

    @mock.patch("audiobook.engines.synthesis.requests.get")
    def test_health_check_connection_error(self, mock_get, engine):
        """Test health check with connection error."""
        mock_get.side_effect = requests.ConnectionError()

        is_healthy = engine.health_check()

        assert is_healthy is False


class TestSynthesisResult:
    """Tests for SynthesisResult dataclass."""

    def test_synthesis_result_success(self):
        """Test successful synthesis result."""
        fragment = AudioFragment(
            fragment_id="frag_001",
            audio_data=b"test audio data",
            duration=2.5,
        )

        result = SynthesisResult(
            success=True,
            audio_fragment=fragment,
            processing_time=1.5,
        )

        assert result.success is True
        assert result.audio_fragment == fragment
        assert result.error_message == ""

    def test_synthesis_result_failure(self):
        """Test failed synthesis result."""
        result = SynthesisResult(
            success=False,
            error_message="Connection timeout",
            retry_count=3,
        )

        assert result.success is False
        assert result.audio_fragment is None
        assert result.error_message == "Connection timeout"


class TestAudioQuality:
    """Tests for AudioQuality dataclass."""

    def test_audio_quality_valid(self):
        """Test valid audio quality."""
        quality = AudioQuality(
            is_valid=True,
            is_silent=False,
            duration_match=True,
            expected_duration=2.0,
            actual_duration=2.1,
            deviation_percent=5.0,
            issues=[],
        )

        assert quality.is_valid is True
        assert len(quality.issues) == 0

    def test_audio_quality_invalid(self):
        """Test invalid audio quality."""
        quality = AudioQuality(
            is_valid=False,
            is_silent=True,
            duration_match=False,
            expected_duration=2.0,
            actual_duration=0.0,
            deviation_percent=100.0,
            issues=["Audio is silent", "Duration mismatch"],
        )

        assert quality.is_valid is False
        assert len(quality.issues) == 2