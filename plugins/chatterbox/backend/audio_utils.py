"""Audio utilities: script text cleaning, chunking, WAV concatenation, and validation."""

import io
import math
import os
import re
import struct
import wave
from pathlib import Path
from typing import List, Tuple, Optional


ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
AUDIO_HEADER_MAGIC = {
    b"RIFF": "wav",
    b"ID3": "mp3",
    b"\xff\xfb": "mp3",
    b"\xff\xf3": "mp3",
    b"\xff\xf2": "mp3",
    b"fLaC": "flac",
    b"OggS": "ogg",
}

# Paralinguistic tags supported natively in Chatterbox Turbo/Nano
ALLOWED_PARALINGUISTIC_TAGS = {"[laugh]", "[chuckle]", "[cough]", "[sigh]", "[gasp]", "[throat-clearing]"}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal or invalid characters across all OS platforms."""
    normalized = str(filename).replace("\\", "/")
    base = os.path.basename(normalized)
    # Remove path traversal tokens and illegal characters
    cleaned = re.sub(r'[^a-zA-Z0-9_\-\. ]', '_', base)
    cleaned = cleaned.strip(". ")
    return cleaned if cleaned else "output"


def clean_script_for_tts(script_text: str) -> str:
    """
    Clean full script text for TTS synthesis.
    
    Removes:
    - Markdown headers (# Scene 1)
    - Production cue lines like **Visual:** ..., [Visual: ...], Scene 1: ..., दृश्य: ...
    - Speaker prefixes like "Host: ", "Narrator: ", "होस्ट: ", "कथावाचक: "
    - Audio cues like (Dramatic electronic music fades in) or (Sound effect: swoosh)
    - Markdown bold/italic formatting
    
    Preserves:
    - Actual spoken text
    - Punctuation (. ! ? , ।)
    - Allowed Chatterbox paralinguistic tags like [laugh], [chuckle]
    """
    if not script_text:
        return ""

    lines = script_text.splitlines()
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip markdown headers (# Scene 1)
        if line.startswith("#"):
            continue

        # Skip lines that are purely metadata (e.g. "Duration: 5 minutes", "Topic: AI")
        if re.match(r"^(Duration|Topic|Target Audience|Tone|Format|Voice Profile)\s*:", line, re.I):
            continue

        # Skip lines that are purely visual or scene cues
        # e.g. **Visual:** ..., Visual: ..., Scene 1: ..., दृश्य: ..., [Visual: ...]
        if re.match(r"^(\*\*|\*)?(Visual|B-roll|Scene\s*\d*|Shot|Camera|दृश्य|सीन)\s*(\*\*|\*)?:", line, re.I):
            continue

        # Skip lines entirely enclosed in parentheses or brackets (cues)
        if (line.startswith("(") and line.endswith(")")) or (line.startswith("[") and line.endswith("]")):
            if line.lower() not in ALLOWED_PARALINGUISTIC_TAGS:
                continue

        # Remove speaker labels in English and Hindi
        line = re.sub(
            r"^(?:Host|Narrator|Speaker\s*\d*|VO|V/O|Voiceover|Anchor|होस्ट|कथावाचक|वक्ता)\s*(?:\([^)]*\))?\s*:\s*",
            "",
            line,
            flags=re.I
        )

        # Remove stage directions in square brackets unless it's a paralinguistic tag
        def replace_brackets(match):
            tag = match.group(0).lower()
            if tag in ALLOWED_PARALINGUISTIC_TAGS:
                return match.group(0)
            return ""

        line = re.sub(r"\[[^\]]+\]", replace_brackets, line)

        # Remove cues in parentheses: audio, sound, music, visual, sfx, effects, slow, dramatic, etc.
        line = re.sub(
            r"\([^)]*(?:music|sound|visual|camera|sfx|b-roll|pause|audio|effect|dramatic|ambient|bgm|electronic|swoosh|धीमा|संगीत|दृश्य|ध्वनि|हंस|हँस)[^)]*\)",
            "",
            line,
            flags=re.I
        )

        # Remove markdown bold/italic markers (*, **, _)
        line = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", line)
        line = re.sub(r"_{1,3}(.*?)_{1,3}", r"\1", line)
        line = re.sub(r"`(.*?)`", r"\1", line)

        # Remove bullet points
        line = re.sub(r"^[-*•]\s+", "", line)

        line = line.strip()
        if line:
            cleaned_lines.append(line)

    full_cleaned = " ".join(cleaned_lines)
    # Collapse multiple spaces
    full_cleaned = re.sub(r"\s+", " ", full_cleaned).strip()
    return full_cleaned


def chunk_text(text: str, max_chunk_chars: int = 250) -> List[str]:
    """
    Split text into optimal chunks for TTS inference without cutting mid-sentence.
    
    Supports Latin (. ! ?) and Devanagari (। ? !) sentence delimiters.
    """
    cleaned = text.strip()
    if not cleaned:
        return []

    if len(cleaned) <= max_chunk_chars:
        return [cleaned]

    # Split by primary sentence boundaries: . ! ? । and newlines
    sentence_regex = re.compile(r'([^.!?|।\n]+[.!?|।\n]+)')
    raw_sentences = sentence_regex.findall(cleaned)

    # Capture any trailing text without terminal punctuation
    consumed_len = sum(len(s) for s in raw_sentences)
    if consumed_len < len(cleaned):
        remainder = cleaned[consumed_len:].strip()
        if remainder:
            raw_sentences.append(remainder)

    chunks: List[str] = []
    current_chunk = ""

    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence) > max_chunk_chars:
            # If a single sentence is longer than max_chunk_chars, split by clause (comma, semicolon, dash)
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            clause_regex = re.compile(r'([^,;—\-]+[,;—\-]+)')
            clauses = clause_regex.findall(sentence)
            c_consumed = sum(len(c) for c in clauses)
            if c_consumed < len(sentence):
                trailing_clause = sentence[c_consumed:].strip()
                if trailing_clause:
                    clauses.append(trailing_clause)

            temp_sub = ""
            for clause in clauses:
                clause = clause.strip()
                if not clause:
                    continue
                if len(temp_sub) + len(clause) + 1 <= max_chunk_chars:
                    temp_sub = f"{temp_sub} {clause}".strip()
                else:
                    if temp_sub:
                        chunks.append(temp_sub.strip())
                    temp_sub = clause
            if temp_sub:
                chunks.append(temp_sub.strip())
        else:
            if len(current_chunk) + len(sentence) + 1 <= max_chunk_chars:
                current_chunk = f"{current_chunk} {sentence}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return [c for c in chunks if c]


def create_silence_wav_bytes(duration_sec: float = 0.25, sample_rate: int = 24000) -> bytes:
    """Generate raw 16-bit mono PCM WAV bytes representing silence."""
    num_samples = int(duration_sec * sample_rate)
    silence_pcm = b"\x00\x00" * num_samples

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(silence_pcm)
    return buf.getvalue()


def create_mock_wav_bytes(duration_sec: float = 1.0, sample_rate: int = 24000) -> bytes:
    """Generate a valid 16-bit mono PCM WAV audio buffer for tests/mock mode."""
    num_samples = max(int(duration_sec * sample_rate), int(0.1 * sample_rate))
    freq = 440.0  # gentle A4 pitch
    samples = []
    for i in range(num_samples):
        # Sine wave with exponential decay envelope
        env = math.exp(-2.0 * i / num_samples)
        sample = int(10000 * env * math.sin(2.0 * math.pi * freq * i / sample_rate))
        samples.append(struct.pack("<h", max(-32768, min(32767, sample))))

    pcm_data = b"".join(samples)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def concat_wav_buffers(wav_buffers: List[bytes], pause_sec: float = 0.25, sample_rate: int = 24000) -> bytes:
    """Concatenate multiple WAV audio byte buffers into one WAV with silence pauses."""
    if not wav_buffers:
        return create_mock_wav_bytes(0.5, sample_rate)

    if len(wav_buffers) == 1:
        return wav_buffers[0]

    all_frames = []
    target_sr = sample_rate
    target_nchannels = 1
    target_sampwidth = 2

    silence_frames = b"\x00\x00" * int(pause_sec * sample_rate)

    for i, buf_bytes in enumerate(wav_buffers):
        try:
            with wave.open(io.BytesIO(buf_bytes), "rb") as wf:
                target_sr = wf.getframerate()
                target_nchannels = wf.getnchannels()
                target_sampwidth = wf.getsampwidth()
                frames = wf.readframes(wf.getnframes())
                all_frames.append(frames)
                if i < len(wav_buffers) - 1 and pause_sec > 0:
                    silence_frames = (b"\x00" * target_sampwidth * target_nchannels) * int(pause_sec * target_sr)
                    all_frames.append(silence_frames)
        except Exception:
            # If not valid wav buffer, continue
            continue

    if not all_frames:
        return create_mock_wav_bytes(0.5, sample_rate)

    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as out_wf:
        out_wf.setnchannels(target_nchannels)
        out_wf.setsampwidth(target_sampwidth)
        out_wf.setframerate(target_sr)
        out_wf.writeframes(b"".join(all_frames))

    return out_buf.getvalue()


def validate_audio_file(file_path: Path, max_bytes: int = 25 * 1024 * 1024) -> Tuple[bool, str]:
    """Validate uploaded audio file for reference cloning."""
    if not file_path.exists():
        return False, f"File {file_path} does not exist"

    size = file_path.stat().st_size
    if size == 0:
        return False, "File is empty"
    if size > max_bytes:
        mb = max_bytes // (1024 * 1024)
        return False, f"File size exceeds maximum limit of {mb}MB"

    suffix = file_path.suffix.lower()
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        return False, f"Unsupported audio format '{suffix}'. Allowed: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"

    # Read header magic bytes
    try:
        with open(file_path, "rb") as f:
            header = f.read(12)
        has_magic = any(header.startswith(magic) for magic in AUDIO_HEADER_MAGIC)
        if not has_magic and suffix not in [".m4a"]:
            return False, "File header does not match a valid audio format"
    except Exception as e:
        return False, f"Unable to read audio header: {e}"

    return True, "Valid audio file"
