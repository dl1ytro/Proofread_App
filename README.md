# Proofread App

A lightweight desktop proofreading interface designed for Windows 10 and Windows 11. Version 1 is intentionally a small, stable desktop tool. The UI uses Python's standard `tkinter` toolkit, so it avoids accounts, web views, complex navigation, and unnecessary animations.

Proofreading is handled offline through a local Ollama server. The app sends text only to the configured local Ollama endpoint and rejects non-local endpoints so proofreading content is not uploaded to a remote service.

## Version 1 scope

Version 1 includes only the core local proofreading workflow:

1. Text input.
2. Profile selection.
3. Local LLM proofreading.
4. Result output.
5. Copy result.
6. Profile editor.
7. Import/export profiles.
8. Local model settings.

The first version does not include accounts, cloud features, payments, document management, or complex formatting. Profiles and settings are local files; there is no database, sign-in flow, subscription logic, remote sync, document library, rich-text editor, or advanced layout tooling.

## Prerequisites

1. Install and start [Ollama](https://ollama.com/).
2. Pull a local model, for example:

```powershell
ollama pull llama3.2:3b
```

If Ollama is not running, the app shows: `Local LLM is not available. Please start Ollama.`

## Run from source

```powershell
python -m proofread_app
```

When running directly from a checkout without installing the package:

```powershell
$env:PYTHONPATH = "src"
python -m proofread_app
```

## UI

- Input text area for pasted or typed text.
- Profile dropdown for proofreading modes loaded from portable JSON files.
- Primary `Proofread` action button for local LLM proofreading.
- Output area for corrected text.
- `Copy Result`, `Settings`, and `Edit Profiles` buttons.

## Proofreading profiles

Profiles define task-specific proofreading behavior. Each profile is a portable JSON file with:

- `name`
- `description`
- `system_message`
- optional settings: `temperature`, `explain_changes`, and `preserve_tone`

The repository includes starter profiles in `profiles/email.json`, `profiles/blog_post.json`, and `profiles/grammar_only.json`. On first run, the app creates editable copies in the current user's profile folder: `%APPDATA%\Proofread App\profiles` on Windows, or `~/.proofread_app/profiles` on other platforms.

Open `Edit Profiles` to create, edit, delete, export, or import profile JSON files. Exported profile files can be copied to another machine and imported there.

## Local LLM settings

Open `Settings` in the app to configure the Ollama backend:

- Ollama endpoint, default `http://localhost:11434`.
- Model name, default `llama3.2:3b`.
- Timeout value in seconds, default `30`.

Settings are stored as a simple `settings.json` file in the current user's app data folder on Windows, or `~/.proofread_app/settings.json` on other platforms. Profiles are stored as individual `profiles/*.json` files, so no database is required for the first version.
