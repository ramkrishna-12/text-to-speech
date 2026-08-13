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


@dataclass(frozen=True)
class Voice:
    id: str
    label: str
    lang: str
    tld: str
    slow: bool = False


# Curated voice presets (id -> Voice). Extend freely; gtts.lang.tts_langs() has 100+ langs.
VOICES: dict[str, Voice] = {
    "en-us": Voice("en-us", "English (US)", "en", "com"),
    "en-uk": Voice("en-uk", "English (UK)", "en", "co.uk"),
    "en-au": Voice("en-au", "English (Australia)", "en", "com.au"),
    "en-in": Voice("en-in", "English (India)", "en", "co.in"),
    "en-us-slow": Voice("en-us-slow", "English (US, Slow)", "en", "com", slow=True),
    "hi-in": Voice("hi-in", "Hindi (India)", "hi", "co.in"),
    "bn-in": Voice("bn-in", "Bengali (India)", "bn", "co.in"),
    "es-es": Voice("es-es", "Spanish (Spain)", "es", "es"),
    "es-mx": Voice("es-mx", "Spanish (Mexico)", "es", "com.mx"),
    "fr-fr": Voice("fr-fr", "French (France)", "fr", "fr"),
    "de-de": Voice("de-de", "German (Germany)", "de", "de"),
    "ja-jp": Voice("ja-jp", "Japanese (Japan)", "ja", "co.jp"),
    "zh-cn": Voice("zh-cn", "Chinese Mandarin (China)", "zh-CN", "com"),
}


class UnknownVoiceError(ValueError):
    pass


class TTSGenerationError(RuntimeError):
    pass


def list_voices() -> list[dict]:
    return [
        {"id": v.id, "label": v.label, "lang": v.lang, "tld": v.tld, "slow": v.slow}
        for v in VOICES.values()
    ]

