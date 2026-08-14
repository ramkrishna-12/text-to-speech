import os
from pathlib import Path

# Base directory for generated audio files (ephemeral - ECS/K8s containers are stateless,
# so this is ONLY a short-lived cache before the file is streamed back to the client)
AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "/tmp/audio"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "5000"))

# CORS - tighten this to your real frontend origin(s) in production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
