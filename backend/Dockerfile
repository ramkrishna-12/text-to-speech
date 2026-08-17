# ---------- Stage 1: build dependencies in an isolated venv ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Build-time only deps (gcc etc. needed to compile some wheels) - never shipped in final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: minimal runtime image ----------
FROM python:3.12-slim AS runtime

# Only runtime OS deps: curl for the HEALTHCHECK, ca-certificates for gTTS's HTTPS calls
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/false --create-home appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AUDIO_DIR=/tmp/audio

WORKDIR /app
COPY app ./app

RUN mkdir -p /tmp/audio && chown -R appuser:appuser /app /tmp/audio

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
