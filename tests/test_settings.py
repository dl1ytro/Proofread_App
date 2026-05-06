import json

import pytest

from proofread_app.settings import (
    AppSettings,
    DEFAULT_OLLAMA_ENDPOINT,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_TIMEOUT,
    SettingsError,
    load_settings,
    parse_settings,
    save_settings,
)


def test_load_settings_returns_defaults_when_file_is_missing(tmp_path):
    settings = load_settings(tmp_path / "missing.json")

    assert settings == AppSettings(DEFAULT_OLLAMA_ENDPOINT, DEFAULT_OLLAMA_MODEL, DEFAULT_OLLAMA_TIMEOUT)


def test_save_and_load_settings_round_trip(tmp_path):
    settings_path = tmp_path / "settings.json"

    saved = save_settings(AppSettings("http://localhost:11500/", "llama3.2:3b", 45), settings_path)
    loaded = load_settings(settings_path)

    assert saved == AppSettings("http://localhost:11500", "llama3.2:3b", 45)
    assert loaded == saved
    assert json.loads(settings_path.read_text())["ollama_model"] == "llama3.2:3b"


def test_parse_settings_validates_timeout():
    with pytest.raises(SettingsError, match="number"):
        parse_settings("http://localhost:11434", "llama3.2:3b", "slow")

    with pytest.raises(SettingsError, match="greater than zero"):
        parse_settings("http://localhost:11434", "llama3.2:3b", "0")
