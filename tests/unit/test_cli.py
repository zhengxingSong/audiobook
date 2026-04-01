"""Tests for CLI commands."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from audiobook.cli import main
from audiobook.config import AppConfig
from audiobook.models import Voice


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_home() -> Generator[Path, None, None]:
    """Create a temporary home directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_novel_file(temp_dir: Path) -> Path:
    """Create a sample novel file for testing."""
    novel_path = temp_dir / "novel.txt"
    novel_path.write_text(
        "第一章 开始\n\n"
        "这是一个测试小说。\n\n"
        "小明说：你好！\n\n"
        "小红回答：你好，小明！\n",
        encoding="utf-8",
    )
    return novel_path


@pytest.fixture
def temp_audio_file(temp_dir: Path) -> Path:
    """Create a sample audio file for testing."""
    audio_path = temp_dir / "sample.wav"
    # Create a minimal valid WAV file header
    audio_path.write_bytes(
        b"RIFF" + b"\x24\x00\x00\x00" + b"WAVE" +
        b"fmt " + b"\x10\x00\x00\x00" + b"\x01\x00\x01\x00" +
        b"\x44\xac\x00\x00" + b"\x88\x58\x01\x00" + b"\x02\x00\x10\x00" +
        b"data" + b"\x08\x00\x00\x00" + b"\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    return audio_path


class TestMainCommand:
    """Tests for main CLI command."""

    def test_version(self, cli_runner: CliRunner) -> None:
        """Test --version flag."""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self, cli_runner: CliRunner) -> None:
        """Test --help flag."""
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Audiobook Converter" in result.output
        assert "convert" in result.output
        assert "voice" in result.output
        assert "init" in result.output


