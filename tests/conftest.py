"""Shared pytest fixtures for audiobook converter tests."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from audiobook.config import AppConfig, CharacterMatchingConfig, VoiceConfig, OutputConfig, LoggingConfig


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files.

    Yields:
        Path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config() -> AppConfig:
    """Create a sample configuration for testing.

    Returns:
        AppConfig with test-friendly defaults.
    """
    return AppConfig(
        character_matching=CharacterMatchingConfig(
            enabled=True,
            similarity_threshold=0.7,
            max_characters=50,
        ),
        voice=VoiceConfig(
            default_provider="azure",
            default_language="zh-CN",
            default_voice="zh-CN-XiaoxiaoNeural",
            speaking_rate=1.0,
        ),
        output=OutputConfig(
            format="mp3",
            bitrate="192k",
            sample_rate=44100,
        ),
        logging=LoggingConfig(
            level="DEBUG",
            console_output=True,
        ),
    )


@pytest.fixture
def config_file(temp_dir: Path, sample_config: AppConfig) -> Path:
    """Create a temporary configuration file.

    Args:
        temp_dir: Temporary directory fixture.
        sample_config: Sample configuration fixture.

    Returns:
        Path to the created configuration file.
    """
    config_path = temp_dir / "config.yaml"
    sample_config.to_yaml(config_path)
    return config_path


@pytest.fixture
def sample_text_file(temp_dir: Path) -> Path:
    """Create a sample text file for testing.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        Path to the sample text file.
    """
    text_path = temp_dir / "sample.txt"
    text_path.write_text(
        "Chapter 1\n\n"
        "The quick brown fox jumps over the lazy dog.\n\n"
        "This is a test paragraph.\n",
        encoding="utf-8",
    )
    return text_path


@pytest.fixture
def sample_yaml_config(temp_dir: Path) -> str:
    """Create a sample YAML configuration string.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        YAML configuration string.
    """
    return """
character_matching:
  enabled: true
  similarity_threshold: 0.8
  max_characters: 100

voice:
  default_provider: azure
  default_language: zh-CN
  default_voice: zh-CN-XiaoxiaoNeural
  speaking_rate: 1.0

output:
  output_dir: ./output
  format: mp3
  bitrate: 192k
  sample_rate: 44100

logging:
  level: INFO
  console_output: true
"""