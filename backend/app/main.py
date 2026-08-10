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