#!/usr/bin/env python3
"""
VoiceStudio CLI (ElevenLabs Alternative).

Unified command-line interface for text-to-speech generation, voice cloning,
voice design, and language validation supporting both local and remote execution.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add plugin directory to path so `backend` package is resolvable from anywhere
_PLUGIN_DIR = Path(__file__).resolve().parent.parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from backend.config import config
from backend.languages import SUPPORTED_LANGUAGES, validate_and_resolve_language
from backend.audio_utils import sanitize_filename


def _run_local_generate(args):
    """Execute speech generation locally using the VoiceStudio engine."""
    from backend.engine import engine

    text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()

    if not text:
        print("Error: No text provided. Use --text or --file.", file=sys.stderr)
        sys.exit(1)

    result = engine.synthesize(
        text=text,
        language_id=args.lang,
        voice_profile=args.voice,
        audio_prompt_path=args.ref,
        exaggeration=args.exaggeration,
        cfg_weight=args.cfg_weight,
        title=args.title,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("\n================ VOICESTUDIO GENERATION ================")
        print(f"Status:        {result.status}")
        print(f"Language:      {result.language_name} ({result.language_id})")
        print(f"Script File:   {result.script_path}")
        if result.audio_path:
            print(f"Audio File:    {result.audio_path}")
            print(f"Duration:      {result.duration_seconds:.2f} seconds")
            print(f"Voice Profile: {result.voice_profile}")
        else:
            print(f"Audio:         NOT GENERATED (Language unsupported)")
        print(f"Message:       {result.message}")
        print("========================================================\n")

    if args.out and result.audio_path:
        out_p = Path(args.out).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copyfile(result.audio_path, out_p)
        print(f"Exported audio to: {out_p}")


def _run_remote_generate(args):
    """Execute speech generation via remote VoiceStudio REST API server."""
    import urllib.request
    import json

    server_url = args.server or config.server_url
    api_key = args.api_key or config.api_key

    text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    payload = json.dumps({
        "text": text,
        "language_id": args.lang,
        "voice_profile": args.voice,
        "audio_prompt_path": args.ref,
        "exaggeration": args.exaggeration,
        "cfg_weight": args.cfg_weight,
        "title": args.title,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{server_url.rstrip('/')}/v1/tts/generate",
        data=payload,
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(description="VoiceStudio AI Voice CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: speak
    speak_parser = subparsers.add_parser("speak", help="Synthesize text to speech")
    speak_parser.add_argument("--text", "-t", help="Text to synthesize")
    speak_parser.add_argument("--file", "-f", help="Input text file path")
    speak_parser.add_argument("--lang", "-l", help="Language code (e.g. 'hi', 'en')")
    speak_parser.add_argument("--voice", "-v", help="Voice profile name")
    speak_parser.add_argument("--ref", "-r", help="Reference audio file for voice cloning")
    speak_parser.add_argument("--title", default="speech", help="Title for output file")
    speak_parser.add_argument("--out", "-o", help="Target output WAV path")
    speak_parser.add_argument("--exaggeration", type=float, default=0.5, help="Emotion scale (0.0 to 1.0)")
    speak_parser.add_argument("--cfg_weight", type=float, default=0.5, help="Guidance weight (0.0 to 1.0)")
    speak_parser.add_argument("--remote", action="store_true", help="Use remote REST server")
    speak_parser.add_argument("--server", help="Remote server URL")
    speak_parser.add_argument("--api-key", help="X-API-Key for authentication")
    speak_parser.add_argument("--json", action="store_true", help="Output JSON result")

    # Subcommand: check-lang
    lang_parser = subparsers.add_parser("check-lang", help="Check language support")
    lang_parser.add_argument("language", help="Language name or code to check")
    lang_parser.add_argument("--content", "-c", help="Text sample to check script")

    # Subcommand: profiles
    subparsers.add_parser("profiles", help="List available voice profiles")

    args = parser.parse_args()

    if args.command == "speak":
        if args.remote:
            _run_remote_generate(args)
        else:
            _run_local_generate(args)
    elif args.command == "check-lang":
        res = validate_and_resolve_language(args.language, args.content)
        print(f"\nLanguage:        {res.name} ({res.code})")
        print(f"Supported:       {res.is_supported}")
        print(f"Detected Script: {res.detected_script}")
        print(f"Can Generate:    {res.can_generate_audio}")
        print(f"Message:         {res.message}\n")
    elif args.command == "profiles":
        from backend.profiles import profile_manager
        profiles = profile_manager.list_profiles()
        print("\nAvailable Voice Profiles:")
        for p in profiles:
            ref = f" (ref: {p.audio_path})" if p.audio_path else ""
            print(f"- {p.name} [{p.gender}, {p.language_tag}]{ref}")
        print("")


if __name__ == "__main__":
    main()
