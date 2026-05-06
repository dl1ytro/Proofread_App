import json
import socket
import urllib.error

import pytest

from proofread_app.engine import (
    EMPTY_INPUT_MESSAGE,
    EMPTY_RESPONSE_MESSAGE,
    LOCAL_LLM_MISSING_MODEL_MESSAGE,
    LOCAL_LLM_TIMEOUT_MESSAGE,
    LOCAL_LLM_UNAVAILABLE_MESSAGE,
    EmptyProofreadingInput,
    LocalLLMConfigurationError,
    LocalLLMUnavailable,
    OllamaBackend,
    proofread_text,
)
from proofread_app.settings import AppSettings
from proofread_app.profiles import ProofreadingProfile


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
    assert captured["payload"]["options"] == {"temperature": 0.1}
    assert "Return only the corrected text unless the profile requests explanations." in captured["payload"]["prompt"]
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
    assert captured["payload"]["options"] == {"temperature": 0.1}
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

    with pytest.raises(LocalLLMUnavailable, match=LOCAL_LLM_TIMEOUT_MESSAGE):
        proofread_text("hello", settings=AppSettings(ollama_timeout=0.1))


def test_ollama_backend_rejects_non_local_endpoints():
    with pytest.raises(LocalLLMConfigurationError, match="localhost"):
        proofread_text("do not upload", settings=AppSettings("https://example.com", "llama3.2:3b", 10))


def test_ollama_backend_uses_profile_system_message_settings(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"response": "Done"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    profile = ProofreadingProfile(
        "Release Notes",
        "Proof release notes.",
        "Use concise product-release language.",
        temperature=0.35,
        explain_changes=True,
        preserve_tone=False,
    )

    result = proofread_text("fixed bug", profile, AppSettings("http://localhost:11434", "mistral", 5))

    assert result == "Done"
    assert captured["payload"]["options"] == {"temperature": 0.35}
    assert "Use concise product-release language." in captured["payload"]["prompt"]
    assert "Return the corrected text followed by a concise explanation" in captured["payload"]["prompt"]
    assert "You may adjust tone" in captured["payload"]["prompt"]


def test_ollama_backend_rejects_empty_input_before_request(monkeypatch):
    def fake_urlopen(request, timeout):
        raise AssertionError("empty text should not be sent to Ollama")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    with pytest.raises(EmptyProofreadingInput, match=EMPTY_INPUT_MESSAGE):
        proofread_text("   ", settings=AppSettings(ollama_timeout=0.1))


def test_ollama_backend_reports_missing_model(monkeypatch):
    def fake_urlopen(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 404, "model not found", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    with pytest.raises(LocalLLMUnavailable, match=LOCAL_LLM_MISSING_MODEL_MESSAGE):
        proofread_text("hello", settings=AppSettings(ollama_model="missing-model"))


def test_ollama_backend_reports_empty_llm_response(monkeypatch):
    def fake_urlopen(request, timeout):
        return FakeResponse({"response": "  "})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    with pytest.raises(LocalLLMUnavailable, match=EMPTY_RESPONSE_MESSAGE):
        proofread_text("hello", settings=AppSettings())
