"""Tests for base enums and types."""

import pytest

from audiobook.models.base import (
    BlockType,
    CharacterImportance,
    EmotionIntensity,
    FragmentStatus,
)


class TestBlockType:
    """Tests for BlockType enum."""

    def test_block_type_values(self) -> None:
        """Test BlockType has correct values."""
        assert BlockType.DIALOGUE.value == "dialogue"
        assert BlockType.NARRATION.value == "narration"
        assert BlockType.DESCRIPTION.value == "description"

    def test_block_type_members(self) -> None:
        """Test BlockType has all expected members."""
        members = [m.value for m in BlockType]
        assert "dialogue" in members
        assert "narration" in members
        assert "description" in members


class TestEmotionIntensity:
    """Tests for EmotionIntensity enum."""

    def test_emotion_intensity_values(self) -> None:
        """Test EmotionIntensity has correct Chinese values."""
        assert EmotionIntensity.LIGHT.value == "轻度"
        assert EmotionIntensity.MODERATE.value == "中度"
        assert EmotionIntensity.STRONG.value == "强烈"

    def test_emotion_intensity_ordering_light_less_than_moderate(self) -> None:
        """Test LIGHT < MODERATE."""
        assert EmotionIntensity.LIGHT < EmotionIntensity.MODERATE

    def test_emotion_intensity_ordering_moderate_less_than_strong(self) -> None:
        """Test MODERATE < STRONG."""
        assert EmotionIntensity.MODERATE < EmotionIntensity.STRONG

    def test_emotion_intensity_ordering_light_less_than_strong(self) -> None:
        """Test LIGHT < STRONG."""
        assert EmotionIntensity.LIGHT < EmotionIntensity.STRONG

    def test_emotion_intensity_ordering_not_less_than_self(self) -> None:
        """Test an intensity is not less than itself."""
        assert not (EmotionIntensity.LIGHT < EmotionIntensity.LIGHT)

    def test_emotion_intensity_ordering_strong_not_less_than_light(self) -> None:
        """Test STRONG is not less than LIGHT."""
        assert not (EmotionIntensity.STRONG < EmotionIntensity.LIGHT)


class TestCharacterImportance:
    """Tests for CharacterImportance enum."""

    def test_character_importance_values(self) -> None:
        """Test CharacterImportance has correct Chinese values."""
        assert CharacterImportance.PROTAGONIST.value == "主角"
        assert CharacterImportance.SUPPORTING.value == "配角"
        assert CharacterImportance.MINOR.value == "次要"

    def test_character_importance_members(self) -> None:
        """Test CharacterImportance has all expected members."""
        members = [m.value for m in CharacterImportance]
        assert "主角" in members
        assert "配角" in members
        assert "次要" in members


class TestFragmentStatus:
    """Tests for FragmentStatus enum."""

    def test_fragment_status_values(self) -> None:
        """Test FragmentStatus has correct values."""
        assert FragmentStatus.PENDING.value == "pending"
        assert FragmentStatus.PROCESSING.value == "processing"
        assert FragmentStatus.COMPLETED.value == "completed"
        assert FragmentStatus.FAILED.value == "failed"

    def test_fragment_status_members(self) -> None:
        """Test FragmentStatus has all expected members."""
        members = [m.value for m in FragmentStatus]
        assert "pending" in members
        assert "processing" in members
        assert "completed" in members
        assert "failed" in members


class TestModelImports:
    """Tests for model imports from package."""

    def test_import_from_base(self) -> None:
        """Test imports directly from base module."""
        from audiobook.models.base import BlockType

        assert BlockType.DIALOGUE.value == "dialogue"

    def test_import_from_package(self) -> None:
        """Test imports from models package."""
        from audiobook.models import (
            BlockType,
            CharacterImportance,
            EmotionIntensity,
            FragmentStatus,
        )

        assert BlockType.DIALOGUE.value == "dialogue"
        assert EmotionIntensity.LIGHT.value == "轻度"
        assert CharacterImportance.PROTAGONIST.value == "主角"
        assert FragmentStatus.PENDING.value == "pending"