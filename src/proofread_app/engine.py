"""Small local proofreading helpers for the first desktop UI."""

from __future__ import annotations

import re

_COMMON_REPLACEMENTS = {
    "teh": "the",
    "adn": "and",
    "recieve": "receive",
    "recieved": "received",
    "seperate": "separate",
    "definately": "definitely",
    "occured": "occurred",
    "untill": "until",
    "wich": "which",
    "alot": "a lot",
    "dont": "don't",
    "cant": "can't",
    "wont": "won't",
    "im": "I'm",
    "ive": "I've",
}

_ACADEMIC_REPLACEMENTS = {
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "isn't": "is not",
    "aren't": "are not",
    "it's": "it is",
}

_BUSINESS_REPLACEMENTS = {
    "asap": "as soon as possible",
    "fyi": "for your information",
    "thanks": "Thank you",
}


def proofread_text(text: str, profile: str = "Standard") -> str:
    """Return a lightly corrected version of *text* for the selected profile.

    This is deliberately modest: it keeps the app local and responsive while the
    first UI is being validated. A future service-backed engine can replace this
    function without changing the UI layout.
    """

    normalized = _normalize_whitespace(text)
    corrected = _replace_words(normalized, _COMMON_REPLACEMENTS)
    corrected = _fix_punctuation_spacing(corrected)
    corrected = _capitalize_sentences(corrected)

    if profile == "Academic":
        corrected = _replace_words(corrected, _ACADEMIC_REPLACEMENTS)
    elif profile == "Business":
        corrected = _replace_words(corrected, _BUSINESS_REPLACEMENTS)
        corrected = _ensure_terminal_punctuation(corrected)

    return corrected.strip()


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _replace_words(text: str, replacements: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        word = match.group(0)
        replacement = replacements[word.lower()]
        if word.isupper():
            return replacement.upper()
        if word[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement

    pattern = re.compile(r"\b(" + "|".join(re.escape(word) for word in replacements) + r")\b", re.IGNORECASE)
    return pattern.sub(replace, text)


def _fix_punctuation_spacing(text: str) -> str:
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])([^\s\n\"')\]}])", r"\1 \2", text)
    text = re.sub(r"([!?.,]){2,}", lambda match: match.group(0)[0], text)
    return text


def _capitalize_sentences(text: str) -> str:
    chars = list(text)
    should_capitalize = True
    for index, char in enumerate(chars):
        if char.isalpha() and should_capitalize:
            chars[index] = char.upper()
            should_capitalize = False
        elif char in ".!?\n":
            should_capitalize = True
        elif not char.isspace():
            should_capitalize = False
    return "".join(chars)


def _ensure_terminal_punctuation(text: str) -> str:
    if text and text[-1] not in ".!?":
        return f"{text}."
    return text
