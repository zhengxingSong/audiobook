"""Unit tests for novel data models."""

import pytest

from audiobook.models.base import BlockType
from audiobook.models.novel import Block, Dialogue, Novel, ParseResult, Position


class TestPosition:
    """Tests for Position dataclass."""

    def test_position_creation(self):
        """Test creating a valid Position."""
        pos = Position(start=0, end=100)
        assert pos.start == 0
        assert pos.end == 100

    def test_position_negative_start_raises_error(self):
        """Test that negative start raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Position(start=-1, end=10)

    def test_position_end_less_than_start_raises_error(self):
        """Test that end < start raises ValueError."""
        with pytest.raises(ValueError, match="cannot be less than start"):
            Position(start=100, end=50)

    def test_position_equal_start_end(self):
        """Test that equal start and end is valid."""
        pos = Position(start=50, end=50)
        assert pos.start == 50
        assert pos.end == 50


class TestDialogue:
    """Tests for Dialogue dataclass."""

    def test_dialogue_creation_with_required_fields(self):
        """Test creating Dialogue with required fields only."""
        dialogue = Dialogue(speaker="张三", content="你好，世界！")
        assert dialogue.speaker == "张三"
        assert dialogue.content == "你好，世界！"
        assert dialogue.emotion_hint is None

    def test_dialogue_creation_with_emotion_hint(self):
        """Test creating Dialogue with emotion hint."""
        dialogue = Dialogue(
            speaker="李四", content="我很高兴！", emotion_hint="高兴"
        )
        assert dialogue.speaker == "李四"
        assert dialogue.content == "我很高兴！"
        assert dialogue.emotion_hint == "高兴"


class TestBlock:
    """Tests for Block dataclass."""

    def test_block_creation_minimal(self):
        """Test creating Block with minimal required fields."""
        block = Block(
            block_id="block-001",
            chapter=1,
            position=Position(start=0, end=100),
            text="这是一段叙述文本。",
        )
        assert block.block_id == "block-001"
        assert block.chapter == 1
        assert block.type == BlockType.NARRATION
        assert len(block.dialogues) == 0

    def test_block_creation_with_dialogue_type(self):
        """Test creating Block with DIALOGUE type."""
        block = Block(
            block_id="block-002",
            chapter=1,
            position=Position(start=100, end=200),
            text='Zhang San said: "Hello!"',
            type=BlockType.DIALOGUE,
        )
        assert block.type == BlockType.DIALOGUE

    def test_block_creation_with_dialogues(self):
        """Test creating Block with Dialogue objects."""
        dialogues = [
            Dialogue(speaker="张三", content="你好！"),
            Dialogue(speaker="李四", content="你好，张三！"),
        ]
        block = Block(
            block_id="block-003",
            chapter=2,
            position=Position(start=0, end=50),
            text="张三和李四打招呼。",
            dialogues=dialogues,
        )
        assert len(block.dialogues) == 2
        assert block.dialogues[0].speaker == "张三"

    def test_block_position_dict_conversion(self):
        """Test that Block converts position dict to Position object."""
        block = Block(
            block_id="block-004",
            chapter=1,
            position={"start": 0, "end": 100},
            text="测试文本",
        )
        assert isinstance(block.position, Position)
        assert block.position.start == 0
        assert block.position.end == 100


class TestNovel:
    """Tests for Novel dataclass."""

    def test_novel_creation_minimal(self):
        """Test creating Novel with minimal required fields."""
        novel = Novel(
            novel_id="novel-001",
            title="测试小说",
            file_path="/path/to/novel.txt",
        )
        assert novel.novel_id == "novel-001"
        assert novel.title == "测试小说"
        assert novel.file_path == "/path/to/novel.txt"
        assert novel.encoding == "utf-8"
        assert len(novel.blocks) == 0
        assert len(novel.characters) == 0

    def test_novel_creation_with_blocks_and_characters(self):
        """Test creating Novel with blocks and characters."""
        blocks = [
            Block(
                block_id="block-001",
                chapter=1,
                position=Position(start=0, end=100),
                text="第一章开头。",
            )
        ]
        novel = Novel(
            novel_id="novel-002",
            title="完整小说",
            file_path="/path/to/novel.txt",
            encoding="gbk",
            blocks=blocks,
            characters=["张三", "李四"],
        )
        assert len(novel.blocks) == 1
        assert len(novel.characters) == 2
        assert novel.encoding == "gbk"


class TestParseResult:
    """Tests for ParseResult dataclass."""

    def test_parse_result_creation(self):
        """Test creating ParseResult."""
        result = ParseResult(
            novel_id="novel-001",
            title="测试小说",
            total_chapters=10,
            total_characters=5,
            character_names=["张三", "李四", "王五"],
            encoding="utf-8",
        )
        assert result.novel_id == "novel-001"
        assert result.title == "测试小说"
        assert result.total_chapters == 10
        assert result.total_characters == 5
        assert len(result.character_names) == 3
        assert len(result.blocks) == 0

    def test_parse_result_with_blocks(self):
        """Test creating ParseResult with blocks."""
        blocks = [
            Block(
                block_id="block-001",
                chapter=1,
                position=Position(start=0, end=100),
                text="测试文本",
            )
        ]
        result = ParseResult(
            novel_id="novel-002",
            title="测试小说2",
            total_chapters=5,
            total_characters=2,
            character_names=["主角", "配角"],
            encoding="utf-8",
            blocks=blocks,
        )
        assert len(result.blocks) == 1


class TestBlockType:
    """Tests for BlockType enum."""

    def test_block_type_values(self):
        """Test BlockType enum values."""
        assert BlockType.DIALOGUE.value == "dialogue"
        assert BlockType.NARRATION.value == "narration"
        assert BlockType.DESCRIPTION.value == "description"

    def test_block_type_from_string(self):
        """Test creating BlockType from string value."""
        assert BlockType("dialogue") == BlockType.DIALOGUE
        assert BlockType("narration") == BlockType.NARRATION
        assert BlockType("description") == BlockType.DESCRIPTION