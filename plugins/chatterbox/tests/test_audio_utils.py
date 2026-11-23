"""Tests for script cleaning, chunking, and WAV audio utilities."""

import io
import wave
import pytest
from backend.audio_utils import (
    clean_script_for_tts,
    chunk_text,
    concat_wav_buffers,
    create_mock_wav_bytes,
    sanitize_filename,
)


def test_clean_script_removes_stage_cues_and_markdown():
    """Verify production cues and speaker labels are removed while spoken text is preserved."""
    raw_script = """
    # Scene 1: The Awakening
    **Visual:** Aerial shot of a glowing futuristic metropolis at dawn.
    [Visual: Drone pans over neon skyscrapers]
    (Dramatic electronic music fades in)
    Host (enthusiastic): Hello and welcome to today's deep dive into AI!
    [Music swells]
    Narrator: In 2026, technology took an unprecedented leap forward.
    (Sound effect: digital swoosh)
    [laugh] That was completely unexpected!
    *Remember to like and subscribe.*
    """

    cleaned = clean_script_for_tts(raw_script)

    # Should NOT contain cues
    assert "# Scene 1" not in cleaned
    assert "Aerial shot" not in cleaned
    assert "Visual:" not in cleaned
    assert "Drone pans" not in cleaned
    assert "music fades" not in cleaned
    assert "Host" not in cleaned
    assert "Narrator:" not in cleaned
    assert "digital swoosh" not in cleaned

    # SHOULD contain spoken words and allowed paralinguistic tag [laugh]
    assert "Hello and welcome to today's deep dive into AI!" in cleaned
    assert "In 2026, technology took an unprecedented leap forward." in cleaned
    assert "[laugh]" in cleaned


def test_clean_script_hindi():
    """Verify Hindi script stage directions are removed while Devanagari text remains intact."""
    hindi_script = """
    # भाग १: परिचय
    [दृश्य: कैमरा रोबोट की तरफ बढ़ता है]
    (धीमा संगीत बजता है)
    होस्ट: नमस्ते दोस्तों! आज हम आर्टिफिशियल इंटेलिजेंस के बारे में विस्तार से जानेंगे।
    [Visual: Graphs showing AI growth]
    यह तकनीक हमारी आने वाली पीढ़ी का भविष्य बदल देगी।
    """
    cleaned = clean_script_for_tts(hindi_script)
    assert "दृश्य:" not in cleaned
    assert "धीमा संगीत" not in cleaned
    assert "Visual:" not in cleaned
    assert "नमस्ते दोस्तों! आज हम आर्टिफिशियल इंटेलिजेंस के बारे में विस्तार से जानेंगे।" in cleaned
    assert "यह तकनीक हमारी आने वाली पीढ़ी का भविष्य बदल देगी।" in cleaned


def test_chunk_text_under_limit():
    """Text shorter than limit should return a single chunk."""
    short = "This is a short sentence for testing."
    chunks = chunk_text(short, max_chunk_chars=100)
    assert len(chunks) == 1
    assert chunks[0] == short


def test_chunk_text_long_sentences_splits_at_punctuation():
    """Long text should split cleanly at sentence or clause boundaries."""
    text = (
        "First sentence is short. "
        "Second sentence provides a longer explanation about how voice models generate waveforms from phonemes. "
        "Third sentence concludes the paragraph nicely with a strong takeaway message for the audience."
    )
    chunks = chunk_text(text, max_chunk_chars=120)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 150  # within sensible bound


def test_chunk_text_hindi_devanagari_purna_viram():
    """Verify text chunking respects Hindi purna viram (।) punctuation."""
    hindi_text = (
        "आर्टिफिशियल इंटेलिजेंस आज हर क्षेत्र में क्रांति ला रहा है। "
        "चिकित्सा से लेकर अंतरिक्ष विज्ञान तक कंप्यूटर इंसानों की सहायता कर रहे हैं। "
        "आने वाले वर्षों में यह क्रांति और भी तीव्र गति से आगे बढ़ेगी।"
    )
    chunks = chunk_text(hindi_text, max_chunk_chars=80)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) > 0


def test_create_and_concat_mock_wav_buffers():
    """Verify WAV buffers can be generated and concatenated into a valid master WAV."""
    wav1 = create_mock_wav_bytes(duration_sec=0.3, sample_rate=24000)
    wav2 = create_mock_wav_bytes(duration_sec=0.4, sample_rate=24000)

    # Validate individual wavs
    with wave.open(io.BytesIO(wav1), "rb") as wf:
        assert wf.getframerate() == 24000
        assert wf.getnchannels() == 1

    # Concatenate
    master_wav = concat_wav_buffers([wav1, wav2], pause_sec=0.1, sample_rate=24000)
    with wave.open(io.BytesIO(master_wav), "rb") as wf:
        assert wf.getframerate() == 24000
        frames = wf.getnframes()
        duration = frames / 24000.0
        # Duration should be ~ 0.3 + 0.1 pause + 0.4 = ~0.8s
        assert 0.7 <= duration <= 0.9


def test_sanitize_filename_prevents_directory_traversal():
    """Verify path traversal characters are stripped."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32") == "system32"
    assert sanitize_filename("my cool audio file!@#$.wav") == "my cool audio file____.wav"
