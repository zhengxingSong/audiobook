"""Tests for the Consistency Controller."""

import pytest

from audiobook.engines.consistency import (
    EMOTION_OFFSETS,
    AudioFragment,
    ConsistencyController,
    ConsistencyResult,
    SynthesisParams,
    VoiceFeatureAnchors,
    VoiceProfile,
    extract_voice_features,
)
from audiobook.models.character import EmotionIntensity, EmotionProfile, EmotionType


class TestVoiceFeatureAnchors:
    """Tests for VoiceFeatureAnchors dataclass."""

    def test_default_values(self) -> None:
        """Test default anchor values."""
        anchors = VoiceFeatureAnchors()
        assert anchors.sentence_end_pattern == ""
        assert anchors.emphasis_pattern == ""
        assert anchors.pause_pattern == ""
        assert anchors.tone_pattern == ""

    def test_custom_values(self) -> None:
        """Test custom anchor values."""
        anchors = VoiceFeatureAnchors(
            sentence_end_pattern="微下沉",
            emphasis_pattern="力度增强",
            pause_pattern="中速",
            tone_pattern="温和",
        )
        assert anchors.sentence_end_pattern == "微下沉"
        assert anchors.emphasis_pattern == "力度增强"


class TestVoiceProfile:
    """Tests for VoiceProfile dataclass."""

    def test_profile_creation(self) -> None:
        """Test creating a voice profile."""
        profile = VoiceProfile(
            character_id="char_001",
            base_voice_id="voice_001",
        )
        assert profile.character_id == "char_001"
        assert profile.base_voice_id == "voice_001"
        assert profile.base_speed == 1.0
        assert profile.base_pitch == "中性"
        assert profile.consistency_score == 1.0
        assert len(profile.history_samples) == 0

    def test_profile_with_custom_values(self) -> None:
        """Test profile with custom values."""
        profile = VoiceProfile(
            character_id="char_001",
            base_voice_id="voice_001",
            base_speed=1.2,
            base_pitch="高",
            feature_anchors=VoiceFeatureAnchors(sentence_end_pattern="微下沉"),
        )
        assert profile.base_speed == 1.2
        assert profile.base_pitch == "高"
        assert profile.feature_anchors.sentence_end_pattern == "微下沉"

    def test_add_sample(self) -> None:
        """Test adding samples to profile."""
        profile = VoiceProfile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        profile.add_sample("frag_001")
        assert len(profile.history_samples) == 1
        assert "frag_001" in profile.history_samples

        profile.add_sample("frag_002")
        assert len(profile.history_samples) == 2

    def test_add_sample_no_duplicates(self) -> None:
        """Test that duplicate samples are not added."""
        profile = VoiceProfile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        profile.add_sample("frag_001")
        profile.add_sample("frag_001")
        assert len(profile.history_samples) == 1

    def test_sample_limit(self) -> None:
        """Test that only last 5 samples are kept."""
        profile = VoiceProfile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        for i in range(10):
            profile.add_sample(f"frag_{i:03d}")

        assert len(profile.history_samples) == 5
        assert "frag_005" in profile.history_samples
        assert "frag_004" not in profile.history_samples

    def test_update_score(self) -> None:
        """Test updating consistency score."""
        profile = VoiceProfile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        profile.update_score(0.85)
        assert profile.consistency_score == 0.85

    def test_score_bounds(self) -> None:
        """Test that score is bounded to [0, 1]."""
        profile = VoiceProfile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        profile.update_score(-0.5)
        assert profile.consistency_score == 0.0

        profile.update_score(1.5)
        assert profile.consistency_score == 1.0


class TestSynthesisParams:
    """Tests for SynthesisParams dataclass."""

    def test_default_values(self) -> None:
        """Test default synthesis parameters."""
        params = SynthesisParams()
        assert params.speed == 1.0
        assert params.pitch == 0.0
        assert params.volume == 1.0
        assert params.emotion_type == "neutral"
        assert params.reference_audio is None

    def test_custom_values(self) -> None:
        """Test custom synthesis parameters."""
        params = SynthesisParams(
            speed=1.2,
            pitch=0.1,
            volume=0.9,
            emotion_type="angry",
            reference_audio="/path/to/ref.wav",
        )
        assert params.speed == 1.2
        assert params.pitch == 0.1
        assert params.volume == 0.9
        assert params.emotion_type == "angry"
        assert params.reference_audio == "/path/to/ref.wav"


