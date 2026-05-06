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
from .settings import AppSettings

LOCAL_LLM_UNAVAILABLE_MESSAGE = "Local LLM is not available. Please start Ollama."


class LocalLLMUnavailable(RuntimeError):
    """Raised when the local Ollama service cannot be reached."""


class LocalLLMConfigurationError(ValueError):
    """Raised when local LLM settings would send text outside the machine."""


class ProofreadingBackend(Protocol):
    """Backend interface for offline proofreading providers."""

    def proofread(self, text: str, profile: str | ProofreadingProfile) -> str:
        """Return corrected text for the selected profile."""


@dataclass(frozen=True)
class OllamaBackend:
    """Proofreading backend that talks to a local Ollama server."""

    settings: AppSettings

    def proofread(self, text: str, profile: str | ProofreadingProfile) -> str:
        settings = self.settings.normalized()
        endpoint = _validate_local_endpoint(settings.ollama_endpoint)
        selected_profile = _resolve_profile(profile)
        payload = {
            "model": settings.ollama_model,
            "prompt": _build_prompt(text, selected_profile),
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
        except (TimeoutError, socket.timeout, ConnectionError, urllib.error.URLError) as exc:
            raise LocalLLMUnavailable(LOCAL_LLM_UNAVAILABLE_MESSAGE) from exc
        except json.JSONDecodeError as exc:
            raise LocalLLMUnavailable("Local LLM returned an unreadable response.") from exc

        result = str(response_payload.get("response", "")).strip()
        if not result:
            raise LocalLLMUnavailable("Local LLM returned an empty response.")
        return result


def proofread_text(
    text: str, profile: str | ProofreadingProfile = "Email", settings: AppSettings | None = None
) -> str:
    """Proofread *text* offline with the configured local Ollama model."""

    backend = OllamaBackend(settings or AppSettings())
    return backend.proofread(text, profile)


def _build_prompt(text: str, profile: ProofreadingProfile) -> str:
    response_instruction = (
        "Return the corrected text followed by a concise explanation of the changes."
        if profile.explain_changes
        else "Return only the corrected text."
    )
    tone_instruction = (
        "Preserve the user's tone and meaning." if profile.preserve_tone else "You may adjust tone when it improves the result."
    )
    return (
        "You are an offline proofreading assistant running locally in Ollama. "
        f"{profile.system_message} "
        f"{tone_instruction} "
        "Do not add new facts or change the user's intent. "
        f"{response_instruction}\n\n"
        f"Profile: {profile.name}\n"
        f"Profile guidance: {profile.description}\n\n"
        "Text to proofread:\n"
        f"{text}"
    )


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
