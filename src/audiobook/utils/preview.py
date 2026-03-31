"""Preview player for voice audition and comparison.

This module provides functionality for users to preview voice selections
before confirming them for the full conversion.

Core components:
- PreviewPlayer: Generate and play voice previews
- VoiceComparison: Compare multiple voice options
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PreviewRequest:
    """Request for generating a voice preview.

    Attributes:
        voice_id: ID of the voice to preview.
        text: Text to synthesize for preview.
        emotion: Optional emotion type for synthesis.
        emotion_intensity: Optional emotion intensity.
    """

    voice_id: str
    text: str
    emotion: Optional[str] = None
    emotion_intensity: Optional[str] = None


@dataclass
class PreviewResult:
    """Result of a preview generation.

    Attributes:
        voice_id: ID of the voice used.
        audio_data: Generated audio bytes.
        duration: Duration of the audio in seconds.
        audio_url: URL to access the audio (for web interface).
        format: Audio format (wav, mp3, etc.).
    """

    voice_id: str
    audio_data: bytes = b""
    duration: float = 0.0
    audio_url: Optional[str] = None
    format: str = "wav"


@dataclass
class VoiceCandidate:
    """A voice candidate with preview capability.

    Attributes:
        voice_id: ID of the voice.
        name: Human-readable name.
        match_score: How well it matches the character (0-100).
        match_reasons: Reasons for the match score.
        preview: Generated preview result.
    """

    voice_id: str
    name: str = ""
    match_score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)
    preview: Optional[PreviewResult] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "voice_id": self.voice_id,
            "name": self.name,
            "match_score": self.match_score,
            "match_reasons": self.match_reasons,
            "preview_url": self.preview.audio_url if self.preview else None,
            "duration": self.preview.duration if self.preview else 0,
        }


@dataclass
class ComparisonResult:
    """Result of comparing multiple voices.

    Attributes:
        candidates: List of voice candidates with previews.
        recommended: ID of the recommended voice.
        sample_text: Text used for previews.
    """

    candidates: list[VoiceCandidate] = field(default_factory=list)
    recommended: Optional[str] = None
    sample_text: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "candidates": [c.to_dict() for c in self.candidates],
            "recommended": self.recommended,
            "sample_text": self.sample_text,
        }


class PreviewPlayer:
    """Generates and manages voice previews for user selection.

    Allows users to audition different voices before confirming
    voice assignments for characters.

    Example usage:
        player = PreviewPlayer(tts_endpoint="http://localhost:9880")
        preview = player.generate_preview(voice_id, text, emotion)
        comparison = player.generate_comparison(voices, text)
    """

    # Default preview text templates
    PREVIEW_TEMPLATES = {
        "default": "你好，我是{character}，很高兴认识你。",
        "angry": "你怎么能这样做？我真的很生气！",
        "sad": "我感到非常难过，心里很沉重。",
        "happy": "太好了！这真是太棒了！",
        "calm": "平静下来，让我们好好谈谈。",
        "narration": "这是一个阳光明媚的早晨，空气中弥漫着花香。",
    }

    def __init__(
        self,
        tts_endpoint: Optional[str] = None,
        cache_dir: Optional[str] = None,
    ) -> None:
        """Initialize the preview player.

        Args:
            tts_endpoint: URL of the TTS service.
            cache_dir: Directory to cache preview audio files.
        """
        self.tts_endpoint = tts_endpoint
        self.cache_dir = cache_dir
        self._previews: dict[str, PreviewResult] = {}

    def generate_preview(
        self,
        voice_id: str,
        text: str,
        emotion: Optional[str] = None,
        emotion_intensity: Optional[str] = None,
    ) -> PreviewResult:
        """Generate a preview for a single voice.

        Args:
            voice_id: ID of the voice to preview.
            text: Text to synthesize.
            emotion: Optional emotion type.
            emotion_intensity: Optional emotion intensity.

        Returns:
            PreviewResult with audio data.
        """
        # Check cache first
        cache_key = f"{voice_id}_{hash(text)}_{emotion}"
        if cache_key in self._previews:
            return self._previews[cache_key]

        # For MVP, return a placeholder
        # In production, would call the TTS endpoint
        preview = PreviewResult(
            voice_id=voice_id,
            audio_data=b"placeholder_audio",
            duration=len(text) * 0.1,  # Rough estimate
            audio_url=f"/api/preview/{voice_id}/audio",
            format="wav",
        )

        # Cache the result
        self._previews[cache_key] = preview
        return preview

    def generate_comparison(
        self,
        voices: list[dict],
        text: str,
        emotion: Optional[str] = None,
    ) -> ComparisonResult:
        """Generate previews for multiple voices for comparison.

        Args:
            voices: List of voice dictionaries with 'voice_id', 'name', etc.
            text: Text to synthesize for all voices.
            emotion: Optional emotion type.

        Returns:
            ComparisonResult with all previews.
        """
        candidates = []

        for voice in voices:
            voice_id = voice.get("voice_id", voice.get("id", ""))
            name = voice.get("name", voice_id)
            match_score = voice.get("match_score", 0)
            match_reasons = voice.get("match_reasons", [])

            # Generate preview
            preview = self.generate_preview(
                voice_id=voice_id,
                text=text,
                emotion=emotion,
            )

            candidate = VoiceCandidate(
                voice_id=voice_id,
                name=name,
                match_score=match_score,
                match_reasons=match_reasons,
                preview=preview,
            )
            candidates.append(candidate)

        # Determine recommended voice (highest match score)
        recommended = None
        if candidates:
            best = max(candidates, key=lambda c: c.match_score)
            recommended = best.voice_id

        return ComparisonResult(
            candidates=candidates,
            recommended=recommended,
            sample_text=text,
        )

    def get_preview_text(
        self,
        character_name: str = "",
        emotion: Optional[str] = None,
        custom_text: Optional[str] = None,
    ) -> str:
        """Get appropriate preview text for a character.

        Args:
            character_name: Name of the character.
            emotion: Optional emotion type.
            custom_text: Optional custom text to use.

        Returns:
            Preview text string.
        """
        if custom_text:
            return custom_text

        # Select template based on emotion
        template_key = emotion.lower() if emotion else "default"
        template = self.PREVIEW_TEMPLATES.get(template_key, self.PREVIEW_TEMPLATES["default"])

        # Format with character name if applicable
        if "{character}" in template and character_name:
            return template.format(character=character_name)

        return template

    def clear_cache(self) -> None:
        """Clear the preview cache."""
        self._previews.clear()


# Sample voice data for testing
SAMPLE_VOICES = [
    {
        "voice_id": "voice_001",
        "name": "青年男声-温和",
        "gender": "男",
        "age_range": "青年",
        "match_score": 92,
        "match_reasons": ["声音温润", "适合沉稳内敛的角色"],
    },
    {
        "voice_id": "voice_002",
        "name": "青年男声-激昂",
        "gender": "男",
        "age_range": "青年",
        "match_score": 78,
        "match_reasons": ["声音有力", "适合性格外露的角色"],
    },
    {
        "voice_id": "voice_003",
        "name": "青年女声-温柔",
        "gender": "女",
        "age_range": "青年",
        "match_score": 85,
        "match_reasons": ["声音柔和", "适合善良温柔的角色"],
    },
]