import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import ALLOWED_ORIGINS, AUDIO_DIR, APP_VERSION
from app.models import ConvertRequest, ConvertResponse, VoiceOut, HealthOut
from app import tts_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tts_api")

app = FastAPI(
    title="Text-to-Speech API",
    description="Converts text to speech (.mp3) using gTTS, with selectable voices.",
    version=APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exposes GET /metrics in Prometheus text format (request counts, latency histograms, etc.)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/health", response_model=HealthOut, tags=["ops"])
def health():
    """Liveness/readiness probe target for ALB / ECS / Kubernetes."""
    return {"status": "ok", "version": APP_VERSION}


@app.get("/voices", response_model=list[VoiceOut], tags=["tts"])
def get_voices():
    return tts_service.list_voices()


@app.post("/convert", response_model=ConvertResponse, tags=["tts"])
def convert(payload: ConvertRequest):
    try:
        filename, _ = tts_service.synthesize(payload.text, payload.voice_id)
    except tts_service.UnknownVoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except tts_service.TTSGenerationError as exc:
        raise HTTPException(status_code=502, detail=f"TTS generation failed: {exc}")

    audio_id = Path(filename).stem
    return ConvertResponse(
        audio_id=audio_id,
        download_url=f"/audio/{audio_id}?download=true",
        preview_url=f"/audio/{audio_id}",
    )


@app.get("/audio/{audio_id}", tags=["tts"])
def get_audio(audio_id: str, download: bool = Query(default=False)):
    # audio_id must be a bare uuid4 hex - reject anything else to prevent path traversal
    if not audio_id.isalnum():
        raise HTTPException(status_code=400, detail="Invalid audio id")

    filepath = (AUDIO_DIR / f"{audio_id}.mp3").resolve()
    if AUDIO_DIR.resolve() not in filepath.parents or not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio not found")

    delete_after_send = BackgroundTask(_cleanup, filepath) if download else None
    return FileResponse(
        path=filepath,
        media_type="audio/mpeg",
        filename=f"{audio_id}.mp3" if download else None,
        background=delete_after_send,
    )


def _cleanup(path: Path):
    try:
        path.unlink(missing_ok=True)
    except Exception:
        logger.warning("Failed to clean up temp audio file: %s", path)
