"""Tests for character data models."""

import pytest

from audiobook.models.base import CharacterImportance, EmotionIntensity
from audiobook.models.character import (
    Character,
    CharacterState,
    Emotion,
    EmotionProfile,
    EmotionType,
)


class TestEmotionType:
    """Tests for the EmotionType enum."""

    def test_emotion_type_values(self) -> None:
        """Test that EmotionType has all expected values."""
        assert EmotionType.NEUTRAL.value == "neutral"
        assert EmotionType.HAPPY.value == "happy"
        assert EmotionType.SAD.value == "sad"
        assert EmotionType.ANGRY.value == "angry"
        assert EmotionType.FEARFUL.value == "fearful"
        assert EmotionType.SURPRISED.value == "surprised"
        assert EmotionType.DISGUSTED.value == "disgusted"
        assert EmotionType.EXCITED.value == "excited"
        assert EmotionType.CALM.value == "calm"
        assert EmotionType.NERVOUS.value == "nervous"

    def test_emotion_type_count(self) -> None:
        """Test that EmotionType has exactly 10 members."""
        assert len(EmotionType) == 10

    def test_emotion_backward_compatibility_alias(self) -> None:
        """Test that Emotion is an alias for EmotionType."""
        assert Emotion is EmotionType
        assert Emotion.NEUTRAL == EmotionType.NEUTRAL
        assert Emotion.HAPPY == EmotionType.HAPPY


class TestEmotionProfile:
    """Tests for the EmotionProfile dataclass."""

    def test_emotion_profile_creation_with_defaults(self) -> None:
        """Test creating an EmotionProfile with default values."""
        emotion = EmotionProfile(emotion_type="happy")

        assert emotion.emotion_type == "happy"
        assert emotion.intensity == EmotionIntensity.LIGHT
        assert emotion.components == []
        assert emotion.scene_context == ""
        assert emotion.suggested_adjustment == ""

    def test_emotion_profile_creation_with_all_fields(self) -> None:
        """Test creating an EmotionProfile with all fields specified."""
        emotion = EmotionProfile(
            emotion_type="sad",
            intensity=EmotionIntensity.STRONG,
            components=["melancholy", "grief"],
            scene_context="Character discovers loss",
            suggested_adjustment="slower pace, lower pitch",
        )

        assert emotion.emotion_type == "sad"
        assert emotion.intensity == EmotionIntensity.STRONG
        assert emotion.components == ["melancholy", "grief"]
        assert emotion.scene_context == "Character discovers loss"
        assert emotion.suggested_adjustment == "slower pace, lower pitch"

    def test_emotion_profile_with_moderate_intensity(self) -> None:
        """Test creating an EmotionProfile with moderate intensity."""
        emotion = EmotionProfile(
            emotion_type="angry",
            intensity=EmotionIntensity.MODERATE,
        )

        assert emotion.emotion_type == "angry"
        assert emotion.intensity == EmotionIntensity.MODERATE

    def test_emotion_profile_with_components(self) -> None:
        """Test creating an EmotionProfile with emotion components."""
        emotion = EmotionProfile(
            emotion_type="joyful",
            intensity=EmotionIntensity.STRONG,
            components=["excitement", "gratitude", "happiness"],
        )

        assert len(emotion.components) == 3
        assert "excitement" in emotion.components
        assert "gratitude" in emotion.components