class TestInitCommand:
    """Tests for init command."""

    def test_init_creates_directories(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test init command creates required directories."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        result = cli_runner.invoke(main, ["init"])

        assert result.exit_code == 0
        assert "Initialization complete" in result.output

        # Check directories were created
        voice_path = temp_home / ".audiobook" / "voices"
        assert voice_path.exists()

    def test_init_creates_config_file(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test init command creates config file."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        result = cli_runner.invoke(main, ["init"])

        assert result.exit_code == 0

        config_path = temp_home / ".audiobook" / "config.yaml"
        assert config_path.exists()


class TestConvertCommand:
    """Tests for convert command."""

    def test_convert_basic(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        temp_novel_file: Path,
        temp_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test basic convert command."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        # Mock pipeline
        with patch("audiobook.cli.AudiobookPipeline") as mock_pipeline_class:
            with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
                mock_library = MagicMock()
                mock_library.count.return_value = 0
                mock_library_class.return_value = mock_library

                mock_pipeline = MagicMock()
                mock_pipeline.convert.return_value = MagicMock(
                    success=True,
                    output_path=temp_dir / "output.mp3",
                    total_blocks=10,
                    processed_blocks=10,
                    total_fragments=10,
                    errors=[],
                )
                mock_pipeline_class.return_value = mock_pipeline

                output_path = temp_dir / "output.mp3"

                result = cli_runner.invoke(
                    main,
                    ["convert", str(temp_novel_file), "-o", str(output_path)],
                )

                assert result.exit_code == 1
                assert "Conversion failed" in result.output
                assert "Output file was not created" in result.output

    def test_convert_with_tts_endpoint(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        temp_novel_file: Path,
        temp_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test convert command with custom TTS endpoint."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.AudiobookPipeline") as mock_pipeline_class:
            with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
                mock_library = MagicMock()
                mock_library.count.return_value = 0
                mock_library_class.return_value = mock_library

                mock_pipeline = MagicMock()
                mock_pipeline.convert.return_value = MagicMock(
                    success=True,
                    output_path=temp_dir / "output.mp3",
                    total_blocks=5,
                    processed_blocks=5,
                    total_fragments=5,
                    errors=[],
                )
                mock_pipeline_class.return_value = mock_pipeline

                output_path = temp_dir / "output.mp3"
                custom_endpoint = "http://custom-tts:8080"

                result = cli_runner.invoke(
                    main,
                    ["convert", str(temp_novel_file), "-o", str(output_path),
                     "--tts-endpoint", custom_endpoint],
                )

                assert result.exit_code == 1
                # Verify the endpoint was used
                mock_pipeline_class.assert_called_once()
                call_kwargs = mock_pipeline_class.call_args.kwargs
                assert call_kwargs["tts_endpoint"] == custom_endpoint

    def test_convert_succeeds_when_output_exists(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        temp_novel_file: Path,
        temp_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test convert reports success only when the output file exists."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        output_path = temp_dir / "output.mp3"
        output_path.write_bytes(b"fake-audio")

        with patch("audiobook.cli.AudiobookPipeline") as mock_pipeline_class:
            with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
                mock_library = MagicMock()
                mock_library.count.return_value = 0
                mock_library_class.return_value = mock_library

                mock_pipeline = MagicMock()
                mock_pipeline.convert.return_value = MagicMock(
                    success=True,
                    output_path=output_path,
                    total_blocks=10,
                    processed_blocks=10,
                    total_fragments=10,
                    errors=[],
                )
                mock_pipeline_class.return_value = mock_pipeline

                result = cli_runner.invoke(
                    main,
                    ["convert", str(temp_novel_file), "-o", str(output_path)],
                )

                assert result.exit_code == 0
                assert "Conversion complete" in result.output

    def test_convert_fails_on_missing_file(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        temp_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test convert fails when novel file does not exist."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        result = cli_runner.invoke(
            main,
            ["convert", str(temp_dir / "nonexistent.txt"), "-o", str(temp_dir / "output.mp3")],
        )

        # Click should fail because file doesn't exist (type=click.Path(exists=True))
        assert result.exit_code != 0

    def test_convert_handles_pipeline_error(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        temp_novel_file: Path,
        temp_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test convert handles pipeline errors."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.AudiobookPipeline") as mock_pipeline_class:
            with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
                mock_library = MagicMock()
                mock_library.count.return_value = 0
                mock_library_class.return_value = mock_library

                mock_pipeline = MagicMock()
                mock_pipeline.convert.return_value = MagicMock(
                    success=False,
                    output_path=None,
                    total_blocks=0,
                    processed_blocks=0,
                    total_fragments=0,
                    errors=["Test error occurred"],
                )
                mock_pipeline_class.return_value = mock_pipeline

                output_path = temp_dir / "output.mp3"

                result = cli_runner.invoke(
                    main,
                    ["convert", str(temp_novel_file), "-o", str(output_path)],
                )

                assert result.exit_code == 1
                assert "Conversion failed" in result.output


class TestVoiceCommands:
    """Tests for voice subcommands."""

    def test_voice_list_empty(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test voice list when library is empty."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
            mock_library = MagicMock()
            mock_library.list.return_value = []
            mock_library_class.return_value = mock_library

            result = cli_runner.invoke(main, ["voice", "list"])

            assert result.exit_code == 0
            assert "No voices found" in result.output

    def test_voice_list_with_voices(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test voice list with existing voices."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
            mock_library = MagicMock()
            mock_library.list.return_value = [
                Voice(
                    voice_id="test-id-1",
                    name="Test Voice 1",
                    gender="女",
                    age_range="青年",
                    tags=["温柔"],
                ),
                Voice(
                    voice_id="test-id-2",
                    name="Test Voice 2",
                    gender="男",
                    age_range="中年",
                    tags=["沉稳"],
                ),
            ]
            mock_library_class.return_value = mock_library

            result = cli_runner.invoke(main, ["voice", "list"])

            assert result.exit_code == 0
            assert "Test Voice 1" in result.output
            assert "Test Voice 2" in result.output

    def test_voice_list_with_filters(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test voice list with gender filter."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
            mock_library = MagicMock()
            mock_library.list.return_value = [
                Voice(
                    voice_id="test-id-1",
                    name="Female Voice",
                    gender="女",
                    age_range="青年",
                    tags=["温柔"],
                ),
            ]
            mock_library_class.return_value = mock_library

            result = cli_runner.invoke(main, ["voice", "list", "--gender", "女"])

            assert result.exit_code == 0
            mock_library.list.assert_called_once_with(gender="女", age_range=None)

    def test_voice_add(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        temp_audio_file: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test adding a voice to library."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
            with patch("uuid.uuid4", return_value=uuid.UUID("00000000-0000-0000-0000-000000000123")):
                with patch("shutil.copy2"):
                    mock_library = MagicMock()
                    mock_library_class.return_value = mock_library

                    result = cli_runner.invoke(
                        main,
                        ["voice", "add", str(temp_audio_file),
                         "--name", "New Voice",
                         "--gender", "女",
                         "--age", "青年",
                         "--tags", "温柔",
                         "--tags", "甜美",
                         "--description", "A test voice"],
                    )

                    assert result.exit_code == 0
                    assert "Voice added successfully" in result.output
                    assert "New Voice" in result.output

                    # Verify voice was added
                    mock_library.add.assert_called_once()
                    added_voice = mock_library.add.call_args.args[0]
                    assert added_voice.name == "New Voice"
                    assert added_voice.gender == "女"
                    assert added_voice.age_range == "青年"
                    assert "温柔" in added_voice.tags
                    assert "甜美" in added_voice.tags

    def test_voice_delete(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test deleting a voice."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
            mock_library = MagicMock()
            mock_library.get.return_value = Voice(
                voice_id="test-id",
                name="Test Voice",
                gender="女",
                age_range="青年",
                audio_path=str(temp_home / "audio.wav"),
            )
            mock_library_class.return_value = mock_library

            result = cli_runner.invoke(main, ["voice", "delete", "test-id"])

            assert result.exit_code == 0
            assert "Deleted voice" in result.output
            mock_library.delete.assert_called_once_with("test-id")

    def test_voice_delete_not_found(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test deleting a voice that doesn't exist."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
            mock_library = MagicMock()
            mock_library.get.return_value = None
            mock_library_class.return_value = mock_library

            result = cli_runner.invoke(main, ["voice", "delete", "nonexistent"])

            assert result.exit_code == 1
            assert "Voice not found" in result.output

    def test_voice_show(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test showing voice details."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
            mock_library = MagicMock()
            mock_library.get.return_value = Voice(
                voice_id="test-id-123",
                name="Test Voice",
                gender="女",
                age_range="青年",
                tags=["温柔", "甜美"],
                description="A beautiful voice",
                audio_path="/path/to/audio.wav",
            )
            mock_library_class.return_value = mock_library

            result = cli_runner.invoke(main, ["voice", "show", "test-id-123"])

            assert result.exit_code == 0
            assert "Test Voice" in result.output
            assert "女" in result.output
            assert "温柔" in result.output

    def test_voice_show_not_found(
        self,
        cli_runner: CliRunner,
        temp_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test showing voice that doesn't exist."""
        monkeypatch.setattr(Path, "home", lambda: temp_home)

        with patch("audiobook.cli.VoiceLibrary") as mock_library_class:
            mock_library = MagicMock()
            mock_library.get.return_value = None
            mock_library_class.return_value = mock_library

            result = cli_runner.invoke(main, ["voice", "show", "nonexistent"])

            assert result.exit_code == 1
            assert "Voice not found" in result.output


class TestConfigOption:
    """Tests for --config option."""

    def test_custom_config_path(
        self,
        cli_runner: CliRunner,
        config_file: Path,
    ) -> None:
        """Test using custom config file."""
        result = cli_runner.invoke(
            main,
            ["--config", str(config_file), "--help"],
        )

        assert result.exit_code == 0


class TestHelpMessages:
    """Tests for help messages."""

    def test_voice_help(self, cli_runner: CliRunner) -> None:
        """Test voice command help."""
        result = cli_runner.invoke(main, ["voice", "--help"])
        assert result.exit_code == 0
        assert "Voice library management" in result.output
        assert "list" in result.output
        assert "add" in result.output

    def test_voice_add_help(self, cli_runner: CliRunner) -> None:
        """Test voice add command help."""
        result = cli_runner.invoke(main, ["voice", "add", "--help"])
        assert result.exit_code == 0
        assert "Add a new voice" in result.output
        assert "--name" in result.output
        assert "--gender" in result.output

    def test_convert_help(self, cli_runner: CliRunner) -> None:
        """Test convert command help."""
        result = cli_runner.invoke(main, ["convert", "--help"])
        assert result.exit_code == 0
        assert "Convert a novel" in result.output
        assert "--output" in result.output
        assert "--tts-endpoint" in result.output
