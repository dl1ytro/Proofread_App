from proofread_app.profiles import ProofreadingProfile
from proofread_app.prompt_builder import build_prompt


def test_build_prompt_combines_profile_text_and_output_rules_in_order():
    profile = ProofreadingProfile(
        "Email",
        "Polish emails.",
        "Correct email grammar while staying professional.",
    )

    prompt = build_prompt("teh update is ready", profile)

    assert prompt.index("## 1. Global system instruction") < prompt.index("## 2. Selected profile instruction")
    assert prompt.index("## 2. Selected profile instruction") < prompt.index("## 3. User text")
    assert prompt.index("## 3. User text") < prompt.index("## 4. Output rules")
    assert "Profile: Email" in prompt
    assert "Profile guidance: Polish emails." in prompt
    assert "Profile instruction: Correct email grammar while staying professional." in prompt
    assert "teh update is ready" in prompt
    assert "- Preserve the original meaning." in prompt
    assert "- Do not invent new facts." in prompt
    assert "- Do not remove important details." in prompt
    assert "- Return only the corrected text unless the profile requests explanations." in prompt


def test_build_prompt_respects_profile_explanations_and_tone_settings():
    profile = ProofreadingProfile(
        "Release Notes",
        "Proof release notes.",
        "Use concise product-release language.",
        explain_changes=True,
        preserve_tone=False,
    )

    prompt = build_prompt("fixed bug", profile)

    assert "You may adjust tone when it improves the result." in prompt
    assert "- Return the corrected text followed by a concise explanation of the changes." in prompt
