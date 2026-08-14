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