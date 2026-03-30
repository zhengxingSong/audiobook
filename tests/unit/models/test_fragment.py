"""Unit tests for Fragment data models."""

import pytest

from audiobook.models.base import FragmentStatus
from audiobook.models.character import Emotion
from audiobook.models.fragment import Fragment, AudioFragment


class TestFragment:
    """Tests for Fragment dataclass."""

    def test_fragment_creation_with_defaults(self) -> None:
        """Test creating a Fragment with default status."""
        fragment = Fragment(
            fragment_id="frag-001",
            block_id="block-001",
            character="Narrator",
            voice_id="voice-001",
            emotion=Emotion.NEUTRAL,
            audio_path="/audio/frag-001.wav",
            duration=5.5,
        )

        assert fragment.fragment_id == "frag-001"
        assert fragment.block_id == "block-001"
        assert fragment.character == "Narrator"
        assert fragment.voice_id == "voice-001"
        assert fragment.emotion == Emotion.NEUTRAL
        assert fragment.audio_path == "/audio/frag-001.wav"
        assert fragment.duration == 5.5
        assert fragment.status == FragmentStatus.PENDING

    def test_fragment_creation_with_status(self) -> None:
        """Test creating a Fragment with explicit status."""
        fragment = Fragment(
            fragment_id="frag-002",
            block_id="block-001",
            character="Alice",
            voice_id="voice-002",
            emotion=Emotion.HAPPY,
            audio_path="/audio/frag-002.wav",
            duration=3.2,
            status=FragmentStatus.COMPLETED,
        )

        assert fragment.status == FragmentStatus.COMPLETED

    def test_fragment_with_different_emotions(self) -> None:
        """Test Fragment with various emotion types."""
        emotions = [
            Emotion.NEUTRAL,
            Emotion.HAPPY,
            Emotion.SAD,
            Emotion.ANGRY,
            Emotion.FEARFUL,
            Emotion.SURPRISED,
            Emotion.DISGUSTED,
            Emotion.EXCITED,
            Emotion.CALM,
            Emotion.NERVOUS,
        ]

        for emotion in emotions:
            fragment = Fragment(
                fragment_id=f"frag-{emotion.value}",
                block_id="block-001",
                character="Test",
                voice_id="voice-001",
                emotion=emotion,
                audio_path="/audio/test.wav",
                duration=1.0,
            )
            assert fragment.emotion == emotion

    def test_fragment_with_different_statuses(self) -> None:
        """Test Fragment with various status values."""
        statuses = [
            FragmentStatus.PENDING,
            FragmentStatus.PROCESSING,
            FragmentStatus.COMPLETED,
            FragmentStatus.FAILED,
        ]

        for status in statuses:
            fragment = Fragment(
                fragment_id=f"frag-{status.value}",
                block_id="block-001",
                character="Test",
                voice_id="voice-001",
                emotion=Emotion.NEUTRAL,
                audio_path="/audio/test.wav",
                duration=1.0,
                status=status,
            )
            assert fragment.status == status


class TestAudioFragment:
    """Tests for AudioFragment dataclass."""

    def test_audio_fragment_creation_with_defaults(self) -> None:
        """Test creating an AudioFragment with default values."""
        audio_data = b"\x00\x01\x02\x03"
        fragment = AudioFragment(
            fragment_id="audio-001",
            audio_data=audio_data,
            duration=2.5,
        )

        assert fragment.fragment_id == "audio-001"
        assert fragment.audio_data == audio_data
        assert fragment.duration == 2.5
        assert fragment.sample_rate == 44100
        assert fragment.format == "wav"

    def test_audio_fragment_creation_with_custom_values(self) -> None:
        """Test creating an AudioFragment with custom values."""
        audio_data = b"\xff\xfe\xfd\xfc"
        fragment = AudioFragment(
            fragment_id="audio-002",
            audio_data=audio_data,
            duration=4.0,
            sample_rate=48000,
            format="mp3",
        )

        assert fragment.sample_rate == 48000
        assert fragment.format == "mp3"

    def test_audio_fragment_empty_audio_data(self) -> None:
        """Test AudioFragment with empty audio data."""
        fragment = AudioFragment(
            fragment_id="audio-003",
            audio_data=b"",
            duration=0.0,
        )

        assert fragment.audio_data == b""
        assert fragment.duration == 0.0

    def test_audio_fragment_large_audio_data(self) -> None:
        """Test AudioFragment with large audio data."""
        large_audio = b"\x00" * 1_000_000  # 1MB of audio data
        fragment = AudioFragment(
            fragment_id="audio-004",
            audio_data=large_audio,
            duration=60.0,
        )

        assert len(fragment.audio_data) == 1_000_000


class TestFragmentStatus:
    """Tests for FragmentStatus enum."""

    def test_fragment_status_values(self) -> None:
        """Test FragmentStatus enum values."""
        assert FragmentStatus.PENDING.value == "pending"
        assert FragmentStatus.PROCESSING.value == "processing"
        assert FragmentStatus.COMPLETED.value == "completed"
        assert FragmentStatus.FAILED.value == "failed"

    def test_fragment_status_count(self) -> None:
        """Test that FragmentStatus has exactly 4 members."""
        assert len(FragmentStatus) == 4


class TestEmotion:
    """Tests for Emotion enum."""

    def test_emotion_values(self) -> None:
        """Test Emotion enum values."""
        assert Emotion.NEUTRAL.value == "neutral"
        assert Emotion.HAPPY.value == "happy"
        assert Emotion.SAD.value == "sad"
        assert Emotion.ANGRY.value == "angry"
        assert Emotion.FEARFUL.value == "fearful"
        assert Emotion.SURPRISED.value == "surprised"
        assert Emotion.DISGUSTED.value == "disgusted"
        assert Emotion.EXCITED.value == "excited"
        assert Emotion.CALM.value == "calm"
        assert Emotion.NERVOUS.value == "nervous"

    def test_emotion_count(self) -> None:
        """Test that Emotion has exactly 10 members."""
        assert len(Emotion) == 10
