"""Portable JSON proofreading profiles used by the desktop UI."""

from __future__ import annotations

import json
import os
import re
import shutil
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_TEMPERATURE = 0.1


class ProfileError(ValueError):
    """Raised when a profile file or field cannot be parsed."""


@dataclass(frozen=True)
class ProfileLoadResult:
    """Profiles loaded from disk plus non-fatal file errors."""

    profiles: list["ProofreadingProfile"]
    errors: list[str]


@dataclass(frozen=True)
class ProofreadingProfile:
    """A named proofreading task profile stored as a portable JSON file."""

    name: str
    description: str
    system_message: str
    temperature: float | None = None
    explain_changes: bool = False
    preserve_tone: bool = True

    def normalized(self) -> "ProofreadingProfile":
        """Return a profile with trimmed text and validated optional settings."""

        name = self.name.strip()
        description = self.description.strip()
        system_message = self.system_message.strip()
        if not name:
            raise ProfileError("Profile name is required.")
        if not description:
            raise ProfileError("Profile description is required.")
        if not system_message:
            raise ProfileError("Profile system message is required.")

        temperature = self.temperature
        if temperature is not None:
            try:
                temperature = float(temperature)
            except (TypeError, ValueError) as exc:
                raise ProfileError("Temperature must be a number between 0 and 2.") from exc
            if not 0 <= temperature <= 2:
                raise ProfileError("Temperature must be between 0 and 2.")

        return ProofreadingProfile(
            name=name,
            description=description,
            system_message=system_message,
            temperature=temperature,
            explain_changes=bool(self.explain_changes),
            preserve_tone=bool(self.preserve_tone),
        )

    def to_json_dict(self) -> dict[str, object]:
        """Return the JSON representation used for profile files."""

        return asdict(self.normalized())


DEFAULT_PROFILES: tuple[ProofreadingProfile, ...] = (
    ProofreadingProfile(
        name="Email",
        description="Polish emails so they are clear, friendly, and ready to send.",
        system_message=(
            "You proofread email messages. Correct spelling, grammar, punctuation, capitalization, and spacing. "
            "Make the message concise and professional without changing the sender's intent."
        ),
        temperature=0.1,
        explain_changes=False,
        preserve_tone=True,
    ),
    ProofreadingProfile(
        name="Blog Post",
        description="Improve blog drafts for readability, flow, and publication quality.",
        system_message=(
            "You proofread blog posts. Correct errors, improve readability, smooth awkward phrasing, and keep the "
            "author's voice suitable for a public article."
        ),
        temperature=0.2,
        explain_changes=False,
        preserve_tone=True,
    ),
    ProofreadingProfile(
        name="Grammar Only",
        description="Fix only objective grammar, spelling, punctuation, capitalization, and spacing issues.",
        system_message=(
            "You perform strict grammar-only proofreading. Fix objective mistakes only. Do not rewrite sentences, "
            "change word choice, add new ideas, or alter the structure unless required for correctness."
        ),
        temperature=0.0,
        explain_changes=False,
        preserve_tone=True,
    ),
)


def default_profiles_dir() -> Path:
    """Return the per-user folder containing portable profile JSON files."""

    app_data = os.environ.get("APPDATA")
    if app_data:
        return Path(app_data) / "Proofread App" / "profiles"
    return Path.home() / ".proofread_app" / "profiles"


def slugify_profile_name(name: str) -> str:
    """Return a safe filename stem for a profile name."""

    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "profile"


def profile_path(profile: ProofreadingProfile, directory: Path | None = None) -> Path:
    """Return the default JSON path for *profile* in *directory*."""

    return (directory or default_profiles_dir()) / f"{slugify_profile_name(profile.name)}.json"


def ensure_default_profiles(directory: Path | None = None) -> None:
    """Create default portable profile files when a profile folder is empty."""

    profiles_dir = directory or default_profiles_dir()
    profiles_dir.mkdir(parents=True, exist_ok=True)
    if any(profiles_dir.glob("*.json")):
        return
    for profile in DEFAULT_PROFILES:
        save_profile(profile, profiles_dir)


def load_profiles(directory: Path | None = None) -> list[ProofreadingProfile]:
    """Load valid portable profile JSON files from disk, creating defaults if needed."""

    return load_profiles_with_errors(directory).profiles


def load_profiles_with_errors(directory: Path | None = None) -> ProfileLoadResult:
    """Load profiles and report invalid JSON/files without deleting or overwriting them."""

    profiles_dir = directory or default_profiles_dir()
    ensure_default_profiles(profiles_dir)
    profiles: list[ProofreadingProfile] = []
    errors: list[str] = []
    for path in sorted(profiles_dir.glob("*.json")):
        try:
            profiles.append(load_profile(path))
        except (OSError, ProfileError) as exc:
            errors.append(f"{path.name}: {exc}")

    if not profiles:
        profiles = [profile.normalized() for profile in DEFAULT_PROFILES]
        if errors:
            errors.append("Using built-in default profiles until profile files are fixed.")

    default_order = {profile.name.casefold(): index for index, profile in enumerate(DEFAULT_PROFILES)}
    profiles = sorted(
        profiles,
        key=lambda profile: (
            default_order.get(profile.name.casefold(), len(default_order)),
            profile.name.casefold(),
        ),
    )
    return ProfileLoadResult(profiles, errors)


