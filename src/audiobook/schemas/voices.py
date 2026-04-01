"""Schema helpers for voice API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field

from audiobook.models import Voice


class VoiceResponse(BaseModel):
    """Serializable representation of a stored voice."""

    voice_id: str
    name: str
    gender: str
    age_range: str
    tags: list[str] = Field(default_factory=list)
    description: str = ""
    audio_path: str = ""

    @classmethod
    def from_voice(cls, voice: Voice) -> "VoiceResponse":
        """Convert a domain Voice model to an API schema."""
        return cls(
            voice_id=voice.voice_id,
            name=voice.name,
            gender=voice.gender,
            age_range=voice.age_range,
            tags=list(voice.tags),
            description=voice.description,
            audio_path=voice.audio_path,
        )
