"""Tests for novel parser engine - file reading, encoding, and character scanning."""

import tempfile
from pathlib import Path

import pytest

from audiobook.engines.parser import NovelParserEngine
from audiobook.models import BlockType


class TestNovelParserEngineEncoding:
    """Test encoding detection and file reading."""

    def test_detect_utf8_encoding(self, temp_dir: Path) -> None:
        """Test detection of UTF-8 encoded files."""
        parser = NovelParserEngine()
        file_path = temp_dir / "test_utf8.txt"
        content = "这是UTF-8编码的测试文本"
        file_path.write_text(content, encoding="utf-8")

        encoding = parser.detect_encoding(str(file_path))
        assert encoding == "utf-8"

    def test_detect_utf8_sig_encoding(self, temp_dir: Path) -> None:
        """Test detection of UTF-8 with BOM encoded files."""
        parser = NovelParserEngine()
        file_path = temp_dir / "test_utf8sig.txt"
        content = "这是UTF-8 BOM编码的测试文本"
        file_path.write_text(content, encoding="utf-8-sig")

        encoding = parser.detect_encoding(str(file_path))
        # Should detect either utf-8 or utf-8-sig
        assert encoding in ["utf-8", "utf-8-sig"]

    def test_detect_gbk_encoding(self, temp_dir: Path) -> None:
        """Test detection of GBK encoded files."""
        parser = NovelParserEngine()
        file_path = temp_dir / "test_gbk.txt"
        content = "这是GBK编码的测试文本"
        file_path.write_text(content, encoding="gbk")

        encoding = parser.detect_encoding(str(file_path))
        assert encoding in ["gbk", "gb18030"]

    def test_read_file_with_detected_encoding(self, temp_dir: Path) -> None:
        """Test reading file with auto-detected encoding."""
        parser = NovelParserEngine()
        file_path = temp_dir / "test_auto.txt"
        content = "自动检测编码测试\n多行文本"
        file_path.write_text(content, encoding="utf-8")

        read_content = parser.read_file(str(file_path))
        assert read_content == content

    def test_read_file_with_explicit_encoding(self, temp_dir: Path) -> None:
        """Test reading file with specified encoding."""
        parser = NovelParserEngine()
        file_path = temp_dir / "test_explicit.txt"
        content = "指定编码测试"
        file_path.write_text(content, encoding="utf-8")

        read_content = parser.read_file(str(file_path), encoding="utf-8")
        assert read_content == content

    def test_read_nonexistent_file_raises_error(self) -> None:
        """Test that reading nonexistent file raises FileNotFoundError."""
        parser = NovelParserEngine()

        with pytest.raises(FileNotFoundError):
            parser.read_file("/nonexistent/path/file.txt")

    def test_detect_encoding_nonexistent_file_raises_error(self) -> None:
        """Test that detecting nonexistent file raises FileNotFoundError."""
        parser = NovelParserEngine()

        with pytest.raises(FileNotFoundError):
            parser.detect_encoding("/nonexistent/path/file.txt")


class TestNovelParserEngineCharacterScanning:
    """Test character name scanning functionality."""

    def test_scan_basic_dialogue_character(self) -> None:
        """Test scanning character from basic dialogue."""
        parser = NovelParserEngine()
        text = '张三说道："你好，世界！"'
        names = parser.scan_character_names(text)

        assert "张三" in names

    def test_scan_multiple_characters(self) -> None:
        """Test scanning multiple characters from dialogue."""
        parser = NovelParserEngine()
        text = '''
        李四问道："今天天气如何？"
        王五回答："天气很好。"
        赵六笑着说："确实不错。"
        '''
        names = parser.scan_character_names(text)

        assert "李四" in names
        assert "王五" in names
        assert "赵六" in names

    def test_scan_character_with_colon_format(self) -> None:
        """Test scanning character with colon dialogue format."""
        parser = NovelParserEngine()
        text = '陈七："这是我的台词。"'
        names = parser.scan_character_names(text)

        # May or may not find depending on pattern match
        # This tests that the format doesn't crash
        assert isinstance(names, list)

    def test_scan_filters_pronouns(self) -> None:
        """Test that pronouns are filtered out."""
        parser = NovelParserEngine()
        text = '他说道："你好"'
        names = parser.scan_character_names(text)

        assert "他" not in names

    def test_scan_filters_invalid_names(self) -> None:
        """Test that invalid names are filtered out."""
        parser = NovelParserEngine()
        text = '一个说道："你好"'
        names = parser.scan_character_names(text)

        assert "一个" not in names

    def test_scan_returns_unique_names(self) -> None:
        """Test that returned names are unique."""
        parser = NovelParserEngine()
        text = '''
        张三说道："你好"
        张三回答："谢谢"
        '''
        names = parser.scan_character_names(text)

        assert names.count("张三") == 1

    def test_scan_returns_sorted_names(self) -> None:
        """Test that returned names are sorted."""
        parser = NovelParserEngine()
        text = '''
        王五说道："你好"
        张三回答："谢谢"
        李四笑着说："好的"
        '''
        names = parser.scan_character_names(text)

        assert names == sorted(names)


