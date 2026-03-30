"""Character-related data models for audiobook TTS system.

This module defines the core data structures for representing characters,
their emotional states, and tracking character state throughout the narrative.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union

from audiobook.models.base import CharacterImportance, EmotionIntensity


class EmotionType(Enum):
    """Emotion types for character voice expression.

    Simple enumeration of emotion categories for basic voice synthesis.
    """

    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    EXCITED = "excited"
    CALM = "calm"
    NERVOUS = "nervous"


# Backward compatibility alias
Emotion = EmotionType


@dataclass
class EmotionProfile:
    """Represents a detailed emotional state for a character.

    Captures the emotion type, intensity, and contextual information
    that affects voice synthesis parameters.

    Attributes:
        emotion_type: The type of emotion (e.g., 'happy', 'sad', 'angry').
        intensity: The intensity level of the emotion.
        components: List of emotion components or nuances.
        scene_context: Contextual information about the scene.
        suggested_adjustment: Suggested voice adjustment for synthesis.
    """

    emotion_type: str
    intensity: EmotionIntensity = EmotionIntensity.LIGHT
    components: list[str] = field(default_factory=list)
    scene_context: str = ""
    suggested_adjustment: str = ""


@dataclass
class CharacterState:
    """Represents the current state of a character in the narrative.

    Tracks the character's emotional state, relationships, and narrative
    history to maintain consistency throughout the audiobook.

    Attributes:
        character_id: Unique identifier for the character.
        current_emotion: The character's current emotional state (enum or profile).
        current_location: Current location in the narrative.
        active: Whether the character is currently active in the scene.
        key_relations: List of key relationship identifiers.
        history_summary: Summary of the character's narrative history.
        consistency_score: Score indicating character consistency (0.0 to 1.0).
    """

    character_id: str
    current_emotion: Union[EmotionType, EmotionProfile] = EmotionType.NEUTRAL
    current_location: str = ""
    active: bool = True
    key_relations: list[str] = field(default_factory=list)
    history_summary: str = ""
    consistency_score: float = 1.0


@dataclass
class Character:
    """Represents a character in the audiobook.

    A character has a name, voice assignment, emotional state, importance level,
    relationships, and optional state tracking for narrative consistency.

    Attributes:
        character_id: Unique identifier for the character.
        name: The character's name.
        default_voice_id: Identifier for the assigned voice (TTS voice ID).
        default_emotion: Default emotion type for voice synthesis.
        traits: List of character personality traits.
        description: Character description.
        voice_id: Alternative voice ID field for compatibility.
        emotion: Detailed emotional profile for synthesis adjustment.
        importance: The importance level of the character.
        relationships: List of relationship descriptions or character IDs.
        state: Optional detailed state tracking for the character.
    """

    character_id: str
    name: str
    default_voice_id: Optional[str] = None
    default_emotion: EmotionType = EmotionType.NEUTRAL
    traits: list[str] = field(default_factory=list)
    description: str = ""
    # Extended fields for detailed character tracking
    voice_id: Optional[str] = None
    emotion: Optional[EmotionProfile] = None
    importance: CharacterImportance = CharacterImportance.SUPPORTING
    relationships: list[str] = field(default_factory=list)
    state: Optional[CharacterState] = None
