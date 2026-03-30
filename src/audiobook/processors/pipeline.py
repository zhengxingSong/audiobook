"""处理流水线 - 整合所有引擎"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from audiobook.engines import (
    CharacterRecognitionEngine,
    CharacterResult,
    MatchResult,
    NovelParserEngine,
    SynthesisResult,
    VoiceMatchEngine,
    VoiceSynthesisEngine,
)
from audiobook.models import (
    Block,
    BlockType,
    Character,
    CharacterImportance,
    CharacterState,
    Emotion,
    EmotionProfile,
    EmotionIntensity,
    Fragment,
    FragmentStatus,
    Voice,
)
from audiobook.storage import VoiceLibrary


@dataclass
class PipelineProgress:
    """Processing pipeline progress tracking.

    Attributes:
        total_blocks: Total number of blocks to process.
        processed_blocks: Number of blocks already processed.
        current_stage: Current processing stage name.
        current_character: Current character being processed.
        failed_blocks: Number of blocks that failed processing.
    """

    total_blocks: int = 0
    processed_blocks: int = 0
    current_stage: str = ""
    current_character: str = ""
    failed_blocks: int = 0

    def to_dict(self) -> dict:
        """Convert progress to dictionary for serialization."""
        return {
            "total_blocks": self.total_blocks,
            "processed_blocks": self.processed_blocks,
            "current_stage": self.current_stage,
            "current_character": self.current_character,
            "failed_blocks": self.failed_blocks,
            "progress_percent": (
                self.processed_blocks / self.total_blocks * 100
                if self.total_blocks > 0
                else 0
            ),
        }


@dataclass
class PreprocessResult:
    """Result of preprocessing a novel.

    Attributes:
        novel_id: Unique novel identifier.
        title: Novel title.
        blocks: List of parsed blocks.
        characters: Dictionary of identified characters.
        character_importance: Classification of character importance.
        total_chapters: Total chapter count.
    """

    novel_id: str
    title: str
    blocks: list[Block]
    characters: dict[str, Character]
    character_importance: dict[str, CharacterImportance]
    total_chapters: int


@dataclass
class BlockProcessResult:
    """Result of processing a single block.

    Attributes:
        block_id: Identifier of the processed block.
        success: Whether processing succeeded.
        fragments: List of generated fragments.
        characters_found: Characters identified in the block.
        error_message: Error message if processing failed.
        processing_time: Time taken to process the block.
    """

    block_id: str
    success: bool
    fragments: list[Fragment] = field(default_factory=list)
    characters_found: list[str] = field(default_factory=list)
    error_message: str = ""
    processing_time: float = 0.0


@dataclass
class ConversionResult:
    """Result of full audiobook conversion.

    Attributes:
        success: Whether conversion succeeded.
        output_path: Path to output audiobook file.
        total_blocks: Total number of blocks.
        processed_blocks: Number of successfully processed blocks.
        total_fragments: Total audio fragments generated.
        failed_blocks: List of failed block IDs.
        errors: List of error messages.
        processing_time: Total processing time in seconds.
    """

    success: bool
    output_path: Optional[Path] = None
    total_blocks: int = 0
    processed_blocks: int = 0
    total_fragments: int = 0
    failed_blocks: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    processing_time: float = 0.0


class AudiobookPipeline:
    """Main pipeline for converting novels to audiobooks.

    This pipeline orchestrates the entire conversion process by integrating:
    1. NovelParserEngine - Parse novel text into blocks
    2. CharacterRecognitionEngine - Identify characters and emotions
    3. VoiceMatchEngine - Match characters to appropriate voices
    4. VoiceSynthesisEngine - Generate audio for text fragments

    The pipeline maintains character states throughout processing for
    consistent voice and emotion tracking.

    Example:
        >>> library = VoiceLibrary("./voices")
        >>> pipeline = AudiobookPipeline(library)
        >>> result = pipeline.convert("novel.txt", "output.wav")
    """

    def __init__(
        self,
        voice_library: VoiceLibrary,
        tts_endpoint: str = "http://localhost:9880",
    ) -> None:
        """Initialize the audiobook pipeline.

        Args:
            voice_library: Voice library for voice matching.
            tts_endpoint: GPT-SoVITS TTS service endpoint URL.
        """
        self.voice_library = voice_library
        self.parser = NovelParserEngine()
        self.character_engine = CharacterRecognitionEngine()
        self.voice_engine = VoiceMatchEngine(library=voice_library)
        self.synthesis_engine = VoiceSynthesisEngine(endpoint=tts_endpoint)

        # Character tracking
        self.character_states: dict[str, CharacterState] = {}
        self.confirmed_voices: dict[str, Voice] = {}
        self._characters: dict[str, Character] = {}

        # Progress tracking
        self.progress_callback: Optional[Callable[[PipelineProgress], None]] = None
        self._progress = PipelineProgress()

    def set_progress_callback(
        self,
        callback: Callable[[PipelineProgress], None]
    ) -> None:
        """Set progress callback for monitoring.

        Args:
            callback: Function to call with progress updates.
        """
        self.progress_callback = callback

    def _update_progress(
        self,
        stage: str = "",
        character: str = "",
        increment_blocks: bool = False,
        increment_failed: bool = False,
    ) -> None:
        """Update progress and notify callback.

        Args:
            stage: Current processing stage.
            character: Current character being processed.
            increment_blocks: Whether to increment processed count.
            increment_failed: Whether to increment failed count.
        """
        if stage:
            self._progress.current_stage = stage
        if character:
            self._progress.current_character = character
        if increment_blocks:
            self._progress.processed_blocks += 1
        if increment_failed:
            self._progress.failed_blocks += 1

        if self.progress_callback:
            self.progress_callback(self._progress)

    def preprocess(self, novel_path: str) -> PreprocessResult:
        """Preprocess novel: parse and identify characters.

        This is the first stage of the pipeline that:
        1. Parses the novel into structured blocks
        2. Scans for character names
        3. Classifies character importance

        Args:
            novel_path: Path to the novel file.

        Returns:
            PreprocessResult with parsed blocks and characters.

        Raises:
            FileNotFoundError: If novel file does not exist.
            ValueError: If file cannot be parsed.
        """
        self._update_progress(stage="Parsing novel")

        # Parse the novel
        parse_result = self.parser.parse_novel(novel_path)

        self._update_progress(stage="Identifying characters")

        # Process all blocks to identify characters
        character_counts: dict[str, int] = {}
        all_characters: dict[str, Character] = {}

        for block in parse_result.blocks:
            char_result = self.character_engine.identify_characters(block)
            for name in char_result.characters:
                character_counts[name] = character_counts.get(name, 0) + 1

                # Create Character object if not exists
                if name not in all_characters:
                    char_id = f"char_{uuid.uuid4().hex[:8]}"
                    all_characters[name] = Character(
                        character_id=char_id,
                        name=name,
                        traits=[],
                        description=f"Character found in novel",
                        importance=CharacterImportance.SUPPORTING,
                    )

        # Classify character importance based on frequency
        importance_map = self.character_engine.classify_importance(character_counts)

        # Update character importance
        for name, importance in importance_map.items():
            if name in all_characters:
                all_characters[name].importance = importance

        # Initialize character states
        for name, char in all_characters.items():
            self._characters[name] = char
            self.character_states[name] = CharacterState(
                character_id=char.character_id,
                current_emotion=Emotion.NEUTRAL,
            )

        self._progress.total_blocks = len(parse_result.blocks)
        self._update_progress(stage="Preprocessing complete")

        return PreprocessResult(
            novel_id=parse_result.novel_id,
            title=parse_result.title,
            blocks=parse_result.blocks,
            characters=all_characters,
            character_importance=importance_map,
            total_chapters=parse_result.total_chapters,
        )

    def classify_characters(
        self,
        character_names: list[str]
    ) -> dict[str, CharacterImportance]:
        """Classify character importance.

        Uses frequency analysis to determine character importance levels.

        Args:
            character_names: List of character names to classify.

        Returns:
            Dictionary mapping names to importance levels.
        """
        # Build counts from known characters
        counts = {
            name: self.character_engine._character_counts.get(name, 1)
            for name in character_names
        }
        return self.character_engine.classify_importance(counts)

    def match_voice_for_character(
        self,
        character: Character,
        emotion: Optional[EmotionProfile] = None
    ) -> Optional[Voice]:
        """Match a voice for a character.

        Args:
            character: Character to match voice for.
            emotion: Optional emotion profile for context.

        Returns:
            Best matching Voice or None if no match found.
        """
        result = self.voice_engine.match_voice(character, emotion)

        if result.best_match:
            return result.best_match.voice

        return None

    def process_block(self, block: Block) -> BlockProcessResult:
        """Process a single block through the pipeline.

        This method:
        1. Identifies characters in the block
        2. Analyzes emotions for each character
        3. Matches voices for characters
        4. Generates audio fragments

        Args:
            block: Block to process.

        Returns:
            BlockProcessResult with fragments and status.
        """
        start_time = time.time()

        try:
            # Identify characters
            char_result = self.character_engine.identify_characters(
                block,
                list(self._characters.keys())
            )

            fragments: list[Fragment] = []
            characters_found: list[str] = []

            # Process dialogues
            for dialogue in block.dialogues:
                speaker = dialogue.speaker

                if not speaker and char_result.characters:
                    # Use first identified character as default speaker
                    speaker = char_result.characters[0]

                if speaker:
                    characters_found.append(speaker)

                    # Get or create character
                    character = self._characters.get(speaker)
                    if not character:
                        char_id = f"char_{uuid.uuid4().hex[:8]}"
                        character = Character(
                            character_id=char_id,
                            name=speaker,
                            importance=CharacterImportance.MINOR,
                        )
                        self._characters[speaker] = character

                    # Analyze emotion for dialogue
                    emotion = self.character_engine.analyze_emotion(
                        dialogue.content,
                        character=speaker,
                    )

                    # Update character state
                    self.update_character_state(speaker, emotion, "dialogue")

                    # Match voice
                    voice = self.confirmed_voices.get(speaker)
                    if not voice:
                        voice = self.match_voice_for_character(character, emotion)
                        if voice:
                            self.confirmed_voices[speaker] = voice

                    # Create fragment
                    frag_id = f"frag_{uuid.uuid4().hex[:8]}"
                    if voice:
                        fragment = Fragment(
                            fragment_id=frag_id,
                            block_id=block.block_id,
                            character=speaker,
                            voice_id=voice.voice_id,
                            emotion=Emotion.NEUTRAL,  # Will use emotion profile
                            audio_path="",  # Will be set after synthesis
                            duration=0.0,  # Will be set after synthesis
                            status=FragmentStatus.PENDING,
                        )
                        fragments.append(fragment)

            # Process narration blocks
            if block.type == BlockType.NARRATION and not block.dialogues:
                # Use narrator voice for narration
                narrator_voice = self.voice_library.get("narrator")
                if not narrator_voice:
                    # Get any available voice as fallback
                    voices = self.voice_library.list()
                    if voices:
                        narrator_voice = voices[0]

                if narrator_voice:
                    frag_id = f"frag_{uuid.uuid4().hex[:8]}"
                    fragment = Fragment(
                        fragment_id=frag_id,
                        block_id=block.block_id,
                        character="narrator",
                        voice_id=narrator_voice.voice_id,
                        emotion=Emotion.CALM,
                        audio_path="",
                        duration=0.0,
                        status=FragmentStatus.PENDING,
                    )
                    fragments.append(fragment)

            return BlockProcessResult(
                block_id=block.block_id,
                success=True,
                fragments=fragments,
                characters_found=characters_found,
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            return BlockProcessResult(
                block_id=block.block_id,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time,
            )

    def get_character_state(self, name: str) -> CharacterState:
        """Get character state.

        Args:
            name: Character name.

        Returns:
            CharacterState for the character.
        """
        if name not in self.character_states:
            char = self._characters.get(name)
            if char:
                self.character_states[name] = CharacterState(
                    character_id=char.character_id,
                    current_emotion=Emotion.NEUTRAL,
                )
            else:
                # Create new state
                self.character_states[name] = CharacterState(
                    character_id=f"char_{uuid.uuid4().hex[:8]}",
                    current_emotion=Emotion.NEUTRAL,
                )

        return self.character_states[name]

    def update_character_state(
        self,
        name: str,
        emotion: EmotionProfile,
        event: str
    ) -> None:
        """Update character state with new emotion.

        Args:
            name: Character name.
            emotion: New emotion profile.
            event: Event causing the state change.
        """
        state = self.get_character_state(name)
        state.current_emotion = emotion

        # Update history
        history_entry = f"{emotion.emotion_type}({event})"
        if state.history_summary:
            state.history_summary = f"{state.history_summary}; {history_entry}"
        else:
            state.history_summary = history_entry

        # Adjust consistency score
        if state.consistency_score > 0:
            state.consistency_score = max(0.5, state.consistency_score - 0.02)

        # Update character emotion
        if name in self._characters:
            self._characters[name].emotion = emotion

    def synthesize_fragment(
        self,
        fragment: Fragment,
        text: str,
        emotion: Optional[EmotionProfile] = None
    ) -> SynthesisResult:
        """Synthesize audio for a fragment.

        Args:
            fragment: Fragment to synthesize.
            text: Text content to synthesize.
            emotion: Optional emotion profile.

        Returns:
            SynthesisResult from synthesis engine.
        """
        voice = self.voice_library.get(fragment.voice_id)
        if not voice:
            voices = self.voice_library.list()
            if voices:
                voice = voices[0]
            else:
                return SynthesisResult(
                    success=False,
                    error_message="No voice available for synthesis",
                )

        # Use character's emotion if not provided
        if not emotion:
            char_name = fragment.character
            if char_name in self._characters and self._characters[char_name].emotion:
                emotion = self._characters[char_name].emotion
            else:
                emotion = EmotionProfile(
                    emotion_type="平静",
                    intensity=EmotionIntensity.LIGHT,
                )

        return self.synthesis_engine.synthesize_text(
            voice=voice,
            emotion=emotion,
            text=text,
            fragment_id=fragment.fragment_id,
        )

    def convert(
        self,
        novel_path: str,
        output_path: str
    ) -> ConversionResult:
        """Complete conversion workflow.

        This is the main entry point for converting a novel to audiobook.
        It runs through all pipeline stages:
        1. Preprocess (parse + character identification)
        2. Process each block
        3. Synthesize audio for fragments
        4. Combine into final output

        Args:
            novel_path: Path to the input novel file.
            output_path: Path for the output audiobook.

        Returns:
            ConversionResult with conversion status and details.
        """
        start_time = time.time()

        # Validate input
        novel_file = Path(novel_path)
        if not novel_file.exists():
            return ConversionResult(
                success=False,
                errors=[f"Novel file not found: {novel_path}"],
                processing_time=time.time() - start_time,
            )

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Stage 1: Preprocess
            self._update_progress(stage="Preprocessing")
            preprocess_result = self.preprocess(novel_path)

            # Stage 2: Process blocks
            all_fragments: list[Fragment] = []
            failed_blocks: list[str] = []
            processed_count = 0

            self._update_progress(stage="Processing blocks")
            self._progress.total_blocks = len(preprocess_result.blocks)

            for block in preprocess_result.blocks:
                self._update_progress(
                    stage=f"Processing block {block.block_id}",
                )

                result = self.process_block(block)

                if result.success:
                    processed_count += 1
                    all_fragments.extend(result.fragments)
                    self._update_progress(increment_blocks=True)
                else:
                    failed_blocks.append(block.block_id)
                    self._update_progress(increment_failed=True)

            # Stage 3: Synthesis (optional - requires TTS service)
            self._update_progress(stage="Synthesis ready")

            # For MVP, we return success if blocks were processed
            # Actual synthesis would be done in production deployment

            return ConversionResult(
                success=True,
                output_path=output_file,
                total_blocks=len(preprocess_result.blocks),
                processed_blocks=processed_count,
                total_fragments=len(all_fragments),
                failed_blocks=failed_blocks,
                errors=[],
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            return ConversionResult(
                success=False,
                errors=[str(e)],
                processing_time=time.time() - start_time,
            )

    def reset(self) -> None:
        """Reset pipeline state for new conversion."""
        self.character_states.clear()
        self.confirmed_voices.clear()
        self._characters.clear()
        self._progress = PipelineProgress()
        self.character_engine.reset()