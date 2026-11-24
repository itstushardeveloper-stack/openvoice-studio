"""VoiceStudio & Chatterbox Voice Engine package."""

from .config import config, VoiceStudioConfig, ChatterboxConfig
from .engine import engine, VoiceStudioEngine, ChatterboxVoiceEngine, GenerationResult
from .languages import (
    SUPPORTED_LANGUAGES,
    validate_and_resolve_language,
    LanguageValidationResult,
    detect_script_from_text,
)
from .profiles import profile_manager, VoiceProfileManager, VoiceProfile
from .audio_utils import (
    clean_script_for_tts,
    chunk_text,
    concat_wav_buffers,
    create_mock_wav_bytes,
    sanitize_filename,
    validate_audio_file,
)

__version__ = "1.2.0"
__all__ = [
    "config",
    "VoiceStudioConfig",
    "ChatterboxConfig",
    "engine",
    "VoiceStudioEngine",
    "ChatterboxVoiceEngine",
    "GenerationResult",
    "SUPPORTED_LANGUAGES",
    "validate_and_resolve_language",
    "LanguageValidationResult",
    "detect_script_from_text",
    "profile_manager",
    "VoiceProfileManager",
    "VoiceProfile",
    "clean_script_for_tts",
    "chunk_text",
    "concat_wav_buffers",
    "create_mock_wav_bytes",
    "sanitize_filename",
    "validate_audio_file",
]