class TestCharacterState:
    """Tests for the CharacterState dataclass."""

    def test_character_state_creation_with_defaults(self) -> None:
        """Test creating a CharacterState with default values."""
        state = CharacterState(character_id="char_001")

        assert state.character_id == "char_001"
        assert state.current_emotion == EmotionType.NEUTRAL
        assert state.current_location == ""
        assert state.active is True
        assert state.key_relations == []
        assert state.history_summary == ""
        assert state.consistency_score == 1.0

    def test_character_state_with_emotion_enum(self) -> None:
        """Test creating a CharacterState with an EmotionType enum."""
        state = CharacterState(
            character_id="char_002",
            current_emotion=EmotionType.ANGRY,
            current_location="battlefield",
            active=True,
        )

        assert state.character_id == "char_002"
        assert state.current_emotion == EmotionType.ANGRY
        assert state.current_location == "battlefield"
        assert state.active is True

    def test_character_state_with_emotion_profile(self) -> None:
        """Test creating a CharacterState with an EmotionProfile."""
        emotion_profile = EmotionProfile(
            emotion_type="nervous",
            intensity=EmotionIntensity.MODERATE,
        )
        state = CharacterState(
            character_id="char_003",
            current_emotion=emotion_profile,
            key_relations=["char_004", "char_006"],
            history_summary="Previously betrayed by allies",
            consistency_score=0.85,
        )

        assert state.character_id == "char_003"
        assert isinstance(state.current_emotion, EmotionProfile)
        assert state.current_emotion.emotion_type == "nervous"
        assert state.key_relations == ["char_004", "char_006"]
        assert state.history_summary == "Previously betrayed by allies"
        assert state.consistency_score == 0.85

    def test_character_state_consistency_score_range(self) -> None:
        """Test that consistency score can be set to valid values."""
        state_low = CharacterState(character_id="char_004", consistency_score=0.0)
        state_high = CharacterState(character_id="char_005", consistency_score=1.0)
        state_mid = CharacterState(character_id="char_006", consistency_score=0.5)

        assert state_low.consistency_score == 0.0
        assert state_high.consistency_score == 1.0
        assert state_mid.consistency_score == 0.5

    def test_character_state_inactive(self) -> None:
        """Test creating a CharacterState with inactive status."""
        state = CharacterState(
            character_id="char_007",
            active=False,
        )

        assert state.active is False


