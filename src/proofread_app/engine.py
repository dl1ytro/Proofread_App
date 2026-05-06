"""Local LLM proofreading helpers backed by Ollama."""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from .profiles import DEFAULT_TEMPERATURE, ProofreadingProfile, find_profile
from .prompt_builder import build_prompt
from .settings import AppSettings

LOCAL_LLM_UNAVAILABLE_MESSAGE = "Ollama is not running. Start Ollama, then try again."
LOCAL_LLM_TIMEOUT_MESSAGE = "Ollama took too long to respond. Try a shorter text, a smaller model, or increase the timeout."
LOCAL_LLM_MISSING_MODEL_MESSAGE = "The selected Ollama model is not installed. Pull the model or choose one that is installed."
EMPTY_INPUT_MESSAGE = "Add text before proofreading."
EMPTY_RESPONSE_MESSAGE = "Ollama returned an empty response. Try again, or choose a different model."


class LocalLLMUnavailable(RuntimeError):
    """Raised when the local Ollama service cannot be reached."""


class LocalLLMConfigurationError(ValueError):
    """Raised when local LLM settings would send text outside the machine."""


class EmptyProofreadingInput(ValueError):
    """Raised when proofreading is requested without any text."""


class ProofreadingBackend(Protocol):
    """Backend interface for offline proofreading providers."""

    def proofread(self, text: str, profile: str | ProofreadingProfile) -> str:
        """Return corrected text for the selected profile."""


@dataclass(frozen=True)
class OllamaBackend:
    """Proofreading backend that talks to a local Ollama server."""

    settings: AppSettings

    def proofread(self, text: str, profile: str | ProofreadingProfile) -> str:
        if not text.strip():
            raise EmptyProofreadingInput(EMPTY_INPUT_MESSAGE)

        settings = self.settings.normalized()
        endpoint = _validate_local_endpoint(settings.ollama_endpoint)
        selected_profile = _resolve_profile(profile)
        payload = {
            "model": settings.ollama_model,
            "prompt": build_prompt(text, selected_profile),
            "stream": False,
            "options": {"temperature": _profile_temperature(selected_profile)},
        }
        request = urllib.request.Request(
            f"{endpoint}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=settings.ollama_timeout) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (TimeoutError, socket.timeout) as exc:
            raise LocalLLMUnavailable(LOCAL_LLM_TIMEOUT_MESSAGE) from exc
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise LocalLLMUnavailable(f"{LOCAL_LLM_MISSING_MODEL_MESSAGE} Model: {settings.ollama_model}") from exc
            raise LocalLLMUnavailable(_http_error_message(exc)) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise LocalLLMUnavailable(LOCAL_LLM_TIMEOUT_MESSAGE) from exc
            raise LocalLLMUnavailable(LOCAL_LLM_UNAVAILABLE_MESSAGE) from exc
        except ConnectionError as exc:
            raise LocalLLMUnavailable(LOCAL_LLM_UNAVAILABLE_MESSAGE) from exc
        except json.JSONDecodeError as exc:
            raise LocalLLMUnavailable("Ollama returned an unreadable response. Try again, or restart Ollama.") from exc

        result = str(response_payload.get("response", "")).strip()
        if not result:
            raise LocalLLMUnavailable(EMPTY_RESPONSE_MESSAGE)
        return result


def proofread_text(
    text: str, profile: str | ProofreadingProfile = "Email", settings: AppSettings | None = None
) -> str:
    """Proofread *text* offline with the configured local Ollama model."""

    backend = OllamaBackend(settings or AppSettings())
    return backend.proofread(text, profile)


def _resolve_profile(profile: str | ProofreadingProfile) -> ProofreadingProfile:
    if isinstance(profile, ProofreadingProfile):
        return profile.normalized()
    return find_profile(profile)


def _profile_temperature(profile: ProofreadingProfile) -> float:
    return DEFAULT_TEMPERATURE if profile.temperature is None else profile.temperature


def _validate_local_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise LocalLLMConfigurationError("Ollama endpoint must be an HTTP URL on this computer.")

    host = parsed.hostname.lower()
    if host not in {"localhost", "127.0.0.1", "::1"}:
        raise LocalLLMConfigurationError("Ollama endpoint must point to localhost to keep text processing offline.")

    return endpoint.rstrip("/")


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    details = exc.reason or exc.msg
    if details:
        return f"Ollama returned an error ({exc.code}): {details}"
    return f"Ollama returned an error ({exc.code})."