def load_profile(path: Path) -> ProofreadingProfile:
    """Load a single profile JSON file."""

    try:
        with path.open("r", encoding="utf-8") as profile_file:
            payload = json.load(profile_file)
    except json.JSONDecodeError as exc:
        raise ProfileError("Profile file is invalid JSON. Fix or restore it from backup; it was not changed.") from exc
    if not isinstance(payload, dict):
        raise ProfileError("Profile file must contain a JSON object.")
    return profile_from_dict(payload).normalized()


def profile_from_dict(payload: dict[str, object]) -> ProofreadingProfile:
    """Parse a profile from a JSON dictionary."""

    return ProofreadingProfile(
        name=str(payload.get("name", "")),
        description=str(payload.get("description", "")),
        system_message=str(payload.get("system_message", "")),
        temperature=_optional_temperature(payload.get("temperature")),
        explain_changes=bool(payload.get("explain_changes", False)),
        preserve_tone=bool(payload.get("preserve_tone", True)),
    )


def save_profile(profile: ProofreadingProfile, directory: Path | None = None) -> ProofreadingProfile:
    """Save *profile* as a portable JSON file and return the normalized profile."""

    normalized = profile.normalized()
    profiles_dir = directory or default_profiles_dir()
    profiles_dir.mkdir(parents=True, exist_ok=True)
    destination = profile_path(normalized, profiles_dir)
    temporary = destination.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as profile_file:
        json.dump(normalized.to_json_dict(), profile_file, indent=2)
        profile_file.write("\n")
    temporary.replace(destination)
    return normalized


def delete_profile(name: str, directory: Path | None = None) -> None:
    """Delete a profile file by name when it exists."""

    path = (directory or default_profiles_dir()) / f"{slugify_profile_name(name)}.json"
    if path.exists():
        path.unlink()


def duplicate_profile(profile: ProofreadingProfile, directory: Path | None = None) -> ProofreadingProfile:
    """Create and save a copy of *profile* with a unique name."""

    profiles_dir = directory or default_profiles_dir()
    existing_names = {loaded.name.casefold() for loaded in load_profiles(profiles_dir)}
    base_name = f"{profile.name} Copy"
    candidate = base_name
    suffix = 2
    while candidate.casefold() in existing_names:
        candidate = f"{base_name} {suffix}"
        suffix += 1
    duplicate = ProofreadingProfile(
        name=candidate,
        description=profile.description,
        system_message=profile.system_message,
        temperature=profile.temperature,
        explain_changes=profile.explain_changes,
        preserve_tone=profile.preserve_tone,
    )
    return save_profile(duplicate, profiles_dir)


def export_profile(profile: ProofreadingProfile, destination: Path) -> Path:
    """Export *profile* to a JSON file chosen by the user."""

    normalized = profile.normalized()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as profile_file:
        json.dump(normalized.to_json_dict(), profile_file, indent=2)
        profile_file.write("\n")
    temporary.replace(destination)
    return destination


def import_profile(source: Path, directory: Path | None = None) -> ProofreadingProfile:
    """Import a portable profile JSON file into the local profile folder."""

    profile = load_profile(source)
    profiles_dir = directory or default_profiles_dir()
    saved = save_profile(profile, profiles_dir)
    if source.resolve() != profile_path(saved, profiles_dir).resolve():
        shutil.copystat(source, profile_path(saved, profiles_dir), follow_symlinks=True)
    return saved


def backup_profiles(destination: Path, directory: Path | None = None) -> Path:
    """Back up every local profile JSON file into a portable zip archive."""

    profiles_dir = directory or default_profiles_dir()
    ensure_default_profiles(profiles_dir)
    profile_files = sorted(profiles_dir.glob("*.json"))
    if not profile_files:
        raise ProfileError("No profile JSON files are available to back up.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as backup_file:
        for profile_file in profile_files:
            backup_file.write(profile_file, arcname=profile_file.name)
    return destination


def profile_names(profiles: list[ProofreadingProfile] | None = None) -> list[str]:
    """Return profile names in UI order."""

    return [profile.name for profile in (profiles or list(DEFAULT_PROFILES))]


def profile_description(name: str, profiles: list[ProofreadingProfile] | None = None) -> str:
    """Return a profile description, defaulting to the first profile for unknown names."""

    available = profiles or list(DEFAULT_PROFILES)
    for profile in available:
        if profile.name == name:
            return profile.description
    return available[0].description if available else ""


def find_profile(name: str, profiles: list[ProofreadingProfile] | None = None) -> ProofreadingProfile:
    """Return the named profile, defaulting to the first profile when not found."""

    available = profiles or load_profiles()
    for profile in available:
        if profile.name == name:
            return profile
    return available[0]


def _optional_temperature(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ProfileError("Temperature must be a number between 0 and 2.") from exc
