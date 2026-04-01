"""Command-line interface for audiobook converter."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

from audiobook import __version__
from audiobook.config import AppConfig, load_config
from audiobook.storage import VoiceLibrary
from audiobook.processors import AudiobookPipeline
from audiobook.models import Voice

console = Console()


@click.group()
@click.version_option(version=__version__)
@click.option("--config", "-c", type=click.Path(exists=False), help="Configuration file path")
@click.pass_context
def main(ctx: click.Context, config: Optional[str]) -> None:
    """Audiobook Converter - Convert novels to audiobooks with character voice matching."""
    ctx.ensure_object(dict)
    config_path = Path(config) if config else None
    ctx.obj["config"] = load_config(config_path)


@main.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Initialize configuration and create required directories."""
    config: AppConfig = ctx.obj["config"]

    # Create voice library directory
    voice_library_path = Path.home() / ".audiobook" / "voices"
    voice_library_path.mkdir(parents=True, exist_ok=True)

    # Create default config file if it doesn't exist
    default_config_path = Path.home() / ".audiobook" / "config.yaml"
    if not default_config_path.exists():
        config.to_yaml(default_config_path)
        console.print(f"[green]Created configuration file:[/] {default_config_path}")
    else:
        console.print(f"[yellow]Configuration file already exists:[/] {default_config_path}")

    # Create output directory
    output_dir = config.output.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]Created output directory:[/] {output_dir}")

    console.print(Panel.fit(
        "[bold green]Initialization complete![/]\n\n"
        f"Voice library: {voice_library_path}\n"
        f"Config file: {default_config_path}\n"
        f"Output directory: {output_dir}",
        title="Audiobook Converter",
    ))


