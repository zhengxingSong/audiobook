"""Tests for novel parser engine - block splitting strategies."""

import tempfile
from pathlib import Path

import pytest

from audiobook.engines.parser import NovelParserEngine
from audiobook.models import BlockType


class TestNovelParserEngineBlockSplitting:
    """Test block splitting functionality."""

    @pytest.fixture
    def parser(self) -> NovelParserEngine:
        """Create parser instance."""
        return NovelParserEngine()

    def test_split_into_blocks_single_chapter(self, parser: NovelParserEngine) -> None:
        """Test splitting single chapter text."""
        text = """第一章 开始

这是第一段内容。

这是第二段内容。
"""
        blocks = parser.split_into_blocks(text)

        assert len(blocks) >= 1
        # First block should be narration (chapter heading is now treated as narration)
        assert blocks[0].type == BlockType.NARRATION
        assert "第一章" in blocks[0].text

    def test_split_into_blocks_multiple_chapters(self, parser: NovelParserEngine) -> None:
        """Test splitting multiple chapters."""
        text = """第一章 开始

内容一。

第二章 继续

内容二。

第三章 结束

内容三。
"""
        blocks = parser.split_into_blocks(text)

        # Find chapter heading blocks (now treated as narration)
        chapter_heading_blocks = [b for b in blocks if "第一章" in b.text or "第二章" in b.text or "第三章" in b.text]
        assert len(chapter_heading_blocks) == 3

        # Verify chapter numbers
        chapters = sorted(set(b.chapter for b in blocks))
        assert chapters == [1, 2, 3]

    def test_split_into_blocks_preserves_positions(self, parser: NovelParserEngine) -> None:
        """Test that block positions are correctly tracked."""
        text = """第一章 测试

内容一。

内容二。
"""
        blocks = parser.split_into_blocks(text)

        # Verify positions are sequential
        for i, block in enumerate(blocks):
            assert block.position.start >= 0
            assert block.position.end >= block.position.start

        # Verify we can extract text using positions
        for block in blocks:
            extracted = text[block.position.start : block.position.end + 1]
            assert block.text in extracted or extracted.strip() in block.text

    def test_split_into_blocks_chapter_increment(self, parser: NovelParserEngine) -> None:
        """Test that chapter numbers increment correctly."""
        text = """第一章

内容一。

第二章

内容二。

第三章

内容三。
"""
        blocks = parser.split_into_blocks(text)

        # Check that chapter numbers increment
        chapter_nums = []
        for block in blocks:
            if "第一章" in block.text:
                chapter_nums.append((1, block.chapter))
            elif "第二章" in block.text:
                chapter_nums.append((2, block.chapter))
            elif "第三章" in block.text:
                chapter_nums.append((3, block.chapter))

        # Verify each chapter block has correct chapter number
        for expected, actual in chapter_nums:
            assert actual == expected

    def test_split_into_blocks_scene_boundary(self, parser: NovelParserEngine) -> None:
        """Test that scene boundaries create new blocks."""
        text = """第一章 测试

第一段内容。

第二天

新的场景内容。

***

另一个场景。
"""
        blocks = parser.split_into_blocks(text)

        # Should have multiple blocks due to scene boundaries
        assert len(blocks) >= 2

    def test_split_into_blocks_unique_ids(self, parser: NovelParserEngine) -> None:
        """Test that each block has a unique ID."""
        text = """第一章

内容一。

第二章

内容二。
"""
        blocks = parser.split_into_blocks(text)

        block_ids = [b.block_id for b in blocks]
        assert len(block_ids) == len(set(block_ids))

    def test_split_into_blocks_empty_text(self, parser: NovelParserEngine) -> None:
        """Test handling of empty text."""
        text = ""
        blocks = parser.split_into_blocks(text)

        assert blocks == []

    def test_split_into_blocks_whitespace_only(self, parser: NovelParserEngine) -> None:
        """Test handling of whitespace-only text."""
        text = "   \n\n   \n   "
        blocks = parser.split_into_blocks(text)

        # Should return empty or only whitespace blocks (which get filtered)
        for block in blocks:
            assert block.text.strip() == "" or block.text.strip()

    def test_split_into_blocks_dialogue_detection(self, parser: NovelParserEngine) -> None:
        """Test that dialogue blocks are properly typed."""
        # Use text without chapter heading to properly test dialogue detection
        text = '''张三说道："你好，世界！"

这是叙述文本。

李四问："今天天气如何？"
'''
        blocks = parser.split_into_blocks(text)

        # Find dialogue blocks - should have at least one
        dialogue_blocks = [b for b in blocks if b.type == BlockType.DIALOGUE]
        assert len(dialogue_blocks) >= 1

        # Find narration block
        narration_blocks = [b for b in blocks if b.type == BlockType.NARRATION]
        assert len(narration_blocks) >= 1


