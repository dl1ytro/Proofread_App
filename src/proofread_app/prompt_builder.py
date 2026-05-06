"""Centralized prompt construction for proofreading profiles."""

from __future__ import annotations

from .profiles import ProofreadingProfile

GLOBAL_SYSTEM_INSTRUCTION = (
    "You are an offline proofreading assistant running locally in Ollama. "
    "Correct the user's text according to the selected proofreading profile."
)

DEFAULT_OUTPUT_RULES = (
    "Preserve the original meaning.",
    "Do not invent new facts.",
    "Do not remove important details.",
)


def build_prompt(text: str, profile: ProofreadingProfile) -> str:
    """Combine the selected profile, user text, and output rules into one prompt."""

    normalized_profile = profile.normalized()
    tone_instruction = (
        "Preserve the user's tone unless a correction requires a small wording change."
        if normalized_profile.preserve_tone
        else "You may adjust tone when it improves the result."
    )
    response_instruction = (
        "Return the corrected text followed by a concise explanation of the changes."
        if normalized_profile.explain_changes
        else "Return only the corrected text unless the profile requests explanations."
    )
    output_rules = (*DEFAULT_OUTPUT_RULES, response_instruction)

    return "\n\n".join(
        (
            _format_section("1. Global system instruction", GLOBAL_SYSTEM_INSTRUCTION),
            _format_section(
                "2. Selected profile instruction",
                "\n".join(
                    (
                        f"Profile: {normalized_profile.name}",
                        f"Profile guidance: {normalized_profile.description}",
                        f"Profile instruction: {normalized_profile.system_message}",
                        f"Tone instruction: {tone_instruction}",
                    )
                ),
            ),
            _format_section("3. User text", text),
            _format_section("4. Output rules", "\n".join(f"- {rule}" for rule in output_rules)),
        )
    )


def _format_section(title: str, body: str) -> str:
    return f"## {title}\n{body}"
