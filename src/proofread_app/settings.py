"""Application settings for local proofreading backends."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_OLLAMA_ENDPOINT = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2:3b"
DEFAULT_OLLAMA_TIMEOUT = 30.0


@dataclass(frozen=True)
class AppSettings:
    """Configurable local LLM settings."""

    ollama_endpoint: str = DEFAULT_OLLAMA_ENDPOINT
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    ollama_timeout: float = DEFAULT_OLLAMA_TIMEOUT

    def normalized(self) -> "AppSettings":
        """Return settings with whitespace trimmed and safe defaults applied."""

        endpoint = self.ollama_endpoint.strip().rstrip("/") or DEFAULT_OLLAMA_ENDPOINT
        model = self.ollama_model.strip() or DEFAULT_OLLAMA_MODEL
        timeout = self.ollama_timeout if self.ollama_timeout > 0 else DEFAULT_OLLAMA_TIMEOUT
        return AppSettings(endpoint, model, timeout)


class SettingsError(ValueError):
    """Raised when settings cannot be parsed or validated."""


def default_settings_path() -> Path:
    """Return the per-user settings file path."""

    app_data = os.environ.get("APPDATA")
    if app_data:
        return Path(app_data) / "Proofread App" / "settings.json"
    return Path.home() / ".proofread_app" / "settings.json"


def load_settings(path: Path | None = None) -> AppSettings:
    """Load settings from disk, returning defaults when no file exists."""

    settings_path = path or default_settings_path()
    if not settings_path.exists():
        return AppSettings()

    with settings_path.open("r", encoding="utf-8") as settings_file:
        payload = json.load(settings_file)

    return AppSettings(
        ollama_endpoint=str(payload.get("ollama_endpoint", DEFAULT_OLLAMA_ENDPOINT)),
        ollama_model=str(payload.get("ollama_model", DEFAULT_OLLAMA_MODEL)),
        ollama_timeout=_parse_timeout(payload.get("ollama_timeout", DEFAULT_OLLAMA_TIMEOUT)),
    ).normalized()


def save_settings(settings: AppSettings, path: Path | None = None) -> AppSettings:
    """Save settings to disk and return the normalized settings that were saved."""

    normalized = settings.normalized()
    settings_path = path or default_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with settings_path.open("w", encoding="utf-8") as settings_file:
        json.dump(asdict(normalized), settings_file, indent=2)
    return normalized


def parse_settings(endpoint: str, model: str, timeout: str) -> AppSettings:
    """Parse raw settings field values from the UI."""

    return AppSettings(endpoint, model, _parse_timeout(timeout)).normalized()


def _parse_timeout(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise SettingsError("Timeout must be a number of seconds.") from exc
    if parsed <= 0:
        raise SettingsError("Timeout must be greater than zero.")
    return parsed
