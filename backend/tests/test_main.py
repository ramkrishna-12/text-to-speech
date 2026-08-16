from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_list_voices():
    resp = client.get("/voices")
    assert resp.status_code == 200
    voices = resp.json()
    assert isinstance(voices, list)
    assert any(v["id"] == "en-us" for v in voices)


def test_convert_rejects_unknown_voice():
    resp = client.post("/convert", json={"text": "hello world", "voice_id": "not-a-voice"})
    assert resp.status_code == 400


def test_convert_rejects_empty_text():
    resp = client.post("/convert", json={"text": "", "voice_id": "en-us"})
    assert resp.status_code == 422  # pydantic min_length validation


@patch("app.main.tts_service.synthesize")
def test_convert_success_returns_urls(mock_synth, tmp_path):
    fake_file = tmp_path / "abc123.mp3"
    fake_file.write_bytes(b"ID3fake-mp3-bytes")
    mock_synth.return_value = ("abc123.mp3", fake_file)

    resp = client.post("/convert", json={"text": "hello", "voice_id": "en-us"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["audio_id"] == "abc123"
    assert body["preview_url"] == "/audio/abc123"
    assert body["download_url"] == "/audio/abc123?download=true"


def test_get_audio_rejects_path_traversal():
    resp = client.get("/audio/..%2F..%2Fetc%2Fpasswd")
    assert resp.status_code in (400, 404)


def test_get_audio_not_found():
    resp = client.get("/audio/doesnotexist1234")
    assert resp.status_code == 404
