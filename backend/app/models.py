from pydantic import BaseModel, Field
from app.config import MAX_TEXT_LENGTH


class ConvertRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    voice_id: str = Field(default="en-us")


class ConvertResponse(BaseModel):
    audio_id: str
    download_url: str
    preview_url: str


class VoiceOut(BaseModel):
    id: str
    label: str
    lang: str
    tld: str
    slow: bool


class HealthOut(BaseModel):
    status: str
    version: str
