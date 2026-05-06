from pathlib import Path

from proofread_app.profiles import DEFAULT_PROFILES, load_profile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGED_PROFILES_DIR = PROJECT_ROOT / "profiles"


def test_packaged_profiles_are_valid_and_match_default_profile_names():
    loaded_profiles = [
        load_profile(path) for path in sorted(PACKAGED_PROFILES_DIR.glob("*.json"))
    ]

    assert loaded_profiles
    assert {profile.name for profile in loaded_profiles} == {
        profile.name for profile in DEFAULT_PROFILES
    }


def test_packaged_profiles_include_required_offline_proofreading_guidance():
    for path in PACKAGED_PROFILES_DIR.glob("*.json"):
        profile = load_profile(path)

        assert profile.description
        assert profile.system_message
        assert 0 <= profile.temperature <= 2
        assert profile.preserve_tone is True
