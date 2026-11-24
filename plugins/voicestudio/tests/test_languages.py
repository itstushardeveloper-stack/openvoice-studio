"""Tests for content language detection, Unicode scripts, and model support."""

import pytest
from backend.languages import (
    SUPPORTED_LANGUAGES,
    LANGUAGE_ALIASES,
    validate_and_resolve_language,
    detect_script_from_text,
    normalize_language_code,
)


def test_supported_languages_contains_23_languages():
    """Chatterbox Multilingual V3 officially supports 23 languages."""
    assert len(SUPPORTED_LANGUAGES) == 23
    assert "hi" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES
    assert "es" in SUPPORTED_LANGUAGES
    assert "fr" in SUPPORTED_LANGUAGES
    assert "ja" in SUPPORTED_LANGUAGES
    assert "zh" in SUPPORTED_LANGUAGES
    # Gujarati is NOT in the 23 supported languages of Chatterbox V3
    assert "gu" not in SUPPORTED_LANGUAGES


def test_normalize_language_code():
    """Verify aliases and names map to standard ISO codes."""
    assert normalize_language_code("Hindi") == "hi"
    assert normalize_language_code("हिन्दी") == "hi"
    assert normalize_language_code("English") == "en"
    assert normalize_language_code("gujarati") == "gu"
    assert normalize_language_code("French") == "fr"
    assert normalize_language_code("Deutsch") == "de"


def test_detect_script_from_text():
    """Verify automatic Unicode script detection."""
    # Devanagari Hindi text
    hindi_text = "नमस्ते दोस्तों, आज हम कृत्रिम बुद्धिमत्ता (AI) के बारे में चर्चा करेंगे।"
    code, script = detect_script_from_text(hindi_text)
    assert code == "hi"
    assert "Devanagari" in script

    # Gujarati text
    gujarati_text = "નમસ્તે મિત્રો, આ એક ગુજરાતી સ્ક્રિપ્ટ છે."
    code, script = detect_script_from_text(gujarati_text)
    assert code == "gu"
    assert "Gujarati" in script

    # English Latin text
    english_text = "Welcome to the future of voice technology and artificial intelligence."
    code, script = detect_script_from_text(english_text)
    assert code == "en"


def test_explicit_hindi_language_handling():
    """Verify explicit Hindi request succeeds with audio generation flag."""
    res = validate_and_resolve_language(explicit_language="Hindi")
    assert res.code == "hi"
    assert res.name == "Hindi"
    assert res.is_supported is True
    assert res.can_generate_audio is True


def test_explicit_english_language_handling():
    """Verify explicit English request succeeds with audio generation flag."""
    res = validate_and_resolve_language(explicit_language="English")
    assert res.code == "en"
    assert res.name == "English"
    assert res.is_supported is True
    assert res.can_generate_audio is True


def test_explicit_gujarati_unsupported_language_handling():
    """Verify explicit Gujarati request safely flags unsupported audio without failing."""
    res = validate_and_resolve_language(explicit_language="Gujarati")
    assert res.code == "gu"
    assert res.name == "Gujarati"
    assert res.is_supported is False
    assert res.can_generate_audio is False
    assert "NOT supported" in res.message
    assert "audio generation was safely bypassed" in res.message


def test_implicit_content_language_detection():
    """Verify content script takes precedence when language is not explicitly provided."""
    hindi_content = "यह एक हिंदी स्क्रिप्ट है जो चैटबॉक्स के माध्यम से बोली जाएगी।"
    res = validate_and_resolve_language(explicit_language=None, content_text=hindi_content)
    assert res.code == "hi"
    assert res.is_supported is True
    assert res.can_generate_audio is True
