import json
import socket
import urllib.error

import pytest

from proofread_app.engine import (
    LOCAL_LLM_UNAVAILABLE_MESSAGE,
    LocalLLMConfigurationError,
    LocalLLMUnavailable,
    OllamaBackend,
    proofread_text,
)
from proofread_app.settings import AppSettings


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_ollama_backend_posts_to_local_generate_endpoint(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"response": "The quick fox jumps."})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = proofread_text(
        "teh quick fox jumps",
        "Standard",
        AppSettings("http://localhost:11434", "llama3.2:3b", 12.5),
    )

    assert result == "The quick fox jumps."
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["timeout"] == 12.5
    assert captured["payload"]["model"] == "llama3.2:3b"
    assert captured["payload"]["stream"] is False
    assert "Return only the corrected text." in captured["payload"]["prompt"]
    assert "teh quick fox jumps" in captured["payload"]["prompt"]


def test_ollama_backend_uses_configured_endpoint_model_and_timeout(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"response": "Done"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    backend = OllamaBackend(AppSettings("http://127.0.0.1:11500/", "mistral", 4))

    assert backend.proofread("done", "Business") == "Done"
    assert captured["url"] == "http://127.0.0.1:11500/api/generate"
    assert captured["payload"]["model"] == "mistral"
    assert captured["timeout"] == 4


def test_ollama_backend_fails_gracefully_when_ollama_is_not_running(monkeypatch):
    def fake_urlopen(request, timeout):
        raise urllib.error.URLError(ConnectionRefusedError("refused"))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    with pytest.raises(LocalLLMUnavailable, match=LOCAL_LLM_UNAVAILABLE_MESSAGE):
        proofread_text("hello", settings=AppSettings(ollama_timeout=0.1))


def test_ollama_backend_fails_gracefully_on_timeout(monkeypatch):
    def fake_urlopen(request, timeout):
        raise socket.timeout("timed out")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    with pytest.raises(LocalLLMUnavailable, match=LOCAL_LLM_UNAVAILABLE_MESSAGE):
        proofread_text("hello", settings=AppSettings(ollama_timeout=0.1))


def test_ollama_backend_rejects_non_local_endpoints():
    with pytest.raises(LocalLLMConfigurationError, match="localhost"):
        proofread_text("do not upload", settings=AppSettings("https://example.com", "llama3.2:3b", 10))