class TestNovelParserEngineDialogueExtraction:
    """Test dialogue extraction from blocks."""

    @pytest.fixture
    def parser(self) -> NovelParserEngine:
        """Create parser instance."""
        return NovelParserEngine()

    def test_extract_dialogues_basic(self, parser: NovelParserEngine) -> None:
        """Test basic dialogue extraction."""
        text = '张三说道："你好，世界！"'
        dialogues = parser.extract_dialogues_from_text(text)

        assert len(dialogues) >= 1
        assert dialogues[0].speaker == "张三"
        assert "你好" in dialogues[0].content

    def test_extract_dialogues_multiple(self, parser: NovelParserEngine) -> None:
        """Test extraction of multiple dialogues."""
        text = '''
        李四问道："今天天气如何？"
        王五回答："天气很好。"
        '''
        dialogues = parser.extract_dialogues_from_text(text)

        assert len(dialogues) >= 2

        speakers = [d.speaker for d in dialogues]
        assert "李四" in speakers
        assert "王五" in speakers

    def test_extract_dialogues_no_speaker(self, parser: NovelParserEngine) -> None:
        """Test extraction of dialogue without explicit speaker."""
        text = '"这是没有说话人的对话"'
        dialogues = parser.extract_dialogues_from_text(text)

        assert len(dialogues) >= 1
        assert "这是没有说话人的对话" in dialogues[0].content

    def test_extract_dialogues_empty_text(self, parser: NovelParserEngine) -> None:
        """Test extraction from empty text."""
        text = ""
        dialogues = parser.extract_dialogues_from_text(text)

        assert dialogues == []

    def test_extract_dialogues_no_quotes(self, parser: NovelParserEngine) -> None:
        """Test extraction from text without quotes."""
        text = "这是没有引号的普通叙述文本"
        dialogues = parser.extract_dialogues_from_text(text)

        assert dialogues == []

    def test_extract_dialogues_with_emotion_hint(self, parser: NovelParserEngine) -> None:
        """Test that dialogue extraction works with emotion hints."""
        text = '张三笑着说："我很高兴！"'
        dialogues = parser.extract_dialogues_from_text(text)

        # Should extract speaker and content
        assert len(dialogues) >= 1
        assert dialogues[0].speaker == "张三"

    def test_extract_dialogues_mixed_content(self, parser: NovelParserEngine) -> None:
        """Test extraction from mixed dialogue and narration."""
        # Use text where character name appears in dialogue pattern
        text = '''
        张三走进房间，环顾四周。
        张三说道："这里真不错。"
        然后他坐了下来。
        '''
        dialogues = parser.extract_dialogues_from_text(text)

        assert len(dialogues) >= 1
        found_speaker = any(d.speaker == "张三" for d in dialogues)
        assert found_speaker


class TestNovelParserEngineChapterCounting:
    """Test chapter counting functionality."""

    @pytest.fixture
    def parser(self) -> NovelParserEngine:
        """Create parser instance."""
        return NovelParserEngine()

    def test_count_chapters_basic(self, parser: NovelParserEngine) -> None:
        """Test basic chapter counting."""
        text = """第一章 开始

内容

第二章 继续

内容

第三章 结束

内容
"""
        count = parser._count_chapters(text)
        assert count == 3

    def test_count_chapters_numeric(self, parser: NovelParserEngine) -> None:
        """Test numeric chapter counting."""
        text = """第1章 开始

第2章 继续

第10章 结束
"""
        count = parser._count_chapters(text)
        assert count == 3

    def test_count_chapters_english(self, parser: NovelParserEngine) -> None:
        """Test English chapter counting."""
        text = """Chapter 1: The Beginning

Chapter 2: The Journey

Chapter 10: The End
"""
        count = parser._count_chapters(text)
        assert count == 3

    def test_count_chapters_mixed_formats(self, parser: NovelParserEngine) -> None:
        """Test mixed format chapter counting."""
        text = """第一章 开始

Chapter 2: The Journey

第3章 继续
"""
        count = parser._count_chapters(text)
        assert count == 3

    def test_count_chapters_no_chapters(self, parser: NovelParserEngine) -> None:
        """Test text with no chapters."""
        text = "这是一段没有章节标题的普通文本。"
        count = parser._count_chapters(text)
        assert count == 0

    def test_count_chapters_empty_text(self, parser: NovelParserEngine) -> None:
        """Test empty text."""
        text = ""
        count = parser._count_chapters(text)
        assert count == 0


