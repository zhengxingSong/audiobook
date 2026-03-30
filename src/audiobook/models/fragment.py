"""Fragment-related data models for audiobook TTS system."""

from dataclasses import dataclass

from audiobook.models.base import FragmentStatus
from audiobook.models.character import Emotion


@dataclass
class Fragment:
    """Represents a text fragment to be converted to audio."""

    fragment_id: str
    block_id: str
    character: str
    voice_id: str
    emotion: Emotion
    audio_path: str
    duration: float
    status: FragmentStatus = FragmentStatus.PENDING


@dataclass
class AudioFragment:
    """Represents an audio fragment with actual audio data."""

    fragment_id: str
    audio_data: bytes
    duration: float
    sample_rate: int = 44100
    format: str = "wav"