from proofread_app.engine import proofread_text


def test_standard_profile_fixes_common_typos_and_spacing():
    assert proofread_text("teh quick  fox ,jumps") == "The quick fox, jumps"


def test_business_profile_expands_common_workplace_shorthand():
    assert proofread_text("fyi send this asap", "Business") == "For your information send this as soon as possible."


def test_academic_profile_expands_contractions():
    assert proofread_text("we can't use teh draft", "Academic") == "We cannot use the draft"
