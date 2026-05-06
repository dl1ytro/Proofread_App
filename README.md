# Proofread App

A lightweight desktop proofreading interface designed for Windows 10 and Windows 11. The first UI uses Python's standard `tkinter` toolkit, so it avoids accounts, web views, complex navigation, and unnecessary animations.

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
- Profile dropdown for proofreading modes.
- Primary `Proofread` action button.
- Output area for corrected text.
- `Copy Result`, `Clear`, and `Edit Profiles` buttons.

The built-in proofreading engine is intentionally local and simple for the first UI. It normalizes spacing, fixes common typos, balances a few punctuation patterns, and applies lightweight tone changes based on the selected profile.
