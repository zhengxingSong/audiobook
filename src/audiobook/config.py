"""Configuration management for audiobook converter.

This module provides centralized configuration management using Pydantic
for validation and settings management. Configuration can be loaded from:
- YAML configuration files
- Environment variables
- Command-line arguments
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class CharacterMatchingConfig(BaseModel):
    """Configuration for character voice matching engine."""

    enabled: bool = Field(default=True, description="Enable character voice matching")
    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold for voice matching",
    )
    max_characters: int = Field(
        default=100,
        ge=1,
        description="Maximum number of characters to track",
    )
    cache_similarities: bool = Field(
        default=True,
        description="Cache voice similarity computations",
    )


class VoiceConfig(BaseModel):
    """Configuration for voice synthesis."""

    default_provider: str = Field(
        default="azure",
        description="Default TTS provider (azure, google, aws, elevenlabs)",
    )
    default_language: str = Field(
        default="zh-CN",
        description="Default language code for synthesis",
    )
    default_voice: str = Field(
        default="zh-CN-XiaoxiaoNeural",
        description="Default voice name",
    )
    speaking_rate: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speaking rate multiplier",
    )
    pitch_adjustment: float = Field(
        default=0.0,
        ge=-50.0,
        le=50.0,
        description="Pitch adjustment in semitones",
    )


class OutputConfig(BaseModel):
    """Configuration for output generation."""

    output_dir: Path = Field(
        default=Path("./output"),
        description="Directory for generated audio files",
    )
    format: str = Field(
        default="mp3",
        description="Output audio format (mp3, wav, ogg)",
    )
    bitrate: str = Field(
        default="192k",
        description="Audio bitrate for compressed formats",
    )
    sample_rate: int = Field(
        default=44100,
        ge=8000,
        le=192000,
        description="Audio sample rate in Hz",
    )
    normalize_audio: bool = Field(
        default=True,
        description="Normalize audio levels",
    )


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format string",
    )
    file_path: Optional[Path] = Field(
        default=None,
        description="Optional log file path",
    )
    console_output: bool = Field(
        default=True,
        description="Output logs to console",
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid logging level: {v}. Must be one of {valid_levels}")
        return v_upper


class AppConfig(BaseModel):
    """Main application configuration.

    This is the root configuration model that contains all sub-configurations
    for the audiobook converter application.
    """

    character_matching: CharacterMatchingConfig = Field(
        default_factory=CharacterMatchingConfig,
        description="Character voice matching configuration",
    )
    voice: VoiceConfig = Field(
        default_factory=VoiceConfig,
        description="Voice synthesis configuration",
    )
    output: OutputConfig = Field(
        default_factory=OutputConfig,
        description="Output generation configuration",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration",
    )

    @classmethod
    def from_yaml(cls, path: Path) -> "AppConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            AppConfig instance populated from the YAML file.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            yaml.YAMLError: If the YAML file is malformed.
            ValidationError: If the configuration values are invalid.
        """
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data or {})

    def to_yaml(self, path: Path) -> None:
        """Save configuration to a YAML file.

        Args:
            path: Path where the YAML configuration will be saved.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and handle Path objects
        data = self.model_dump(mode="python")

        def convert_paths(obj):
            """Recursively convert Path objects to strings."""
            if isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            elif isinstance(obj, Path):
                return str(obj)
            return obj

        data = convert_paths(data)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load application configuration.

    Configuration is loaded in the following order (later sources override earlier):
    1. Default values
    2. Configuration file (if specified)
    3. Environment variables (not yet implemented)

    Args:
        config_path: Optional path to a YAML configuration file.

    Returns:
        AppConfig instance with loaded configuration.
    """
    if config_path and config_path.exists():
        return AppConfig.from_yaml(config_path)
    return AppConfig()


# Default configuration instance
DEFAULT_CONFIG = AppConfig()