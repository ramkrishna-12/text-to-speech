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