class TestCharacter:
    """Tests for the Character dataclass."""

    def test_character_creation_with_required_fields(self) -> None:
        """Test creating a Character with required fields only."""
        character = Character(character_id="char_001", name="John Doe")

        assert character.character_id == "char_001"
        assert character.name == "John Doe"
        assert character.default_voice_id is None
        assert character.default_emotion == EmotionType.NEUTRAL
        assert character.traits == []
        assert character.description == ""
        assert character.voice_id is None
        assert character.emotion is None
        assert character.importance == CharacterImportance.SUPPORTING
        assert character.relationships == []
        assert character.state is None

    def test_character_creation_with_all_fields(self) -> None:
        """Test creating a Character with all fields specified."""
        emotion_profile = EmotionProfile(
            emotion_type="confident",
            intensity=EmotionIntensity.MODERATE,
        )
        state = CharacterState(
            character_id="char_protagonist",
            current_emotion=emotion_profile,
            key_relations=["char_sidekick"],
        )
        character = Character(
            character_id="char_hero",
            name="Hero",
            default_voice_id="default_voice_01",
            default_emotion=EmotionType.HAPPY,
            traits=["brave", "kind"],
            description="The main protagonist",
            voice_id="voice_male_hero_01",
            emotion=emotion_profile,
            importance=CharacterImportance.PROTAGONIST,
            relationships=["sidekick", "mentor"],
            state=state,
        )

        assert character.character_id == "char_hero"
        assert character.name == "Hero"
        assert character.default_voice_id == "default_voice_01"
        assert character.default_emotion == EmotionType.HAPPY
        assert character.traits == ["brave", "kind"]
        assert character.description == "The main protagonist"
        assert character.voice_id == "voice_male_hero_01"
        assert character.emotion is not None
        assert character.emotion.emotion_type == "confident"
        assert character.importance == CharacterImportance.PROTAGONIST
        assert character.relationships == ["sidekick", "mentor"]
        assert character.state is not None
        assert character.state.character_id == "char_protagonist"

    def test_character_with_minor_importance(self) -> None:
        """Test creating a Character with minor importance."""
        character = Character(
            character_id="char_minor",
            name="Background NPC",
            importance=CharacterImportance.MINOR,
        )

        assert character.importance == CharacterImportance.MINOR

    def test_character_with_protagonist_importance(self) -> None:
        """Test creating a Character with protagonist importance."""
        character = Character(
            character_id="char_main",
            name="Main Hero",
            importance=CharacterImportance.PROTAGONIST,
        )

        assert character.importance == CharacterImportance.PROTAGONIST

    def test_character_with_voice_assignment(self) -> None:
        """Test creating a Character with voice IDs."""
        character = Character(
            character_id="char_voice",
            name="Narrator",
            default_voice_id="default-narrator-voice",
            voice_id="zh-CN-XiaoxiaoNeural",
        )

        assert character.default_voice_id == "default-narrator-voice"
        assert character.voice_id == "zh-CN-XiaoxiaoNeural"

    def test_character_with_traits(self) -> None:
        """Test creating a Character with personality traits."""
        character = Character(
            character_id="char_traits",
            name="Complex Character",
            traits=["intelligent", "stubborn", "loyal", "ambitious"],
        )

        assert len(character.traits) == 4
        assert "intelligent" in character.traits
        assert "stubborn" in character.traits

    def test_character_emotional_state_management(self) -> None:
        """Test managing a character's emotional state."""
        character = Character(
            character_id="char_emotional",
            name="Emotional Character",
        )

        # Initially no emotion profile
        assert character.emotion is None

        # Set an emotion profile
        character.emotion = EmotionProfile(
            emotion_type="joyful",
            intensity=EmotionIntensity.STRONG,
            components=["excitement", "gratitude"],
        )

        assert character.emotion is not None
        assert character.emotion.emotion_type == "joyful"
        assert character.emotion.intensity == EmotionIntensity.STRONG
        assert "excitement" in character.emotion.components

    def test_character_relationship_tracking(self) -> None:
        """Test tracking character relationships."""
        character = Character(
            character_id="char_relations",
            name="Main Character",
            relationships=["friend:char_002", "enemy:char_005", "family:char_010"],
        )

        assert len(character.relationships) == 3
        assert "friend:char_002" in character.relationships
        assert "enemy:char_005" in character.relationships

    def test_character_with_state_tracking(self) -> None:
        """Test character with full state tracking."""
        state = CharacterState(
            character_id="char_full",
            current_emotion=EmotionProfile(
                emotion_type="determined",
                intensity=EmotionIntensity.MODERATE,
            ),
            current_location="castle",
            active=True,
            key_relations=["ally_1", "enemy_2"],
            history_summary="A veteran warrior seeking peace",
            consistency_score=0.95,
        )
        character = Character(
            character_id="char_full",
            name="Veteran Warrior",
            state=state,
        )

        assert character.state is not None
        assert character.state.current_location == "castle"
        assert character.state.history_summary == "A veteran warrior seeking peace"
        assert character.state.consistency_score == 0.95


class TestEmotionIntensityOrdering:
    """Tests for EmotionIntensity ordering."""

    def test_intensity_ordering(self) -> None:
        """Test that intensity levels can be ordered."""
        assert EmotionIntensity.LIGHT < EmotionIntensity.MODERATE
        assert EmotionIntensity.MODERATE < EmotionIntensity.STRONG
        assert EmotionIntensity.LIGHT < EmotionIntensity.STRONG

    def test_intensity_not_less_than_self(self) -> None:
        """Test that an intensity is not less than itself."""
        assert not (EmotionIntensity.LIGHT < EmotionIntensity.LIGHT)
        assert not (EmotionIntensity.MODERATE < EmotionIntensity.MODERATE)


class TestCharacterImportanceValues:
    """Tests for CharacterImportance enum values."""

    def test_protagonist_value(self) -> None:
        """Test protagonist importance value."""
        assert CharacterImportance.PROTAGONIST.value == "主角"

    def test_supporting_value(self) -> None:
        """Test supporting importance value."""
        assert CharacterImportance.SUPPORTING.value == "配角"

    def test_minor_value(self) -> None:
        """Test minor importance value."""
        assert CharacterImportance.MINOR.value == "次要"

    def test_character_importance_count(self) -> None:
        """Test that CharacterImportance has exactly 3 members."""
        assert len(CharacterImportance) == 3