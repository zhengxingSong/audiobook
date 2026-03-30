"""Fragment-related data models for audiobook TTS system."""

from dataclasses import dataclass
from typing import Optional

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
    """Represents an audio fragment with actual audio data.

    Attributes:
        fragment_id: Unique identifier for this fragment.
        audio_data: Raw audio bytes.
        duration: Duration in seconds.
        sample_rate: Audio sample rate (default 44100).
        format: Audio format (default wav).
        audio_path: Path to the audio file (optional, for reference).
        pitch: Pitch value extracted from audio (optional).
        volume: Volume/energy level (optional).
        character_id: Associated character ID (optional).
    """

    fragment_id: str
    audio_data: bytes
    duration: float
    sample_rate: int = 44100
    format: str = "wav"
    audio_path: Optional[str] = None
    pitch: Optional[float] = None
    volume: Optional[float] = None
    character_id: Optional[str] = None