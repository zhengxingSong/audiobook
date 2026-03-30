"""Unit tests for the character recognition engine."""

import pytest

from audiobook.models import (
    Block,
    Character,
    CharacterImportance,
    CharacterState,
    Dialogue,
    Emotion,
    EmotionIntensity,
    EmotionProfile,
    Position,
)
from audiobook.engines.character import CharacterRecognitionEngine, CharacterResult


@pytest.fixture
def engine() -> CharacterRecognitionEngine:
    """Create a fresh engine instance for each test."""
    return CharacterRecognitionEngine()


@pytest.fixture
def sample_block() -> Block:
    """Create a sample text block for testing."""
    return Block(
        block_id="block_001",
        chapter=1,
        position=Position(start=0, end=100),
        text='"你好啊，"李明笑着说道，"好久不见了。"\n张华点了点头，眼中满是喜悦。',
        dialogues=[
            Dialogue(speaker="李明", content="你好啊，", emotion_hint="喜悦"),
            Dialogue(speaker="张华", content="好久不见了。", emotion_hint=None),
        ],
    )


@pytest.fixture
def emotional_block() -> Block:
    """Create a block with emotional content."""
    return Block(
        block_id="block_002",
        chapter=1,
        position=Position(start=100, end=200),
        text='王刚暴怒地吼道："你竟然背叛了我！"\n小红听到这话，泪水夺眶而出，心中充满悲伤。',
        dialogues=[
            Dialogue(speaker="王刚", content="你竟然背叛了我！", emotion_hint="愤怒"),
        ],
    )


class TestCharacterResult:
    """Tests for CharacterResult dataclass."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        result = CharacterResult()
        assert result.characters == []
        assert result.new_characters == []
        assert result.confidence == 1.0

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        result = CharacterResult(
            characters=["Alice", "Bob"],
            new_characters=["Bob"],
            confidence=0.9,
        )
        assert result.characters == ["Alice", "Bob"]
        assert result.new_characters == ["Bob"]
        assert result.confidence == 0.9


class TestCharacterRecognitionEngine:
    """Tests for CharacterRecognitionEngine class."""

    def test_engine_initialization(self, engine: CharacterRecognitionEngine) -> None:
        """Test engine initializes with empty state."""
        assert engine._known_characters == set()
        assert engine._character_counts == {}

    def test_identify_characters_basic(
        self,
        engine: CharacterRecognitionEngine,
        sample_block: Block
    ) -> None:
        """Test basic character identification."""
        result = engine.identify_characters(sample_block)

        # Should find characters from dialogues
        assert "李明" in result.characters
        assert "张华" in result.characters

        # Both should be new characters
        assert "李明" in result.new_characters
        assert "张华" in result.new_characters

    def test_identify_characters_with_known(
        self,
        engine: CharacterRecognitionEngine,
        sample_block: Block
    ) -> None:
        """Test identification with pre-known characters."""
        known = ["李明"]
        result = engine.identify_characters(sample_block, known_characters=known)

        # 李明 should not be in new_characters since it's already known
        assert "李明" in result.characters
        assert "李明" not in result.new_characters

        # 张华 should still be new
        assert "张华" in result.new_characters

    def test_identify_characters_updates_internal_state(
        self,
        engine: CharacterRecognitionEngine,
        sample_block: Block
    ) -> None:
        """Test that identification updates internal character tracking."""
        engine.identify_characters(sample_block)

        assert "李明" in engine._known_characters
        assert "张华" in engine._known_characters

        # Check counts
        assert engine._character_counts.get("李明", 0) >= 1
        assert engine._character_counts.get("张华", 0) >= 1

    def test_identify_characters_from_dialogues(
        self,
        engine: CharacterRecognitionEngine,
        sample_block: Block
    ) -> None:
        """Test that speakers from dialogue objects are identified."""
        result = engine.identify_characters(sample_block)

        # Dialogues have explicit speakers
        assert "李明" in result.characters
        assert "张华" in result.characters

    def test_identify_characters_confidence(
        self,
        engine: CharacterRecognitionEngine,
        sample_block: Block
    ) -> None:
        """Test confidence score is calculated."""
        result = engine.identify_characters(sample_block)
        assert 0.0 <= result.confidence <= 1.0

    def test_identify_characters_empty_block(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test identification with empty block."""
        empty_block = Block(
            block_id="empty",
            chapter=1,
            position=Position(start=0, end=0),
            text="",
            dialogues=[],
        )
        result = engine.identify_characters(empty_block)

        assert result.characters == []
        assert result.new_characters == []

    def test_is_valid_name(self, engine: CharacterRecognitionEngine) -> None:
        """Test valid name detection."""
        # Valid Chinese names
        assert engine._is_valid_name("李明") is True
        assert engine._is_valid_name("张华") is True
        assert engine._is_valid_name("王刚") is True

        # Invalid names
        assert engine._is_valid_name("他") is False
        assert engine._is_valid_name("她") is False
        assert engine._is_valid_name("什么") is False
        assert engine._is_valid_name("") is False
        assert engine._is_valid_name("说道") is False

    def test_reset(self, engine: CharacterRecognitionEngine) -> None:
        """Test engine state reset."""
        # Add some state
        engine._known_characters.add("李明")
        engine._character_counts["李明"] = 5

        # Reset
        engine.reset()

        assert engine._known_characters == set()
        assert engine._character_counts == {}


