"""Proofreading profiles used by the desktop UI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProofreadingProfile:
    """A named proofreading mode shown in the profile dropdown."""

    name: str
    description: str


DEFAULT_PROFILES: tuple[ProofreadingProfile, ...] = (
    ProofreadingProfile(
        "Standard",
        "Correct spelling, spacing, capitalization, and punctuation while preserving the original tone.",
    ),
    ProofreadingProfile(
        "Business",
        "Make the text concise, polished, and professional for workplace communication.",
    ),
    ProofreadingProfile(
        "Academic",
        "Favor formal wording and reduce casual contractions where possible.",
    ),
    ProofreadingProfile(
        "Casual",
        "Keep wording relaxed and conversational while fixing visible mistakes.",
    ),
)


def profile_names() -> list[str]:
    """Return profile names in UI order."""

    return [profile.name for profile in DEFAULT_PROFILES]


def profile_description(name: str) -> str:
    """Return a profile description, defaulting to Standard for unknown names."""

    for profile in DEFAULT_PROFILES:
        if profile.name == name:
            return profile.description
    return DEFAULT_PROFILES[0].description
