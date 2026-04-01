"""FastAPI application for the audiobook web service."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from audiobook import __version__
from audiobook.config import load_config
from audiobook.models import Voice
from audiobook.repositories import JobRepository
from audiobook.schemas.voices import VoiceResponse
from audiobook.services import AudiobookConversionRunner, JobService
from audiobook.storage import VoiceLibrary
from audiobook.utils.progress import generate_sse_events_async


WEB_ROOT = Path(__file__).resolve().parent
STATIC_DIR = WEB_ROOT / "static"
TEMPLATES_DIR = WEB_ROOT / "templates"


def _load_html(template_name: str, **replacements: str) -> str:
    """Load a HTML template and apply placeholder replacements."""
    html = (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
    merged = {"__APP_VERSION__": __version__, **replacements}
    for key, value in merged.items():
        html = html.replace(key, value)
    return html


def _voice_library_path(provided: Optional[Path]) -> Path:
    """Resolve the voice-library directory."""
    if provided is not None:
        return Path(provided)
    return Path.home() / ".audiobook" / "voices"


def _serialize_job(record) -> dict:
    """Serialize a job record for JSON responses."""
    return record.model_dump(mode="json")


def create_app(
    job_service: Optional[JobService] = None,
    output_root: Optional[Path] = None,
    voice_library_path: Optional[Path] = None,
    run_jobs_inline: bool = False,
) -> FastAPI:
    """Create the FastAPI application."""
    config = load_config()
    service_output_root = Path(output_root or config.output.output_dir)
    jobs_root = service_output_root / "jobs"
    resolved_voice_library = _voice_library_path(voice_library_path)

    if job_service is None:
        repository = JobRepository(jobs_root)
        runner = AudiobookConversionRunner(
            voice_library_path=resolved_voice_library,
            repository=repository,
        )
        job_service = JobService(
            repository=repository,
            runner=runner,
            run_inline=run_jobs_inline,
        )

    app = FastAPI(
        title="Audiobook Converter Web Service",
        version=__version__,
        description="Monitoring and control surface for audiobook conversion jobs.",
    )
    app.state.job_service = job_service
    app.state.trackers = job_service.tracker_summary()
    app.state.output_root = service_output_root
    app.state.voice_library_path = resolved_voice_library
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    @app.get("/dashboard")
    async def dashboard() -> HTMLResponse:
        return HTMLResponse(_load_html("dashboard.html"))

    @app.get("/jobs")
    async def jobs_page() -> HTMLResponse:
        return HTMLResponse(_load_html("jobs.html"))

    @app.get("/jobs/{job_id}")
    async def job_detail_page(job_id: str) -> HTMLResponse:
        html = _load_html("job_detail.html", __JOB_ID__=job_id)
        return HTMLResponse(html)

    @app.get("/voices")
    async def voices_page() -> HTMLResponse:
        return HTMLResponse(_load_html("voices.html"))

    @app.get("/api")
    async def api_root() -> dict:
        return {
            "service": "audiobook-web",
            "version": __version__,
            "status": "ok",
            "endpoints": {
                "dashboard": "/",
                "health": "/health",
                "system_checks": "/api/system/checks",
                "jobs": "/api/jobs",
                "voices": "/api/voices",
            },
        }

    @app.get("/health")
    async def health() -> dict:
        active_jobs = sum(
            1
            for job in app.state.job_service.list_jobs()
            if job.status.value in {"pending", "running"}
        )
        return {
            "status": "ok",
            "service": "audiobook-web",
            "version": __version__,
            "active_jobs": active_jobs,
        }

    @app.get("/api/system/checks")
    async def system_checks() -> dict:
        output_root_path = Path(app.state.output_root)
        output_root_path.mkdir(parents=True, exist_ok=True)
        probe_path = output_root_path / ".web-healthcheck"
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink(missing_ok=True)

        voice_library = VoiceLibrary(str(app.state.voice_library_path))
        try:
            voice_count = voice_library.count()
        finally:
            voice_library.close()

        return {
            "status": "ok",
            "checks": {
                "output_root": {
                    "ok": True,
                    "path": str(output_root_path),
                },
                "voice_library": {
                    "ok": True,
                    "path": str(app.state.voice_library_path),
                    "count": voice_count,
                },
                "tts_endpoint": {
                    "ok": True,
                    "note": "Use demo://tone for built-in local synthesis, or provide a live GPT-SoVITS HTTP endpoint.",
                },
            },
        }

    @app.get("/api/jobs")
    async def list_jobs() -> dict:
        jobs = [_serialize_job(job) for job in app.state.job_service.list_jobs()]
        return {"jobs": jobs, "count": len(jobs)}

    @app.post("/api/jobs")
    async def create_job(
        novel_path: Optional[str] = Form(default=None),
        output_name: Optional[str] = Form(default=None),
        tts_endpoint: str = Form(default="demo://tone"),
        novel_file: Optional[UploadFile] = File(default=None),
    ) -> JSONResponse:
        if novel_file is None and not novel_path:
            raise HTTPException(status_code=400, detail="Provide either novel_file or novel_path.")

        try:
            if novel_file is not None:
                record = app.state.job_service.create_job_from_upload(
                    filename=novel_file.filename or "novel.txt",
                    data=await novel_file.read(),
                    output_name=output_name,
                    tts_endpoint=tts_endpoint,
                )
            else:
                record = app.state.job_service.create_job_from_path(
                    input_path=Path(novel_path),
                    output_name=output_name,
                    tts_endpoint=tts_endpoint,
                )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        return JSONResponse(_serialize_job(record), status_code=201)

    @app.get("/api/jobs/{job_id}")
    async def get_job(job_id: str) -> dict:
        try:
            record = app.state.job_service.get_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found")
        return _serialize_job(record)

    @app.get("/api/jobs/{job_id}/stream")
    async def stream_job(job_id: str) -> StreamingResponse:
        tracker = app.state.trackers.get(job_id)
        if tracker is None:
            raise HTTPException(status_code=404, detail="Job not found")

        async def event_generator():
            async for event in generate_sse_events_async(tracker):
                yield event

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/api/jobs/{job_id}/report")
    async def get_job_report(job_id: str) -> dict:
        try:
            return app.state.job_service.get_report(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Report not found") from exc

    @app.get("/api/jobs/{job_id}/errors")
    async def get_job_errors(job_id: str) -> dict:
        try:
            record = app.state.job_service.get_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc
        return {"job_id": record.job_id, "errors": record.errors}

    @app.get("/api/jobs/{job_id}/result")
    async def get_job_result(job_id: str) -> FileResponse:
        try:
            result_path = app.state.job_service.get_result_path(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Result file not found") from exc
        return FileResponse(result_path)

    @app.post("/api/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str) -> dict:
        try:
            record = app.state.job_service.cancel_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _serialize_job(record)

    @app.post("/api/jobs/{job_id}/retry")
    async def retry_job(job_id: str) -> JSONResponse:
        try:
            record = app.state.job_service.retry_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return JSONResponse(_serialize_job(record), status_code=201)

    @app.get("/api/voices")
    async def list_voices() -> dict:
        library = VoiceLibrary(str(app.state.voice_library_path))
        try:
            voices = [VoiceResponse.from_voice(voice).model_dump(mode="json") for voice in library.list()]
        finally:
            library.close()
        return {"voices": voices, "count": len(voices)}

    @app.get("/api/voices/{voice_id}")
    async def get_voice(voice_id: str) -> dict:
        library = VoiceLibrary(str(app.state.voice_library_path))
        try:
            voice = library.get(voice_id)
        finally:
            library.close()
        if voice is None:
            raise HTTPException(status_code=404, detail="Voice not found")
        return VoiceResponse.from_voice(voice).model_dump(mode="json")

    @app.post("/api/voices")
    async def create_voice(
        audio_file: UploadFile = File(...),
        name: str = Form(...),
        gender: str = Form(...),
        age_range: str = Form(...),
        tags: str = Form(default=""),
        description: str = Form(default=""),
    ) -> JSONResponse:
        library = VoiceLibrary(str(app.state.voice_library_path))
        try:
            voice_id = f"voice_{uuid.uuid4().hex[:10]}"
            suffix = Path(audio_file.filename or "sample.wav").suffix or ".wav"
            audio_target = Path(app.state.voice_library_path) / "audio" / f"{voice_id}{suffix}"
            audio_target.parent.mkdir(parents=True, exist_ok=True)
            audio_target.write_bytes(await audio_file.read())

            voice = Voice(
                voice_id=voice_id,
                name=name,
                gender=gender,  # type: ignore[arg-type]
                age_range=age_range,
                tags=[item.strip() for item in tags.split(",") if item.strip()],
                description=description,
                audio_path=str(audio_target),
            )
            library.add(voice)
        finally:
            library.close()

        return JSONResponse(
            VoiceResponse.from_voice(voice).model_dump(mode="json"),
            status_code=201,
        )

    @app.delete("/api/voices/{voice_id}")
    async def delete_voice(voice_id: str) -> dict:
        library = VoiceLibrary(str(app.state.voice_library_path))
        try:
            voice = library.get(voice_id)
            if voice is None:
                raise HTTPException(status_code=404, detail="Voice not found")
            library.delete(voice_id)
        finally:
            library.close()

        audio_path = Path(voice.audio_path)
        if audio_path.exists():
            audio_path.unlink()
        return {"deleted": True, "voice_id": voice_id}

    return app
