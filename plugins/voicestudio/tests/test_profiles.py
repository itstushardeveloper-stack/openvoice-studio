"""Tests for Voice Profile creation, storage, and authorization safeguards."""

import pytest
from pathlib import Path
from backend.profiles import VoiceProfileManager
from backend.audio_utils import create_mock_wav_bytes


def test_builtin_profiles_seeded(test_profile_manager):
    """Verify standard built-in profiles are automatically initialized."""
    profiles = test_profile_manager.list_profiles()
    names = [p.name for p in profiles]
    assert "standard_hindi_narrator" in names
    assert "standard_english_narrator" in names
    assert "conversational_turbo" in names


def test_unauthorized_voice_cloning_blocked(test_profile_manager, setup_test_environment):
    """Voice cloning MUST fail with PermissionError if authorization is False."""
    sample_wav = setup_test_environment["storage_dir"] / "sample_voice.wav"
    sample_wav.write_bytes(create_mock_wav_bytes(1.0))

    with pytest.raises(PermissionError) as exc_info:
        test_profile_manager.create_profile(
            name="stolen_voice",
            audio_file_path=sample_wav,
            authorized=False,  # Unauthorized!
            gender="female",
        )
    assert "authorization" in str(exc_info.value).lower()


def test_authorized_voice_cloning_succeeds(test_profile_manager, setup_test_environment):
    """Voice cloning succeeds when user explicitly affirms authorization."""
    sample_wav = setup_test_environment["storage_dir"] / "my_authorized_voice.wav"
    sample_wav.write_bytes(create_mock_wav_bytes(2.0))

    profile = test_profile_manager.create_profile(
        name="my_cloned_voice",
        audio_file_path=sample_wav,
        authorized=True,
        gender="male",
        language_tag="hi",
        description="Authorized Hindi narrator clone",
    )

    assert profile.name == "my_cloned_voice"
    assert profile.authorized is True
    assert profile.audio_path is not None
    assert Path(profile.audio_path).exists()

    # Retrieve profile
    fetched = test_profile_manager.get_profile("my_cloned_voice")
    assert fetched is not None
    assert fetched.name == "my_cloned_voice"


def test_cannot_delete_builtin_profile(test_profile_manager):
    """Attempting to delete core built-in profiles must raise ValueError."""
    with pytest.raises(ValueError):
        test_profile_manager.delete_profile("standard_hindi_narrator")
