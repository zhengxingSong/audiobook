"""Base models and enums for audiobook TTS system."""

from enum import Enum


class FragmentStatus(Enum):
    """Status of an audio fragment in the processing pipeline."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BlockType(Enum):
    """Types of content blocks in the audiobook."""

    DIALOGUE = "dialogue"
    NARRATION = "narration"
    DESCRIPTION = "description"


class CharacterImportance(Enum):
    """Importance level of a character in the story."""

    PROTAGONIST = "主角"
    SUPPORTING = "配角"
    MINOR = "次要"


class EmotionIntensity(Enum):
    """Intensity levels for emotions."""

    LIGHT = "轻度"
    MODERATE = "中度"
    STRONG = "强烈"

    def __lt__(self, other: "EmotionIntensity") -> bool:
        """Enable comparison by intensity level."""
        order = [EmotionIntensity.LIGHT, EmotionIntensity.MODERATE, EmotionIntensity.STRONG]
        return order.index(self) < order.index(other)