"""Voice-related data models for audiobook TTS system."""

from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class VoiceParams:
    """Parameters for voice synthesis."""

    base_speed: float = 1.0
    base_pitch: str = "中性"
    feature_anchors: list[dict] = field(default_factory=list)


@dataclass
class Voice:
    """Represents a voice option for audiobook narration."""

    voice_id: str
    name: str
    gender: Literal["男", "女", "中性"]
    age_range: str
    tags: list[str] = field(default_factory=list)
    description: str = ""
    embedding: Optional[list[float]] = None
    audio_path: str = ""


@dataclass
class VoiceCandidate:
    """A candidate voice with matching confidence and reasons."""

    voice: Voice
    confidence: float = 0.0
    match_reasons: list[str] = field(default_factory=list)