@main.command()
@click.argument("novel_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), required=True, help="Output audio file path")
@click.option("--tts-endpoint", default="http://localhost:9880", help="TTS service endpoint URL")
@click.pass_context
def convert(
    ctx: click.Context,
    novel_path: str,
    output: str,
    tts_endpoint: str,
) -> None:
    """Convert a novel to audiobook.

    NOVEL_PATH is the path to the input novel file (txt, epub, etc.).
    """
    config: AppConfig = ctx.obj["config"]

    # Initialize voice library
    voice_library_path = Path.home() / ".audiobook" / "voices"
    voice_library = VoiceLibrary(str(voice_library_path))

    # Check voice library
    voice_count = voice_library.count()
    if voice_count == 0:
        console.print("[yellow]Warning: Voice library is empty. Add voices with 'audiobook voice add' command.[/]")

    # Create pipeline
    pipeline = AudiobookPipeline(
        voice_library=voice_library,
        tts_endpoint=tts_endpoint,
    )

    # Run conversion
    console.print(f"[cyan]Converting:[/] {novel_path}")
    console.print(f"[cyan]Output:[/] {output}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Converting...", total=None)

        result = pipeline.convert(
            novel_path=novel_path,
            output_path=output,
        )

    output_exists = bool(
        result.output_path and Path(result.output_path).exists()
    )

    # Display results
    if result.success and output_exists:
        console.print(Panel.fit(
            f"[bold green]Conversion complete![/]\n\n"
            f"Output: {result.output_path}\n"
            f"Blocks processed: {result.processed_blocks}/{result.total_blocks}\n"
            f"Fragments generated: {result.total_fragments}",
            title="Success",
        ))
    else:
        errors = list(result.errors)
        if result.success and not output_exists:
            missing_output = result.output_path or output
            errors.append(f"Output file was not created: {missing_output}")

        console.print(Panel.fit(
            f"[bold red]Conversion failed![/]\n\n"
            f"Errors:\n" + "\n".join(f"  - {e}" for e in errors),
            title="Error",
        ))
        raise SystemExit(1)


@main.group()
def voice() -> None:
    """Voice library management commands."""
    pass


@voice.command("list")
@click.option("--gender", "-g", type=click.Choice(["男", "女", "中性"]), help="Filter by gender")
@click.option("--age", "-a", help="Filter by age range")
@click.pass_context
def voice_list(ctx: click.Context, gender: Optional[str], age: Optional[str]) -> None:
    """List all voices in the library."""
    voice_library_path = Path.home() / ".audiobook" / "voices"
    voice_library = VoiceLibrary(str(voice_library_path))

    voices = voice_library.list(gender=gender, age_range=age)

    if not voices:
        console.print("[yellow]No voices found in library.[/]")
        console.print("[cyan]Add voices with 'audiobook voice add' command.[/]")
        return

    table = Table(title="Voice Library")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Gender", style="magenta")
    table.add_column("Age Range", style="yellow")
    table.add_column("Tags", style="blue")

    for v in voices:
        table.add_row(
            v.voice_id[:8] + "...",
            v.name,
            v.gender,
            v.age_range,
            ", ".join(v.tags) if v.tags else "-",
        )

    console.print(table)
    console.print(f"\n[cyan]Total voices:[/] {len(voices)}")


@voice.command("add")
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("--name", "-n", required=True, help="Voice name")
@click.option("--gender", "-g", type=click.Choice(["男", "女", "中性"]), required=True, help="Voice gender")
@click.option("--age", "-a", default="青年", help="Age range (default: 青年)")
@click.option("--tags", "-t", multiple=True, help="Tags for the voice")
@click.option("--description", "-d", default="", help="Voice description")
@click.pass_context
def voice_add(
    ctx: click.Context,
    audio_file: str,
    name: str,
    gender: str,
    age: str,
    tags: tuple,
    description: str,
) -> None:
    """Add a new voice to the library from an audio file.

    AUDIO_FILE is the path to the reference audio file for this voice.
    """
    import uuid

    voice_library_path = Path.home() / ".audiobook" / "voices"
    voice_library = VoiceLibrary(str(voice_library_path))

    # Copy audio file to voice library
    audio_path = Path(audio_file)
    voice_id = str(uuid.uuid4())
    target_path = voice_library_path / "audio" / f"{voice_id}{audio_path.suffix}"
    target_path.parent.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy2(audio_path, target_path)

    # Create voice entry
    voice = Voice(
        voice_id=voice_id,
        name=name,
        gender=gender,
        age_range=age,
        tags=list(tags),
        description=description,
        audio_path=str(target_path),
    )

    voice_library.add(voice)

    console.print(Panel.fit(
        f"[bold green]Voice added successfully![/]\n\n"
        f"ID: {voice_id}\n"
        f"Name: {name}\n"
        f"Gender: {gender}\n"
        f"Age Range: {age}\n"
        f"Tags: {', '.join(tags) if tags else 'none'}",
        title="Voice Added",
    ))


@voice.command("delete")
@click.argument("voice_id")
@click.pass_context
def voice_delete(ctx: click.Context, voice_id: str) -> None:
    """Delete a voice from the library.

    VOICE_ID is the ID of the voice to delete.
    """
    voice_library_path = Path.home() / ".audiobook" / "voices"
    voice_library = VoiceLibrary(str(voice_library_path))

    # Check if voice exists
    voice = voice_library.get(voice_id)
    if voice is None:
        console.print(f"[red]Error: Voice not found with ID: {voice_id}[/]")
        raise SystemExit(1)

    # Delete voice
    voice_library.delete(voice_id)

    # Delete audio file if it exists
    if voice.audio_path and Path(voice.audio_path).exists():
        Path(voice.audio_path).unlink()

    console.print(f"[green]Deleted voice: {voice.name}[/]")


@voice.command("show")
@click.argument("voice_id")
@click.pass_context
def voice_show(ctx: click.Context, voice_id: str) -> None:
    """Show detailed information about a voice.

    VOICE_ID is the ID of the voice to show.
    """
    voice_library_path = Path.home() / ".audiobook" / "voices"
    voice_library = VoiceLibrary(str(voice_library_path))

    voice = voice_library.get(voice_id)

    if voice is None:
        console.print(f"[red]Error: Voice not found with ID: {voice_id}[/]")
        raise SystemExit(1)

    console.print(Panel.fit(
        f"[bold cyan]ID:[/] {voice.voice_id}\n"
        f"[bold cyan]Name:[/] {voice.name}\n"
        f"[bold cyan]Gender:[/] {voice.gender}\n"
        f"[bold cyan]Age Range:[/] {voice.age_range}\n"
        f"[bold cyan]Tags:[/] {', '.join(voice.tags) if voice.tags else 'none'}\n"
        f"[bold cyan]Description:[/] {voice.description or 'N/A'}\n"
        f"[bold cyan]Audio Path:[/] {voice.audio_path or 'N/A'}",
        title=f"Voice: {voice.name}",
    ))


if __name__ == "__main__":
    main()
