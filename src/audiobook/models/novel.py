"""Novel-related data models for audiobook system."""

from dataclasses import dataclass, field
from typing import Optional

from audiobook.models.base import BlockType


@dataclass
class Dialogue:
    """Represents a dialogue within a block."""

    speaker: str
    content: str
    emotion_hint: Optional[str] = None


@dataclass
class Position:
    """Represents a position range in text."""

    start: int
    end: int

    def __post_init__(self):
        """Validate position values."""
        if self.start < 0:
            raise ValueError(f"Position start cannot be negative: {self.start}")
        if self.end < self.start:
            raise ValueError(
                f"Position end ({self.end}) cannot be less than start ({self.start})"
            )


@dataclass
class Block:
    """Represents a text block in a novel chapter."""

    block_id: str
    chapter: int
    position: Position
    text: str
    type: BlockType = BlockType.NARRATION
    dialogues: list[Dialogue] = field(default_factory=list)

    def __post_init__(self):
        """Convert dict position to Position object if needed."""
        if isinstance(self.position, dict):
            self.position = Position(**self.position)


@dataclass
class Novel:
    """Represents a novel with its metadata and content blocks."""

    novel_id: str
    title: str
    file_path: str
    encoding: str = "utf-8"
    blocks: list[Block] = field(default_factory=list)
    characters: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """Result of parsing a novel file."""

    novel_id: str
    title: str
    total_chapters: int
    total_characters: int
    character_names: list[str]
    encoding: str
    blocks: list[Block] = field(default_factory=list)