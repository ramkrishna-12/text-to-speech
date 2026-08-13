"""
gTTS wraps Google Translate's TTS endpoint. It doesn't offer multiple "voices" per se -
voice variety comes from (lang, tld) combinations, which change the accent, and from
the `slow` flag. This module exposes a curated set of these as named "voices" so the
frontend can offer a simple dropdown instead of raw lang/tld codes.
"""
import uuid
import logging
from dataclasses import dataclass
from gtts import gTTS
from gtts.lang import tts_langs

from app.config import AUDIO_DIR

logger = logging.getLogger("tts_service")