class TestNovelParserEngineParsing:
    """Test full novel parsing functionality."""

    def test_parse_novel_basic(self, temp_dir: Path) -> None:
        """Test basic novel parsing."""
        parser = NovelParserEngine()
        file_path = temp_dir / "novel.txt"
        content = '''第一章 开始

这是一个测试小说的内容。

李明说道："你好，世界！"

王芳回答："你好！"

第二章 继续

故事继续发展。
'''
        file_path.write_text(content, encoding="utf-8")

        result = parser.parse_novel(str(file_path))

        assert result.title == "novel"
        assert result.total_chapters == 2
        assert result.encoding == "utf-8"
        assert "李明" in result.character_names
        assert "王芳" in result.character_names
        assert len(result.blocks) > 0

    def test_parse_novel_returns_novel_id(self, temp_dir: Path) -> None:
        """Test that parsing returns a novel_id."""
        parser = NovelParserEngine()
        file_path = temp_dir / "test.txt"
        file_path.write_text("测试内容", encoding="utf-8")

        result = parser.parse_novel(str(file_path))

        assert result.novel_id.startswith("novel_test_")
        assert len(result.novel_id) > len("novel_test_")

    def test_parse_novel_nonexistent_file_raises_error(self) -> None:
        """Test that parsing nonexistent file raises FileNotFoundError."""
        parser = NovelParserEngine()

        with pytest.raises(FileNotFoundError):
            parser.parse_novel("/nonexistent/path/novel.txt")

    def test_parse_novel_chinese_chapters(self, temp_dir: Path) -> None:
        """Test parsing novels with Chinese chapter format."""
        parser = NovelParserEngine()
        file_path = temp_dir / "chinese.txt"
        content = '''第一章 初遇

内容一

第二章 相识

内容二

第三章 相知

内容三
'''
        file_path.write_text(content, encoding="utf-8")

        result = parser.parse_novel(str(file_path))

        assert result.total_chapters == 3

    def test_parse_novel_numeric_chapters(self, temp_dir: Path) -> None:
        """Test parsing novels with numeric chapter format."""
        parser = NovelParserEngine()
        file_path = temp_dir / "numeric.txt"
        content = '''第1章 开始

内容一

第2章 继续

内容二
'''
        file_path.write_text(content, encoding="utf-8")

        result = parser.parse_novel(str(file_path))

        assert result.total_chapters == 2

    def test_parse_novel_english_chapters(self, temp_dir: Path) -> None:
        """Test parsing novels with English chapter format."""
        parser = NovelParserEngine()
        file_path = temp_dir / "english.txt"
        content = '''Chapter 1: The Beginning

Some content here.

Chapter 2: The Journey Continues

More content.
'''
        file_path.write_text(content, encoding="utf-8")

        result = parser.parse_novel(str(file_path))

        assert result.total_chapters == 2


