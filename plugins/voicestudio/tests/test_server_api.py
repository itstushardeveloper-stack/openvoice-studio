"""Tests for server routes, handlers, and security validation."""

from pathlib import Path
import pytest
from fastapi import HTTPException
from backend.server import (
    health,
    get_languages,
    check_language,
    generate_speech,
    get_audio_file,
    list_voice_profiles,
    delete_voice_profile,
    get_generation_history,
    verify_api_key,
    TTSGenerateRequest,
    LanguageCheckRequest,
)
from backend.config import config


def test_health_endpoint():
    """Verify health handler returns 200 metadata."""
    res = health()
    assert res["status"] == "healthy"
    assert "device" in res
    assert res["supported_languages_count"] == 23


def test_get_languages_endpoint():
    """Verify languages handler lists 23 supported languages."""
    res = get_languages()
    assert "supported_languages" in res
    assert len(res["supported_languages"]) == 23
    assert res["supported_languages"]["hi"] == "Hindi"
    assert res["supported_languages"]["en"] == "English"


def test_check_language_endpoint_hindi():
    """Verify language check for Hindi."""
    req = LanguageCheckRequest(language="Hindi")
    res = check_language(req)
    assert res["code"] == "hi"
    assert res["is_supported"] is True
    assert res["can_generate_audio"] is True


def test_check_language_endpoint_gujarati():
    """Verify language check for Gujarati flags unsupported gracefully."""
    req = LanguageCheckRequest(language="Gujarati")
    res = check_language(req)
    assert res["code"] == "gu"
    assert res["is_supported"] is False
    assert res["can_generate_audio"] is False


def test_generate_speech_endpoint_hindi():
    """Verify speech generation endpoint synthesizes Hindi audio."""
    req = TTSGenerateRequest(
        text="नमस्ते दोस्तों, आज का वीडियो बहुत ख़ास होने वाला है।",
        language_id="hi",
        title="Server_Hindi_Test",
    )
    res = generate_speech(req)
    assert res["status"] == "completed"
    assert res["language_id"] == "hi"
    assert res["audio_url"] is not None

    # Test file retrieval handler
    filename = Path(res["audio_path"]).name
    file_res = get_audio_file(filename)
    assert file_res.media_type == "audio/wav"
    assert Path(file_res.path).exists()


def test_path_traversal_attack_blocked():
    """Verify path traversal attacks on audio retrieval are rejected."""
    with pytest.raises(HTTPException) as exc_info:
        get_audio_file("../../../etc/passwd")
    assert exc_info.value.status_code in (403, 404)


def test_api_key_authentication():
    """Verify API key verification function."""
    original_key = config.api_key
    config.api_key = "secret-test-token-12345"

    try:
        # 1. Missing key -> raises 401
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(None)
        assert exc_info.value.status_code == 401

        # 2. Wrong key -> raises 401
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key("wrong-token")
        assert exc_info.value.status_code == 401

        # 3. Valid key -> returns key without exception
        valid = verify_api_key("secret-test-token-12345")
        assert valid == "secret-test-token-12345"
    finally:
        config.api_key = original_key


def test_list_and_delete_voice_profiles():
    """Verify profile handlers."""
    profiles_data = list_voice_profiles()
    assert "profiles" in profiles_data
    assert len(profiles_data["profiles"]) >= 3

    # Builtin deletion raises 400
    with pytest.raises(HTTPException) as exc_info:
        delete_voice_profile("standard_hindi_narrator")
    assert exc_info.value.status_code == 400


def test_generation_history_endpoint():
    """Verify history endpoint returns list of generations."""
    history_data = get_generation_history(limit=10)
    assert "history" in history_data
    assert isinstance(history_data["history"], list)
