"""小说解析引擎 - 文件读取、编码检测、分块策略"""

import hashlib
import re
from pathlib import Path
from typing import Optional

from audiobook.models import Block, BlockType
from audiobook.models.novel import Dialogue, Novel, ParseResult, Position


class NovelParserEngine:
    """Engine for parsing novel files into structured blocks.

    Handles encoding detection, character name extraction,
    chapter detection, and content block splitting.
    """

    ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "gbk", "gb18030", "big5"]
    CHAPTER_PATTERNS = [
        r"^第[一二三四五六七八九十百千万零\d]+[章节回]\s*.*$",
        r"^[一二三四五六七八九十百千万零]+[、.]\s*.*$",
        r"^Chapter\s*\d+.*$",
    ]
    TIME_MARKERS = ["第二天", "次日", "清晨", "傍晚", "黄昏", "入夜", "三天后", "一周后"]
    LOCATION_MARKERS = ["来到了", "回到", "走进", "走出", "来到", "离开", "到达"]

    # Common Chinese name patterns
    NAME_PATTERN = re.compile(r"^[\u4e00-\u9fa5]{2,4}$")

    # Dialogue patterns - speaker + action + quote format
    # Format: "张三说道："你好"" - name outside quotes
    # Use complete action words first to prevent partial matches
    # Use non-greedy quantifier {2,4}? to prefer shorter name matches
    DIALOGUE_WITH_SPEAKER_PATTERN = re.compile(
        r'([\u4e00-\u9fa5]{2,4}?)(?:笑着|生气地|激动地)?(?:回答道?|打招呼道?|说道?|问道?|喊道?|叫道?|笑道?)[：:][""]([^"""]+)[""]'
    )

    # Standalone dialogue pattern (just quotes)
    QUOTE_PATTERN = re.compile(r'[""]([^"""]+)[""]')

    def parse_novel(self, file_path: str) -> ParseResult:
        """Parse a novel file and return structured ParseResult.

        Args:
            file_path: Path to the novel file.

        Returns:
            ParseResult with novel metadata, blocks, and characters.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file cannot be read with any supported encoding.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Novel file not found: {file_path}")

        # Detect encoding and read content
        encoding = self.detect_encoding(file_path)
        text = self.read_file(file_path, encoding)

        # Extract title from filename
        title = path.stem

        # Scan for character names
        character_names = self.scan_character_names(text)

        # Split into blocks
        blocks = self.split_into_blocks(text)

        # Count chapters
        total_chapters = self._count_chapters(text)

        # Generate novel ID
        novel_id = self._generate_novel_id(file_path)

        return ParseResult(
            novel_id=novel_id,
            title=title,
            total_chapters=total_chapters,
            total_characters=len(character_names),
            character_names=character_names,
            encoding=encoding,
            blocks=blocks,
        )

    def detect_encoding(self, file_path: str) -> str:
        """Detect the encoding of a file by trying different encodings.

        Args:
            file_path: Path to the file.

        Returns:
            Detected encoding name.

        Raises:
            ValueError: If no encoding can decode the file.
        """
        path = Path(file_path)

        for encoding in self.ENCODINGS_TO_TRY:
            try:
                with open(path, "r", encoding=encoding) as f:
                    # Try to read a significant portion to verify encoding
                    f.read(4096)
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue

        raise ValueError(
            f"Cannot detect encoding for file: {file_path}. "
            f"Tried encodings: {', '.join(self.ENCODINGS_TO_TRY)}"
        )

    def read_file(self, file_path: str, encoding: Optional[str] = None) -> str:
        """Read file content with specified or detected encoding.

        Args:
            file_path: Path to the file.
            encoding: Optional encoding to use. If None, auto-detect.

        Returns:
            File content as string.

        Raises:
            FileNotFoundError: If file does not exist.
            ValueError: If file cannot be read.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if encoding is None:
            encoding = self.detect_encoding(file_path)

        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError) as e:
            raise ValueError(f"Failed to read file with encoding {encoding}: {e}")

    def scan_character_names(self, text: str) -> list[str]:
        """Scan text for character names using dialogue patterns.

        Args:
            text: Novel text content.

        Returns:
            List of unique character names found.
        """
        names: set[str] = set()

        # Extract names from dialogue patterns: "张三说道："你好""
        for match in self.DIALOGUE_WITH_SPEAKER_PATTERN.finditer(text):
            speaker = match.group(1).strip()
            if self._is_valid_character_name(speaker):
                names.add(speaker)

        # Also look for simple "xxx说" patterns (without quotes or incomplete patterns)
        # Use complete action words to avoid partial matches
        # Use non-greedy quantifier to prefer shorter name matches
        say_pattern = re.compile(
            r"([\u4e00-\u9fa5]{2,4}?)(?:笑着|生气地|激动地)?(?:回答道?|打招呼道?|说道?|问道?|喊道?|叫道?|笑道?)"
        )
        for match in say_pattern.finditer(text):
            name = match.group(1).strip()
            if self._is_valid_character_name(name):
                names.add(name)

        return sorted(names)

    def split_into_blocks(self, text: str) -> list[Block]:
        """Split text into blocks using chapter and scene boundaries.

        Args:
            text: Novel text content.

        Returns:
            List of Block objects.
        """
        blocks: list[Block] = []
        lines = text.split("\n")

        current_chapter = 0
        current_block_lines: list[str] = []
        current_block_start = 0
        position = 0
        block_counter = 0

        def flush_block():
            nonlocal block_counter
            if not current_block_lines:
                return

            block_text = "\n".join(current_block_lines).strip()
            if not block_text:
                return

            block_type = self._detect_block_type(block_text)
            block_id = f"block_{block_counter:04d}"
            block_counter += 1

            dialogues = self.extract_dialogues_from_text(block_text)

            block = Block(
                block_id=block_id,
                chapter=current_chapter,
                position=Position(start=current_block_start, end=position - 1),
                text=block_text,
                type=block_type,
                dialogues=dialogues,
            )
            blocks.append(block)

        for line in lines:
            line_len = len(line) + 1  # +1 for newline
            stripped = line.strip()

            # Check for chapter start
            if self._is_chapter_start(stripped):
                flush_block()
                current_chapter += 1
                current_block_lines = [line]
                current_block_start = position
            # Check for scene boundary
            elif self._is_scene_boundary(stripped):
                flush_block()
                current_block_lines = [line]
                current_block_start = position
            # Empty line indicates paragraph boundary - flush current block
            elif not stripped:
                flush_block()
                current_block_lines = []
                current_block_start = position + line_len  # Start after this empty line
            else:
                current_block_lines.append(line)

            position += line_len

        # Flush remaining content
        flush_block()

        return blocks

    def extract_dialogues_from_text(self, text: str) -> list[Dialogue]:
        """Extract dialogues from a text block.

        Args:
            text: Text content to extract dialogues from.

        Returns:
            List of Dialogue objects.
        """
        dialogues: list[Dialogue] = []

        # Try structured patterns first: "张三说道："你好""
        for match in self.DIALOGUE_WITH_SPEAKER_PATTERN.finditer(text):
            speaker = match.group(1).strip()
            content = match.group(2).strip()
            if self._is_valid_character_name(speaker):
                dialogues.append(Dialogue(speaker=speaker, content=content))

        # If no structured dialogues found, look for simple quotes
        if not dialogues:
            for match in self.QUOTE_PATTERN.finditer(text):
                content = match.group(1).strip()
                # Only add if it looks like dialogue (not too short, not narration)
                if len(content) > 2:
                    dialogues.append(Dialogue(speaker="", content=content))

        return dialogues

    def _is_chapter_start(self, line: str) -> bool:
        """Check if a line indicates a chapter start.

        Args:
            line: Line to check.

        Returns:
            True if line is a chapter heading.
        """
        if not line:
            return False

        for pattern in self.CHAPTER_PATTERNS:
            if re.match(pattern, line, re.IGNORECASE):
                return True
        return False

    def _is_scene_boundary(self, line: str) -> bool:
        """Check if a line indicates a scene boundary.

        Args:
            line: Line to check.

        Returns:
            True if line indicates a scene change.
        """
        if not line:
            return False

        # Check for time markers
        for marker in self.TIME_MARKERS:
            if marker in line:
                return True

        # Check for location markers
        for marker in self.LOCATION_MARKERS:
            if marker in line:
                return True

        # Check for common scene break indicators
        if line.strip() in ["***", "---", "* * *", "*"]:
            return True

        return False

    def _detect_block_type(self, text: str) -> BlockType:
        """Detect the type of a text block.

        Args:
            text: Text content to analyze.

        Returns:
            BlockType for the content.
        """
        # Check for dialogue content
        quote_count = text.count('"') + text.count('"')
        if quote_count >= 2:
            return BlockType.DIALOGUE

        # Check for description (scene descriptions, setting)
        if any(marker in text for marker in ["看着", "走", "坐", "站", "想", "感觉", "窗外", "房间"]):
            return BlockType.DESCRIPTION

        # Default to narration
        return BlockType.NARRATION

    def _is_valid_character_name(self, name: str) -> bool:
        """Validate if a string is a likely character name.

        Args:
            name: Name to validate.

        Returns:
            True if name is a valid character name.
        """
        if not name:
            return False

        # Length check (Chinese names are typically 2-4 characters)
        if not (2 <= len(name) <= 4):
            return False

        # Must be all Chinese characters
        if not self.NAME_PATTERN.match(name):
            return False

        # Filter out common non-name patterns
        invalid_patterns = [
            "他", "她", "它", "我", "你", "你们", "我们", "他们", "她们",
            "这", "那", "什么", "怎么", "为什么", "哪里", "那里", "这里",
            "一个", "这个", "那个", "每个", "大家", "众人", "其他人",
        ]

        if name in invalid_patterns:
            return False

        return True

    def _generate_novel_id(self, file_path: str) -> str:
        """Generate a unique novel ID from file path.

        Args:
            file_path: Path to the novel file.

        Returns:
            Unique novel ID string.
        """
        path = Path(file_path)
        # Use hash of absolute path for uniqueness
        abs_path = str(path.resolve())
        hash_value = hashlib.md5(abs_path.encode()).hexdigest()[:8]
        return f"novel_{path.stem}_{hash_value}"

    def _count_chapters(self, text: str) -> int:
        """Count the number of chapters in the text.

        Args:
            text: Novel text content.

        Returns:
            Number of chapters detected.
        """
        count = 0
        for line in text.split("\n"):
            if self._is_chapter_start(line.strip()):
                count += 1
        return count