"""Pytest configuration and test fixtures for Chatterbox Voice Studio."""

import os
import shutil
import sys
import tempfile
from pathlib import Path
import pytest

# Ensure plugin directory and root directory are in sys.path across all platforms
_TESTS_DIR = Path(__file__).resolve().parent
_PLUGIN_DIR = _TESTS_DIR.parent
_ROOT_DIR = _PLUGIN_DIR.parent.parent

for _p in [str(_PLUGIN_DIR), str(_ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Ensure mock inference is enabled during all automated test runs
os.environ["CHATTERBOX_MOCK_INFERENCE"] = "true"
os.environ["CHATTERBOX_MODE"] = "local"

from backend.config import config
from backend.profiles import VoiceProfileManager
from backend.engine import ChatterboxVoiceEngine


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup isolated test storage and voice profile directories."""
    test_dir = Path(tempfile.mkdtemp(prefix="cbx_test_")).resolve()
    storage_dir = (test_dir / "generated_audio").resolve()
    profiles_dir = (test_dir / "voice_profiles").resolve()

    storage_dir.mkdir(parents=True, exist_ok=True)
    profiles_dir.mkdir(parents=True, exist_ok=True)

    config.storage_dir = storage_dir
    config.profiles_dir = profiles_dir
    config.mock_inference = True

    yield {
        "test_dir": test_dir,
        "storage_dir": storage_dir,
        "profiles_dir": profiles_dir,
    }

    # Cleanup after tests
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def test_profile_manager(setup_test_environment):
    """Provides a fresh VoiceProfileManager using isolated test storage."""
    return VoiceProfileManager(profiles_dir=setup_test_environment["profiles_dir"])


@pytest.fixture
def test_engine():
    """Provides a ChatterboxVoiceEngine in mock inference mode."""
    return ChatterboxVoiceEngine()
