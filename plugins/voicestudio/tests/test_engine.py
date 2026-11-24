"""Tests for the Chatterbox Voice Engine, TTS synthesis, chunking, and fallback."""

from pathlib import Path
import pytest
from backend.engine import ChatterboxVoiceEngine, GenerationResult


def test_engine_synthesize_hindi(test_engine):
    """Verify Hindi speech synthesis produces valid WAV audio and saved script file."""
    hindi_text = (
        "नमस्ते दोस्तों! आज हम जानेंगे कि कैसे मॉडर्न AI हमारी ज़िंदगी को हमेशा के लिए बदल रहा है। "
        "वीडियो को अंत तक ज़रूर देखें।"
    )

    result: GenerationResult = test_engine.synthesize(
        text=hindi_text,
        language_id="hi",
        title="Hindi_AI_Intro",
    )

    assert result.status == "completed"
    assert result.language_id == "hi"
    assert result.language_name == "Hindi"
    assert result.duration_seconds > 0.5
    assert result.audio_path is not None
    assert Path(result.audio_path).exists()
    assert Path(result.script_path).exists()

    # Script file should contain original text
    with open(result.script_path, "r", encoding="utf-8") as f:
        saved_text = f.read()
    assert "नमस्ते दोस्तों" in saved_text


def test_engine_synthesize_english(test_engine):
    """Verify English documentary speech synthesis."""
    english_text = (
        "Deep within the cosmos, billions of stars illuminate the vast, silent expanse of space. "
        "Every galaxy tells a story of cosmic evolution."
    )

    result: GenerationResult = test_engine.synthesize(
        text=english_text,
        language_id="en",
        title="Cosmos_Doc",
    )

    assert result.status == "completed"
    assert result.language_id == "en"
    assert result.audio_path is not None
    assert Path(result.audio_path).exists()
    assert result.duration_seconds > 0.5


def test_engine_unsupported_gujarati_preserves_script_skips_audio(test_engine):
    """
    CRITICAL USER REQUIREMENT:
    When an unsupported language (like Gujarati) is requested:
    - Preserve the script in Gujarati.
    - Save the script file.
    - Do NOT generate corrupted audio.
    - Return clear explanatory status and message.
    """
    gujarati_text = (
        "નમસ્તે દર્શક મિત્રો! આજના વીડિયોમાં આપણે આર્ટિફિશિયલ ઇન્ટેલિજન્સ વિશે વાત કરીશું."
    )

    result: GenerationResult = test_engine.synthesize(
        text=gujarati_text,
        language_id="gu",
        title="Gujarati_Reel",
    )

    assert result.status == "unsupported_language_script_saved"
    assert result.language_id == "gu"
    assert result.language_name == "Gujarati"
    assert result.audio_path is None, "Audio MUST NOT be generated for unsupported languages"
    assert result.script_path is not None
    assert Path(result.script_path).exists()

    # Verify original Gujarati text was fully preserved
    with open(result.script_path, "r", encoding="utf-8") as f:
        saved_script = f.read()
    assert "નમસ્તે દર્શક મિત્રો" in saved_script
    assert "NOT supported" in result.message


def test_engine_long_text_chunking(test_engine):
    """Verify long scripts are divided into multiple chunks and concatenated seamlessly."""
    long_script = (
        "Welcome to episode one of our audio series. Today we explore the architecture of neural networks. "
        "First, we examine how artificial neurons take multiple weighted inputs and pass them through activation functions. "
        "Second, we look at how backpropagation calculates gradients efficiently across hidden layers. "
        "Finally, we analyze real-world applications in voice generation, multilingual translation, and autonomous agents."
    )

    result: GenerationResult = test_engine.synthesize(
        text=long_script,
        language_id="en",
        title="Long_Episode",
    )

    assert result.status == "completed"
    assert result.chunks_count >= 2, "Long text should be broken into 2+ chunks"
    assert Path(result.audio_path).exists()


def test_engine_history_logging(test_engine):
    """Verify generation events are recorded into history log."""
    history = test_engine.get_history(limit=10)
    assert isinstance(history, list)
    assert len(history) > 0
    latest = history[0]
    assert "id" in latest
    assert "language_id" in latest
    assert "script_path" in latest