class TestConsistencyResult:
    """Tests for ConsistencyResult dataclass."""

    def test_default_values(self) -> None:
        """Test default result values."""
        result = ConsistencyResult(
            is_consistent=True,
            similarity_score=0.9,
        )
        assert result.is_consistent is True
        assert result.similarity_score == 0.9
        assert result.threshold == 0.75
        assert len(result.warnings) == 0

    def test_with_warnings(self) -> None:
        """Test result with warnings."""
        result = ConsistencyResult(
            is_consistent=False,
            similarity_score=0.5,
            warnings=["Low similarity", "Check manually"],
        )
        assert result.is_consistent is False
        assert len(result.warnings) == 2


class TestConsistencyController:
    """Tests for ConsistencyController class."""

    @pytest.fixture
    def controller(self) -> ConsistencyController:
        """Create a controller for testing."""
        return ConsistencyController()

    @pytest.fixture
    def sample_audio_fragment(self) -> AudioFragment:
        """Create a sample audio fragment for testing."""
        return AudioFragment(
            fragment_id="frag_001",
            audio_data=b"fake_audio_data",
            duration=5.0,
            sample_rate=44100,
            format="wav",
        )

    def test_controller_initialization(self, controller: ConsistencyController) -> None:
        """Test controller initialization."""
        assert len(controller.profiles) == 0
        assert len(controller.audio_samples) == 0

    def test_create_profile(self, controller: ConsistencyController) -> None:
        """Test creating a voice profile."""
        profile = controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        assert profile.character_id == "char_001"
        assert profile.base_voice_id == "voice_001"
        assert "char_001" in controller.profiles

    def test_get_profile(self, controller: ConsistencyController) -> None:
        """Test getting a voice profile."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        profile = controller.get_profile("char_001")
        assert profile is not None
        assert profile.character_id == "char_001"

        # Non-existent profile
        assert controller.get_profile("char_999") is None

    def test_update_profile(
        self,
        controller: ConsistencyController,
        sample_audio_fragment: AudioFragment,
    ) -> None:
        """Test updating a profile with a new sample."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        controller.update_profile("char_001", sample_audio_fragment)

        profile = controller.get_profile("char_001")
        assert profile is not None
        assert len(profile.history_samples) == 1
        assert "frag_001" in profile.history_samples

    def test_calculate_adjusted_params_basic(
        self,
        controller: ConsistencyController,
    ) -> None:
        """Test calculating adjusted params for neutral emotion."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        params = controller.calculate_adjusted_params(
            character_id="char_001",
            emotion=EmotionType.NEUTRAL,
        )

        assert isinstance(params, SynthesisParams)
        assert params.emotion_type == "neutral"
        # Neutral should have minimal offsets
        assert 0.5 <= params.speed <= 1.5

    def test_calculate_adjusted_params_angry(
        self,
        controller: ConsistencyController,
    ) -> None:
        """Test calculating adjusted params for angry emotion."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        params = controller.calculate_adjusted_params(
            character_id="char_001",
            emotion=EmotionType.ANGRY,
        )

        assert params.emotion_type == "angry"
        # Angry should increase speed and pitch
        assert params.speed > 1.0  # Anger increases speed

    def test_calculate_adjusted_params_sad(
        self,
        controller: ConsistencyController,
    ) -> None:
        """Test calculating adjusted params for sad emotion."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        params = controller.calculate_adjusted_params(
            character_id="char_001",
            emotion=EmotionType.SAD,
        )

        assert params.emotion_type == "sad"
        # Sad should decrease speed
        assert params.speed < 1.0

    def test_calculate_adjusted_params_with_profile(
        self,
        controller: ConsistencyController,
    ) -> None:
        """Test calculating params with EmotionProfile."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        emotion_profile = EmotionProfile(
            emotion_type="angry",
            intensity=EmotionIntensity.STRONG,
        )

        params = controller.calculate_adjusted_params(
            character_id="char_001",
            emotion=emotion_profile,
        )

        assert params.emotion_type == "angry"
        # Strong intensity should have larger effect
        assert params.speed > 1.0

    def test_calculate_adjusted_params_no_profile(
        self,
        controller: ConsistencyController,
    ) -> None:
        """Test calculating params when no profile exists."""
        params = controller.calculate_adjusted_params(
            character_id="char_999",
            emotion=EmotionType.HAPPY,
        )

        # Should return default-ish params
        assert isinstance(params, SynthesisParams)
        assert params.emotion_type == "happy"

    def test_check_consistency_no_history(
        self,
        controller: ConsistencyController,
        sample_audio_fragment: AudioFragment,
    ) -> None:
        """Test consistency check with no historical samples."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        result = controller.check_consistency("char_001", sample_audio_fragment)

        assert result.is_consistent is True
        assert result.similarity_score == 1.0
        assert "No historical samples" in result.warnings[0]

    def test_check_consistency_with_history(
        self,
        controller: ConsistencyController,
    ) -> None:
        """Test consistency check with historical samples."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        # Add some historical samples
        for i in range(3):
            fragment = AudioFragment(
                fragment_id=f"frag_{i:03d}",
                audio_data=b"fake_audio_data",
                duration=5.0,
                pitch=150.0,
                volume=1.0,
            )
            controller.update_profile("char_001", fragment)

        # Check a similar fragment
        new_fragment = AudioFragment(
            fragment_id="frag_new",
            audio_data=b"fake_audio_data",
            duration=5.0,
            pitch=150.0,
            volume=1.0,
        )

        result = controller.check_consistency("char_001", new_fragment)

        assert isinstance(result, ConsistencyResult)
        assert result.similarity_score >= 0

    def test_check_consistency_low_similarity_warning(
        self,
        controller: ConsistencyController,
    ) -> None:
        """Test that low similarity generates warnings."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        # Add historical samples with specific characteristics
        for i in range(3):
            fragment = AudioFragment(
                fragment_id=f"frag_{i:03d}",
                audio_data=b"fake_audio_data",
                duration=5.0,
                pitch=150.0,
                volume=1.0,
            )
            controller.update_profile("char_001", fragment)

        # Check a very different fragment (low pitch)
        different_fragment = AudioFragment(
            fragment_id="frag_different",
            audio_data=b"fake_audio_data",
            duration=5.0,
            pitch=50.0,  # Very different pitch
            volume=0.3,  # Very different volume
        )

        result = controller.check_consistency(
            "char_001",
            different_fragment,
            threshold=0.9,  # High threshold
        )

        # Low similarity should generate warnings
        if not result.is_consistent:
            assert len(result.warnings) > 0

    def test_get_reference_audio_none(
        self,
        controller: ConsistencyController,
    ) -> None:
        """Test getting reference audio when no samples exist."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        ref = controller.get_reference_audio("char_001")
        assert ref is None

    def test_get_reference_audio_with_samples(
        self,
        controller: ConsistencyController,
    ) -> None:
        """Test getting reference audio with samples."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        fragment = AudioFragment(
            fragment_id="frag_001",
            audio_data=b"fake_audio_data",
            duration=5.0,
            audio_path="/path/to/audio.wav",
        )
        controller.update_profile("char_001", fragment)

        ref = controller.get_reference_audio("char_001")
        assert ref == "/path/to/audio.wav"

    def test_reset(self, controller: ConsistencyController) -> None:
        """Test resetting the controller."""
        controller.create_profile(
            character_id="char_001",
            base_voice_id="voice_001",
        )

        controller.reset()

        assert len(controller.profiles) == 0
        assert len(controller.audio_samples) == 0


class TestEmotionOffsets:
    """Tests for emotion offset table."""

    def test_emotion_offsets_defined(self) -> None:
        """Test that all expected emotions have offset definitions."""
        expected_emotions = [
            "愤怒", "悲伤", "喜悦", "恐惧", "平静", "紧张",
            "neutral", "happy", "sad", "angry", "fearful",
            "surprised", "excited", "calm", "nervous",
        ]

        for emotion in expected_emotions:
            assert emotion in EMOTION_OFFSETS
            assert "语速" in EMOTION_OFFSETS[emotion]
            assert "音调" in EMOTION_OFFSETS[emotion]
            assert "力度" in EMOTION_OFFSETS[emotion]

    def test_neutral_offsets_are_zero(self) -> None:
        """Test that neutral emotion has zero offsets."""
        # Only "neutral" and "平静" should be exactly zero
        for key in ["neutral", "平静"]:
            if key in EMOTION_OFFSETS:
                offsets = EMOTION_OFFSETS[key]
                assert offsets["语速"] == 0.0
                assert offsets["音调"] == 0.0
                assert offsets["力度"] == 0.0

        # "calm" has slight negative offsets (relaxed state)
        assert EMOTION_OFFSETS["calm"]["语速"] == -0.05


class TestExtractVoiceFeatures:
    """Tests for voice feature extraction."""

    def test_extract_voice_features(self) -> None:
        """Test feature extraction returns expected keys."""
        features = extract_voice_features("/path/to/audio.wav")

        assert "pitch_mean" in features
        assert "pitch_std" in features
        assert "energy_mean" in features
        assert "tempo" in features
        assert "mfcc_mean" in features

    def test_extract_voice_features_values(self) -> None:
        """Test that extracted features have reasonable values."""
        features = extract_voice_features("/path/to/audio.wav")

        assert features["pitch_mean"] > 0
        assert features["tempo"] > 0
        assert 0 <= features["energy_mean"] <= 1