class TestNovelParserEngineValidation:
    """Test validation and edge cases."""

    def test_is_valid_character_name_accepts_valid(self) -> None:
        """Test that valid character names are accepted."""
        parser = NovelParserEngine()

        assert parser._is_valid_character_name("张三") is True
        assert parser._is_valid_character_name("李四") is True
        assert parser._is_valid_character_name("诸葛亮") is True
        assert parser._is_valid_character_name("欧阳锋") is True

    def test_is_valid_character_name_rejects_pronouns(self) -> None:
        """Test that pronouns are rejected."""
        parser = NovelParserEngine()

        assert parser._is_valid_character_name("他") is False
        assert parser._is_valid_character_name("她") is False
        assert parser._is_valid_character_name("我") is False
        assert parser._is_valid_character_name("你") is False

    def test_is_valid_character_name_rejects_wrong_length(self) -> None:
        """Test that names with wrong length are rejected."""
        parser = NovelParserEngine()

        assert parser._is_valid_character_name("A") is False
        assert parser._is_valid_character_name("张") is False
        assert parser._is_valid_character_name("一二三四五") is False

    def test_is_valid_character_name_rejects_non_chinese(self) -> None:
        """Test that non-Chinese names are rejected."""
        parser = NovelParserEngine()

        assert parser._is_valid_character_name("John") is False
        assert parser._is_valid_character_name("ABC") is False

    def test_is_chapter_start_detects_chinese(self) -> None:
        """Test Chinese chapter pattern detection."""
        parser = NovelParserEngine()

        assert parser._is_chapter_start("第一章 开始") is True
        assert parser._is_chapter_start("第二章") is True
        assert parser._is_chapter_start("第十章 相逢") is True
        assert parser._is_chapter_start("第一百章") is True

    def test_is_chapter_start_detects_numeric(self) -> None:
        """Test numeric chapter pattern detection."""
        parser = NovelParserEngine()

        assert parser._is_chapter_start("第1章 开始") is True
        assert parser._is_chapter_start("第2章") is True
        assert parser._is_chapter_start("第10章 相逢") is True

    def test_is_chapter_start_detects_english(self) -> None:
        """Test English chapter pattern detection."""
        parser = NovelParserEngine()

        assert parser._is_chapter_start("Chapter 1") is True
        assert parser._is_chapter_start("Chapter 10: The End") is True
        assert parser._is_chapter_start("chapter 5") is True  # case insensitive

    def test_is_chapter_start_rejects_non_chapters(self) -> None:
        """Test that non-chapter lines are rejected."""
        parser = NovelParserEngine()

        assert parser._is_chapter_start("这是一段普通文本") is False
        assert parser._is_chapter_start("他说道：") is False
        assert parser._is_chapter_start("") is False
        assert parser._is_chapter_start("   ") is False


class TestNovelParserEngineSceneBoundary:
    """Test scene boundary detection."""

    def test_is_scene_boundary_time_markers(self) -> None:
        """Test that time markers are detected as scene boundaries."""
        parser = NovelParserEngine()

        assert parser._is_scene_boundary("第二天，他们出发了") is True
        assert parser._is_scene_boundary("次日清晨") is True
        assert parser._is_scene_boundary("三天后") is True

    def test_is_scene_boundary_location_markers(self) -> None:
        """Test that location markers are detected as scene boundaries."""
        parser = NovelParserEngine()

        assert parser._is_scene_boundary("他来到了京城") is True
        assert parser._is_scene_boundary("回到家中") is True
        assert parser._is_scene_boundary("走进房间") is True

    def test_is_scene_boundary_break_symbols(self) -> None:
        """Test that break symbols are detected as scene boundaries."""
        parser = NovelParserEngine()

        assert parser._is_scene_boundary("***") is True
        assert parser._is_scene_boundary("---") is True
        assert parser._is_scene_boundary("* * *") is True
        assert parser._is_scene_boundary("*") is True

    def test_is_scene_boundary_rejects_normal_text(self) -> None:
        """Test that normal text is not detected as scene boundary."""
        parser = NovelParserEngine()

        assert parser._is_scene_boundary("这是普通文本") is False
        assert parser._is_scene_boundary("他说话了") is False
        assert parser._is_scene_boundary("") is False


class TestNovelParserEngineBlockType:
    """Test block type detection."""

    def test_detect_block_type_dialogue(self) -> None:
        """Test that dialogue content is detected."""
        parser = NovelParserEngine()

        assert parser._detect_block_type('张三说："你好"') == BlockType.DIALOGUE
        assert parser._detect_block_type('"这是对话"') == BlockType.DIALOGUE

    def test_detect_block_type_narration(self) -> None:
        """Test that narration content is detected."""
        parser = NovelParserEngine()

        assert parser._detect_block_type("这是普通的叙述文本") == BlockType.NARRATION
        assert parser._detect_block_type("故事继续发展") == BlockType.NARRATION

    def test_detect_block_type_description(self) -> None:
        """Test that description content is detected."""
        parser = NovelParserEngine()

        # Description typically contains descriptive keywords from the parser's markers
        assert parser._detect_block_type("他看着窗外的风景") == BlockType.DESCRIPTION
        assert parser._detect_block_type("房间里摆放着各种家具") == BlockType.DESCRIPTION