class TestEmotionAnalysis:
    """Tests for emotion analysis functionality."""

    def test_analyze_emotion_joy(self, engine: CharacterRecognitionEngine) -> None:
        """Test joy emotion detection."""
        text = "她高兴地笑了起来，心中充满喜悦"
        profile = engine.analyze_emotion(text)

        assert profile.emotion_type == Emotion.HAPPY.value

    def test_analyze_emotion_anger(self, engine: CharacterRecognitionEngine) -> None:
        """Test anger emotion detection."""
        text = "他愤怒地瞪着对方，怒火中烧"
        profile = engine.analyze_emotion(text)

        assert profile.emotion_type == Emotion.ANGRY.value

    def test_analyze_emotion_sadness(self, engine: CharacterRecognitionEngine) -> None:
        """Test sadness emotion detection."""
        text = "她悲伤地哭泣，泪水不断流下"
        profile = engine.analyze_emotion(text)

        assert profile.emotion_type == Emotion.SAD.value

    def test_analyze_emotion_fear(self, engine: CharacterRecognitionEngine) -> None:
        """Test fear emotion detection."""
        text = "他感到恐惧，浑身颤抖"
        profile = engine.analyze_emotion(text)

        assert profile.emotion_type == Emotion.FEARFUL.value

    def test_analyze_emotion_surprise(self, engine: CharacterRecognitionEngine) -> None:
        """Test surprise emotion detection."""
        text = "她惊讶地睁大了眼睛，完全出乎意料"
        profile = engine.analyze_emotion(text)

        assert profile.emotion_type == Emotion.SURPRISED.value

    def test_analyze_emotion_calm(self, engine: CharacterRecognitionEngine) -> None:
        """Test calm emotion detection for neutral text."""
        text = "他平静地坐在那里"
        profile = engine.analyze_emotion(text)

        assert profile.emotion_type == Emotion.CALM.value

    def test_analyze_emotion_with_character(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test emotion analysis with character context."""
        text = "她开心地笑了"
        profile = engine.analyze_emotion(text, character="小红")

        assert "小红" in profile.scene_context
        assert Emotion.HAPPY.value == profile.emotion_type

    def test_analyze_emotion_with_context(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test emotion analysis with additional context."""
        text = "他愤怒地拍桌子"
        context = {"scene": "office_argument"}
        profile = engine.analyze_emotion(text, character="张三", context=context)

        assert "张三" in profile.scene_context
        assert "office_argument" in profile.scene_context

    def test_analyze_emotion_intensity_extreme(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test strong intensity detection."""
        text = "他暴怒地狂吼，完全失控"
        profile = engine.analyze_emotion(text)

        assert profile.intensity == EmotionIntensity.STRONG

    def test_analyze_emotion_intensity_high(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test strong intensity detection."""
        text = "他非常愤怒地大喊"
        profile = engine.analyze_emotion(text)

        assert profile.intensity == EmotionIntensity.STRONG

    def test_analyze_emotion_intensity_low(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test light intensity detection."""
        text = "她微微有些开心"
        profile = engine.analyze_emotion(text)

        assert profile.intensity == EmotionIntensity.LIGHT

    def test_generate_adjustment_anger(self, engine: CharacterRecognitionEngine) -> None:
        """Test voice adjustment generation for anger."""
        adjustment = engine._generate_adjustment("愤怒", EmotionIntensity.STRONG)
        assert "loud" in adjustment.lower() or "harsh" in adjustment.lower()

    def test_generate_adjustment_sadness(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test voice adjustment generation for sadness."""
        adjustment = engine._generate_adjustment("悲伤", EmotionIntensity.MODERATE)
        assert "slow" in adjustment.lower() or "soft" in adjustment.lower()


class TestImportanceClassification:
    """Tests for character importance classification."""

    def test_classify_importance_empty(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test classification with empty input."""
        result = engine.classify_importance({})
        assert result == {}

    def test_classify_importance_single_character(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test classification with single character."""
        result = engine.classify_importance({"张三": 10})
        assert result["张三"] == CharacterImportance.PROTAGONIST

    def test_classify_importance_multiple_characters(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test classification with multiple characters."""
        counts = {
            "主角": 100,  # Most frequent - should be PROTAGONIST
            "配角A": 50,
            "配角B": 45,
            "配角C": 40,
            "路人甲": 5,
            "路人乙": 3,
            "路人丙": 2,
            "路人丁": 1,
        }
        result = engine.classify_importance(counts)

        # Most frequent should be protagonist
        assert result["主角"] == CharacterImportance.PROTAGONIST

        # Less frequent characters should be lower importance
        # Note: actual classification depends on position and frequency ratio

    def test_classify_importance_distribution(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test that importance distribution follows expected pattern."""
        # Create 10 characters with varying frequencies
        counts = {f"角色{i}": 100 - i * 10 for i in range(10)}
        result = engine.classify_importance(counts)

        # All characters should have an importance level
        assert len(result) == 10

        # Check that all importance values are valid enum members
        for importance in result.values():
            assert importance in CharacterImportance


class TestCharacterStateUpdate:
    """Tests for character state update functionality."""

    def test_update_character_state_new_state(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test updating character without existing state."""
        character = Character(
            character_id="char_001",
            name="张三",
        )
        emotion = EmotionProfile(
            emotion_type=Emotion.HAPPY.value,
            intensity=EmotionIntensity.MODERATE,
        )

        updated = engine.update_character_state(character, emotion, "met an old friend")

        assert updated.state is not None
        assert updated.state.character_id == "char_001"
        assert updated.state.current_emotion == emotion
        assert updated.emotion == emotion
        assert "met an old friend" in updated.state.history_summary

    def test_update_character_state_existing_state(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test updating character with existing state."""
        character = Character(
            character_id="char_001",
            name="李四",
            state=CharacterState(
                character_id="char_001",
                current_emotion=Emotion.CALM,
                history_summary="previous event",
            ),
        )
        emotion = EmotionProfile(
            emotion_type=Emotion.SAD.value,
            intensity=EmotionIntensity.STRONG,
        )

        updated = engine.update_character_state(character, emotion, "lost something")

        assert updated.state is not None
        assert updated.state.current_emotion == emotion
        assert "previous event" in updated.state.history_summary
        assert "lost something" in updated.state.history_summary

    def test_update_character_state_consistency_decrease(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test that consistency score decreases with state changes."""
        character = Character(
            character_id="char_001",
            name="王五",
            state=CharacterState(
                character_id="char_001",
                current_emotion=Emotion.CALM,
                consistency_score=1.0,
            ),
        )
        emotion = EmotionProfile(
            emotion_type=Emotion.ANGRY.value,
            intensity=EmotionIntensity.STRONG,
        )

        updated = engine.update_character_state(character, emotion, "got upset")

        assert updated.state.consistency_score < 1.0
        assert updated.state.consistency_score >= 0.5

    def test_update_character_state_consistency_floor(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test that consistency score has a minimum floor."""
        character = Character(
            character_id="char_001",
            name="赵六",
            state=CharacterState(
                character_id="char_001",
                current_emotion=Emotion.CALM,
                consistency_score=0.51,  # Near the floor
            ),
        )
        emotion = EmotionProfile(
            emotion_type=Emotion.ANGRY.value,
            intensity=EmotionIntensity.STRONG,
        )

        updated = engine.update_character_state(character, emotion, "another event")

        # Should not go below 0.5
        assert updated.state.consistency_score >= 0.5


class TestIntensityDetection:
    """Tests for emotion intensity detection."""

    def test_detect_intensity_extreme(self, engine: CharacterRecognitionEngine) -> None:
        """Test strong intensity detection."""
        intensity = engine._detect_intensity(["暴怒", "狂怒"])
        assert intensity == EmotionIntensity.STRONG

    def test_detect_intensity_high(self, engine: CharacterRecognitionEngine) -> None:
        """Test strong intensity detection."""
        intensity = engine._detect_intensity(["愤怒"])
        assert intensity == EmotionIntensity.STRONG

    def test_detect_intensity_low(self, engine: CharacterRecognitionEngine) -> None:
        """Test light intensity detection."""
        intensity = engine._detect_intensity(["微微"])
        assert intensity == EmotionIntensity.LIGHT

    def test_detect_intensity_default(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test default intensity for unknown keywords."""
        intensity = engine._detect_intensity(["unknown_keyword"])
        assert intensity == EmotionIntensity.LIGHT

    def test_detect_intensity_empty(self, engine: CharacterRecognitionEngine) -> None:
        """Test intensity detection with empty list."""
        intensity = engine._detect_intensity([])
        assert intensity == EmotionIntensity.LIGHT


class TestEmotionKeywords:
    """Tests for emotion keyword coverage."""

    def test_emotion_keywords_defined(self, engine: CharacterRecognitionEngine) -> None:
        """Test that all emotion types have keywords defined."""
        assert len(engine.EMOTION_KEYWORDS) > 0

        # Check that each emotion type has associated keywords
        for emotion_type, keywords in engine.EMOTION_KEYWORDS.items():
            assert isinstance(emotion_type, str)
            assert isinstance(keywords, list)
            assert len(keywords) > 0

    def test_intensity_modifiers_defined(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test that intensity modifiers are defined."""
        assert "strong" in engine.INTENSITY_MODIFIERS
        assert "moderate" in engine.INTENSITY_MODIFIERS
        assert "light" in engine.INTENSITY_MODIFIERS


class TestInvalidNames:
    """Tests for invalid name filtering."""

    def test_invalid_names_defined(self, engine: CharacterRecognitionEngine) -> None:
        """Test that invalid names set is populated."""
        assert len(engine.INVALID_NAMES) > 0

        # Should contain common pronouns
        assert "他" in engine.INVALID_NAMES
        assert "她" in engine.INVALID_NAMES
        assert "我" in engine.INVALID_NAMES

    def test_filtering_invalid_names(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test that invalid names are filtered out."""
        # All invalid names should fail validation
        for name in engine.INVALID_NAMES:
            assert engine._is_valid_name(name) is False

    def test_name_length_validation(
        self,
        engine: CharacterRecognitionEngine
    ) -> None:
        """Test that name length is validated."""
        # Too short
        assert engine._is_valid_name("") is False

        # Too long
        assert engine._is_valid_name("这是一个很长的名字不应该被接受") is False

        # Valid lengths
        assert engine._is_valid_name("李") is True
        assert engine._is_valid_name("李明") is True
        assert engine._is_valid_name("欧阳修竹") is True


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow(
        self,
        engine: CharacterRecognitionEngine,
        sample_block: Block
    ) -> None:
        """Test complete workflow: identify -> analyze -> classify."""
        # Step 1: Identify characters
        result = engine.identify_characters(sample_block)
        assert len(result.characters) > 0

        # Step 2: Analyze emotion for first character
        first_char = result.characters[0]
        emotion = engine.analyze_emotion(sample_block.text, character=first_char)
        assert emotion is not None

        # Step 3: Classify importance
        importance = engine.classify_importance(engine._character_counts)
        assert len(importance) > 0

    def test_multiple_blocks_workflow(
        self,
        engine: CharacterRecognitionEngine,
        sample_block: Block,
        emotional_block: Block
    ) -> None:
        """Test workflow with multiple blocks."""
        # Process first block
        result1 = engine.identify_characters(sample_block)

        # Process second block
        result2 = engine.identify_characters(emotional_block)

        # Characters should accumulate
        all_characters = engine._known_characters
        assert len(all_characters) >= 4  # At least 4 unique characters

        # Analyze emotion for emotional block
        emotion = engine.analyze_emotion(emotional_block.text)
        assert emotion.emotion_type == Emotion.ANGRY.value