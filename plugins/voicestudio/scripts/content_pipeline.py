#!/usr/bin/env python3
"""
Content Pipeline Orchestrator for VoiceStudio & Chatterbox Voice Studio.

Connects script creation with automated language detection, text cleaning,
and speech generation across multiple formats:
- YouTube videos
- YouTube Shorts / Instagram Reels
- Documentaries
- Educational videos
- Podcasts
- Storytelling
- News narration
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

_PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from backend.config import config
from backend.languages import (
    SUPPORTED_LANGUAGES,
    validate_and_resolve_language,
    LanguageValidationResult,
)
from backend.audio_utils import clean_script_for_tts, sanitize_filename
from backend.engine import engine, GenerationResult


# Word-per-minute estimates for duration calculations
WPM_RATES = {
    "youtube": 140,
    "shorts": 160,
    "reels": 160,
    "documentary": 125,
    "educational": 130,
    "storytelling": 120,
    "podcast": 140,
    "news": 150,
}


def calculate_target_word_count(format_type: str, duration_minutes: float) -> int:
    """Calculate target word count based on content format and duration."""
    wpm = WPM_RATES.get(format_type.lower(), 135)
    return int(wpm * duration_minutes)


def execute_content_pipeline(
    script_content: str,
    title: str,
    requested_language: Optional[str] = None,
    content_format: str = "youtube",
    voice_profile: Optional[str] = None,
    audio_ref: Optional[str] = None,
    exaggeration: float = 0.5,
    cfg_weight: float = 0.5,
    output_dir: Optional[str] = None,
) -> Dict:
    """
    Execute complete pipeline:
    1. Validate requested content language against voice engine.
    2. Save formatted script file (.md and .txt).
    3. If language is supported:
       - Clean spoken text (removes visual cues, markdown, parentheticals).
       - Synthesize audio via VoiceStudio / Chatterbox engine.
       - Save WAV audio file.
    4. If language is unsupported (e.g. Gujarati):
       - Preserve script completely in native script.
       - Skip audio synthesis to prevent corrupt output.
       - Explain the limitation clearly.
    5. Return comprehensive result dict with file paths and metadata.
    """
    dest_dir = Path(output_dir).resolve() if output_dir else config.storage_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = sanitize_filename(title.lower().replace(" ", "_"))

    # Language resolution
    lang_info: LanguageValidationResult = validate_and_resolve_language(
        explicit_language=requested_language,
        content_text=script_content,
    )

    # Save complete script as Markdown
    script_md_filename = f"{timestamp}_{safe_title}_script.md"
    script_md_path = dest_dir / script_md_filename

    md_header = f"""# {title}
**Format:** {content_format.title()}  
**Language:** {lang_info.name} (`{lang_info.code}`)  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Voice Profile:** {voice_profile or 'Standard'}  
**Audio Status:** {'Supported & Generated' if lang_info.is_supported else 'Unsupported (Script Preserved)'}

---

"""
    with open(script_md_path, "w", encoding="utf-8") as f:
        f.write(md_header + script_content)

    # Save spoken narration text
    clean_narration = clean_script_for_tts(script_content)
    spoken_txt_filename = f"{timestamp}_{safe_title}_narration.txt"
    spoken_txt_path = dest_dir / spoken_txt_filename
    with open(spoken_txt_path, "w", encoding="utf-8") as f:
        f.write(clean_narration)

    result_summary = {
        "title": title,
        "format": content_format,
        "language_name": lang_info.name,
        "language_code": lang_info.code,
        "language_supported": lang_info.is_supported,
        "detected_script": lang_info.detected_script,
        "script_md_path": str(script_md_path),
        "spoken_txt_path": str(spoken_txt_path),
        "audio_path": None,
        "audio_duration_seconds": 0.0,
        "status": "pending",
        "message": "",
    }

    if not lang_info.is_supported:
        result_summary["status"] = "script_saved_audio_unsupported"
        result_summary["message"] = lang_info.message
        return result_summary

    # Synthesize audio
    gen_result: GenerationResult = engine.synthesize(
        text=clean_narration,
        language_id=lang_info.code,
        voice_profile=voice_profile,
        audio_prompt_path=audio_ref,
        exaggeration=exaggeration,
        cfg_weight=cfg_weight,
        title=safe_title,
    )

    result_summary["audio_path"] = gen_result.audio_path
    result_summary["audio_duration_seconds"] = gen_result.duration_seconds
    result_summary["status"] = "success"
    result_summary["message"] = f"Script and audio generated successfully in {lang_info.name} ({gen_result.duration_seconds:.1f}s)."

    return result_summary


def main():
    parser = argparse.ArgumentParser(description="VoiceStudio Content & Audio Pipeline")
    parser.add_argument("--title", "-t", required=True, help="Title of the script")
    parser.add_argument("--file", "-f", help="Script input text file")
    parser.add_argument("--script", "-s", help="Inline script content")
    parser.add_argument("--lang", "-l", help="Content language (e.g. 'hi', 'en', 'gu')")
    parser.add_argument("--format", default="youtube", help="Content format (youtube, shorts, reels, documentary, podcast)")
    parser.add_argument("--voice", help="Voice profile name")
    parser.add_argument("--ref", help="Reference audio for voice cloning")
    parser.add_argument("--out-dir", help="Output directory")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    content = args.script
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()

    if not content:
        print("Error: Provide script content via --script or --file", file=sys.stderr)
        sys.exit(1)

    result = execute_content_pipeline(
        script_content=content,
        title=args.title,
        requested_language=args.lang,
        content_format=args.format,
        voice_profile=args.voice,
        audio_ref=args.ref,
        output_dir=args.out_dir,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n" + "=" * 60)
        print(f" VoiceStudio Content Generation: {result['title']}")
        print("=" * 60)
        print(f" Language : {result['language_name']} ({result['language_code']})")
        print(f" Status   : {result['status']}")
        print(f" Script MD: {result['script_md_path']}")
        print(f" Spoken TX: {result['spoken_txt_path']}")
        if result['audio_path']:
            print(f" Audio WAV: {result['audio_path']} ({result['audio_duration_seconds']:.1f}s)")
        print(f" Message  : {result['message']}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