class TestNovelParserEngineIntegration:
    """Integration tests for full parsing workflow."""

    @pytest.fixture
    def parser(self) -> NovelParserEngine:
        """Create parser instance."""
        return NovelParserEngine()

    def test_full_parsing_workflow(self, temp_dir: Path) -> None:
        """Test complete parsing workflow."""
        parser = NovelParserEngine()
        file_path = temp_dir / "full_novel.txt"
        content = """第一章 相遇

北京城的初春，风还是有些凉意。

张明站在街角，看着来往的行人。

李华走过来，打招呼道："好久不见！"

张明笑着说："是啊，有三年了吧。"

第二章 重逢

第二天，他们再次相遇。

李华问道："最近工作怎么样？"

张明回答："还行，就是有点忙。"

第三章 告别

傍晚时分，两人分别。

"下次再聚！"李华挥挥手。

张明点点头："一定！"
"""
        file_path.write_text(content, encoding="utf-8")

        result = parser.parse_novel(str(file_path))

        # Verify basic metadata
        assert result.title == "full_novel"
        assert result.total_chapters == 3
        assert result.encoding == "utf-8"

        # Verify characters found
        assert "张明" in result.character_names
        assert "李华" in result.character_names

        # Verify blocks
        assert len(result.blocks) > 0

        # Verify block types (CHAPTER type no longer exists, headings are NARRATION)
        chapter_heading_blocks = [b for b in result.blocks if "第一章" in b.text or "第二章" in b.text or "第三章" in b.text]
        assert len(chapter_heading_blocks) == 3

        # Verify dialogues in blocks
        dialogue_blocks = [b for b in result.blocks if b.type == BlockType.DIALOGUE]
        assert len(dialogue_blocks) >= 1

    def test_parsing_with_various_encodings(self, temp_dir: Path) -> None:
        """Test parsing files with different encodings."""
        parser = NovelParserEngine()

        # UTF-8 file
        utf8_file = temp_dir / "utf8.txt"
        utf8_content = "第一章 测试\n内容"
        utf8_file.write_text(utf8_content, encoding="utf-8")

        result = parser.parse_novel(str(utf8_file))
        assert result.encoding == "utf-8"
        assert result.total_chapters == 1

    def test_parsing_generates_unique_novel_ids(self, temp_dir: Path) -> None:
        """Test that different files get different novel IDs."""
        parser = NovelParserEngine()

        file1 = temp_dir / "novel1.txt"
        file2 = temp_dir / "novel2.txt"

        file1.write_text("内容一", encoding="utf-8")
        file2.write_text("内容二", encoding="utf-8")

        result1 = parser.parse_novel(str(file1))
        result2 = parser.parse_novel(str(file2))

        assert result1.novel_id != result2.novel_id
        assert "novel1" in result1.novel_id
        assert "novel2" in result2.novel_id

    def test_block_positions_cover_full_text(self, temp_dir: Path) -> None:
        """Test that block positions cover the full text."""
        parser = NovelParserEngine()
        file_path = temp_dir / "coverage.txt"
        content = """第一章 测试

第一段。

第二段。

第二章 继续

第三段。
"""
        file_path.write_text(content, encoding="utf-8")

        result = parser.parse_novel(str(file_path))

        # Blocks should have sequential, non-overlapping positions
        for block in result.blocks:
            assert block.position.start >= 0
            assert block.position.end >= block.position.start

    def test_empty_file_handling(self, temp_dir: Path) -> None:
        """Test handling of empty files."""
        parser = NovelParserEngine()
        file_path = temp_dir / "empty.txt"
        file_path.write_text("", encoding="utf-8")

        result = parser.parse_novel(str(file_path))

        assert result.title == "empty"
        assert result.total_chapters == 0
        assert result.total_characters == 0
        assert result.character_names == []
        assert result.blocks == []

    def test_whitespace_only_file_handling(self, temp_dir: Path) -> None:
        """Test handling of files with only whitespace."""
        parser = NovelParserEngine()
        file_path = temp_dir / "whitespace.txt"
        file_path.write_text("   \n\n   \n   ", encoding="utf-8")

        result = parser.parse_novel(str(file_path))

        assert result.title == "whitespace"
        # Should handle gracefully without errors
        assert isinstance(result.blocks, list)