import json

import pytest

from proofread_app.profiles import (
    ProfileError,
    ProofreadingProfile,
    default_profiles_dir,
    delete_profile,
    export_profile,
    import_profile,
    load_profiles,
    load_profiles_with_errors,
    profile_path,
    save_profile,
    slugify_profile_name,
)


def test_profiles_are_saved_as_portable_json(tmp_path):
    profile = ProofreadingProfile(
        name="Client Email",
        description="Polish client messages.",
        system_message="Fix grammar and keep the message professional.",
        temperature=0.15,
        explain_changes=True,
        preserve_tone=False,
    )

    saved = save_profile(profile, tmp_path)
    payload = json.loads((tmp_path / "client_email.json").read_text(encoding="utf-8"))

    assert saved == profile
    assert payload == {
        "name": "Client Email",
        "description": "Polish client messages.",
        "system_message": "Fix grammar and keep the message professional.",
        "temperature": 0.15,
        "explain_changes": True,
        "preserve_tone": False,
    }


def test_load_profiles_creates_default_files_in_empty_directory(tmp_path):
    profiles = load_profiles(tmp_path)

    assert {profile.name for profile in profiles} == {
        "Email",
        "Blog Post",
        "Grammar Only",
    }
    assert (tmp_path / "email.json").exists()
    assert (tmp_path / "blog_post.json").exists()
    assert (tmp_path / "grammar_only.json").exists()


def test_export_import_and_delete_profile(tmp_path):
    local_dir = tmp_path / "local"
    transfer_dir = tmp_path / "transfer"
    profile = ProofreadingProfile("Blog", "Blog edits.", "Proofread the blog post.")
    save_profile(profile, local_dir)

    exported_path = export_profile(profile, transfer_dir / "blog.json")
    delete_profile("Blog", local_dir)
    imported = import_profile(exported_path, local_dir)

    assert imported == profile.normalized()
    assert profile_path(imported, local_dir).exists()


def test_profile_validation_requires_core_fields_and_valid_temperature():
    with pytest.raises(ProfileError, match="name"):
        ProofreadingProfile("", "Description", "System").normalized()

    with pytest.raises(ProfileError, match="Temperature"):
        ProofreadingProfile("Name", "Description", "System", 3).normalized()


def test_slugify_profile_name_makes_windows_friendly_names():
    assert slugify_profile_name("Grammar Only!") == "grammar_only"


def test_load_profiles_skips_invalid_json_without_changing_file(tmp_path):
    valid = ProofreadingProfile("Valid", "Valid edits.", "Proofread valid text.")
    save_profile(valid, tmp_path)
    invalid_path = tmp_path / "broken.json"
    invalid_text = "{not valid json"
    invalid_path.write_text(invalid_text, encoding="utf-8")

    result = load_profiles_with_errors(tmp_path)

    assert [profile.name for profile in result.profiles] == ["Valid"]
    assert result.errors
    assert "broken.json" in result.errors[0]
    assert invalid_path.read_text(encoding="utf-8") == invalid_text


def test_load_profiles_falls_back_to_defaults_when_all_files_are_invalid(tmp_path):
    invalid_path = tmp_path / "broken.json"
    invalid_path.write_text("{not valid json", encoding="utf-8")

    result = load_profiles_with_errors(tmp_path)

    assert {profile.name for profile in result.profiles} == {
        "Email",
        "Blog Post",
        "Grammar Only",
    }
    assert any("built-in default profiles" in error for error in result.errors)
    assert invalid_path.exists()


def test_default_profiles_dir_uses_windows_appdata_when_available(monkeypatch, tmp_path):
    appdata = tmp_path / "AppData" / "Roaming"
    monkeypatch.setenv("APPDATA", str(appdata))

    assert default_profiles_dir() == appdata / "Proofread App" / "profiles"
