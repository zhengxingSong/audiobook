"""Audiobook processing engines package."""

from audiobook.engines.parser import NovelParserEngine
from audiobook.engines.character import CharacterRecognitionEngine, CharacterResult
from audiobook.engines.voice_match import MatchResult, VoiceMatchEngine
from audiobook.engines.synthesis import (
    AudioQuality,
    SynthesisResult,
    VoiceSynthesisEngine,
)

__all__ = [
    "NovelParserEngine",
    "CharacterRecognitionEngine",
    "CharacterResult",
    "MatchResult",
    "VoiceMatchEngine",
    "VoiceSynthesisEngine",
    "SynthesisResult",
    "AudioQuality",
]