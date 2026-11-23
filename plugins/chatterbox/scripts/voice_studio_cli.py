#!/usr/bin/env python3
"""
Chatterbox Voice Studio CLI.

Unified command-line interface for text-to-speech generation, voice cloning,
and language validation supporting both local and remote execution.
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
    """Execute speech generation locally using the Chatterbox engine."""
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
        print("\n================ CHATTERBOX VOICE GENERATION ================")
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
        print("=============================================================\n")

    if args.out and result.audio_path:
        out_p = Path(args.out).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copyfile(result.audio_path, out_p)
        print(f"Exported audio to: {out_p}")


def _run_remote_generate(args):
    """Execute speech generation via remote Chatterbox REST API server."""
    try:
        import requests
    except ImportError:
        print("Error: 'requests' package required for remote mode.", file=sys.stderr)
        sys.exit(1)

    server_url = args.server or config.server_url
    api_key = args.api_key or config.api_key

    text = args.text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    payload = {
        "text": text,
        "language_id": args.lang,
        "voice_profile": args.voice,
        "audio_prompt_path": args.ref,
        "exaggeration": args.exaggeration,
        "cfg_weight": args.cfg_weight,
        "title": args.title,
    }

    try:
        res = requests.post(f"{server_url.rstrip('/')}/v1/tts/generate", json=payload, headers=headers, timeout=120)
        res.raise_for_status()
        data = res.json()

        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print("\n================ CHATTERBOX REMOTE GENERATION ================")
            print(f"Status:        {data.get('status')}")
            print(f"Language:      {data.get('language_name')} ({data.get('language_id')})")
            print(f"Audio URL:     {server_url.rstrip('/')}{data.get('audio_url') if data.get('audio_url') else 'N/A'}")
            print(f"Duration:      {data.get('duration_seconds')} seconds")
            print(f"Message:       {data.get('message')}")
            print("==============================================================\n")

        # Download file if output path specified
        if args.out and data.get("audio_url"):
            audio_dl_url = f"{server_url.rstrip('/')}{data.get('audio_url')}"
            dl_res = requests.get(audio_dl_url, headers=headers, timeout=60)
            dl_res.raise_for_status()
            out_p = Path(args.out).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "wb") as f:
                f.write(dl_res.content)
            print(f"Downloaded audio to: {out_p}")

    except Exception as e:
        print(f"Error calling remote server: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_generate(args):
    """Route generate command based on local or remote configuration."""
    is_remote = args.remote or config.mode == "remote"
    if is_remote:
        _run_remote_generate(args)
    else:
        _run_local_generate(args)


def cmd_check_language(args):
    """Validate requested language code or name and verify speech model support."""
    res = validate_and_resolve_language(
        explicit_language=args.lang,
        content_text=args.text,
    )
    if args.json:
        print(json.dumps({
            "code": res.code,
            "name": res.name,
            "is_supported": res.is_supported,
            "detected_script": res.detected_script,
            "can_generate_audio": res.can_generate_audio,
            "message": res.message,
        }, indent=2))
    else:
        print(f"\nLanguage: {res.name} (Code: '{res.code}')")
        print(f"Supported by Chatterbox V3: {'YES' if res.is_supported else 'NO'}")
        if res.detected_script:
            print(f"Detected Script: {res.detected_script}")
        print(f"Details: {res.message}\n")


def cmd_list_languages(args):
    """List all supported languages."""
    if args.json:
        print(json.dumps(SUPPORTED_LANGUAGES, indent=2))
    else:
        print("\nChatterbox Multilingual V3 Supported Languages (23 Total):")
        print("-" * 50)
        for code, name in sorted(SUPPORTED_LANGUAGES.items()):
            star = " (Primary)" if code in ("hi", "en") else ""
            print(f"  {code:4s} -> {name}{star}")
        print("-" * 50 + "\n")


def cmd_list_profiles(args):
    """List saved voice cloning profiles."""
    from backend.profiles import profile_manager
    profiles = profile_manager.list_profiles()
    if args.json:
        print(json.dumps([p.to_dict() for p in profiles], indent=2))
    else:
        print("\nAvailable Chatterbox Voice Profiles:")
        print("-" * 65)
        for p in profiles:
            ref = "Ref audio: YES" if p.audio_path else "Built-in"
            auth = "Authorized: YES" if p.authorized else "Unauthorized"
            print(f"  • {p.name:<26s} | {p.gender:<7s} | {p.language_tag:<5s} | {ref}")
            if p.description:
                print(f"    {p.description}")
        print("-" * 65 + "\n")


def cmd_clone_voice(args):
    """Create a new voice cloning profile from reference audio with authorization check."""
    if not args.authorized:
        print(
            "Error: Voice cloning requires explicit authorization. Pass --authorized "
            "to confirm ownership or authorized permission to use the reference recording.",
            file=sys.stderr,
        )
        sys.exit(1)

    ref_audio = Path(args.audio).resolve()
    if not ref_audio.exists():
        print(f"Error: Reference audio file '{ref_audio}' does not exist.", file=sys.stderr)
        sys.exit(1)

    from backend.profiles import profile_manager
    try:
        profile = profile_manager.create_profile(
            name=args.name,
            audio_file_path=ref_audio,
            authorized=True,
            gender=args.gender or "neutral",
            language_tag=args.lang or "multilingual",
            description=args.description or "",
        )
        print(f"\nSuccessfully created voice profile '{profile.name}'!")
        print(f"Language: {profile.language_tag}")
        print(f"Stored audio: {profile.audio_path}\n")
    except Exception as e:
        print(f"Error creating profile: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_server_health(args):
    """Check status of local or remote Chatterbox API server."""
    server_url = args.server or config.server_url
    try:
        import requests
        res = requests.get(f"{server_url.rstrip('/')}/health", timeout=5)
        res.raise_for_status()
        data = res.json()
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Server check failed ({server_url}): {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Chatterbox AI Voice Studio CLI - Multilingual TTS & Voice Cloning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Command to run")

    # Generate subcommand
    gen_parser = subparsers.add_parser("generate", help="Synthesize audio from text or script file")
    gen_parser.add_argument("--text", "-t", type=str, help="Text to speak")
    gen_parser.add_argument("--file", "-f", type=str, help="Path to text or markdown script file")
    gen_parser.add_argument("--lang", "-l", type=str, help="Language code or name (e.g. 'hi', 'en', 'es')")
    gen_parser.add_argument("--voice", "-v", type=str, help="Voice profile name")
    gen_parser.add_argument("--ref", type=str, help="Direct path to reference audio file for zero-shot cloning")
    gen_parser.add_argument("--exaggeration", type=float, default=0.5, help="Emotion / expressiveness (0.0 to 1.0)")
    gen_parser.add_argument("--cfg-weight", type=float, default=0.5, help="CFG weight (0.0 to 1.0)")
    gen_parser.add_argument("--title", type=str, default="narration", help="Title for output files")
    gen_parser.add_argument("--out", "-o", type=str, help="Export output WAV file path")
    gen_parser.add_argument("--remote", action="store_true", help="Force remote API inference")
    gen_parser.add_argument("--server", type=str, help="Remote server URL (e.g. https://your-server:8000)")
    gen_parser.add_argument("--api-key", type=str, help="API key for remote server")
    gen_parser.add_argument("--json", action="store_true", help="Output JSON response")
    gen_parser.set_defaults(func=cmd_generate)

    # Check language subcommand
    chk_parser = subparsers.add_parser("check-lang", help="Verify language support in Chatterbox V3")
    chk_parser.add_argument("--lang", "-l", type=str, help="Language code or name")
    chk_parser.add_argument("--text", "-t", type=str, help="Optional text content to detect script")
    chk_parser.add_argument("--json", action="store_true", help="Output JSON response")
    chk_parser.set_defaults(func=cmd_check_language)

    # List languages subcommand
    list_langs_parser = subparsers.add_parser("list-languages", help="List all 23 supported languages")
    list_langs_parser.add_argument("--json", action="store_true", help="Output JSON response")
    list_langs_parser.set_defaults(func=cmd_list_languages)

    # List profiles subcommand
    list_prof_parser = subparsers.add_parser("list-profiles", help="List saved voice profiles")
    list_prof_parser.add_argument("--json", action="store_true", help="Output JSON response")
    list_prof_parser.set_defaults(func=cmd_list_profiles)

    # Clone voice subcommand
    clone_parser = subparsers.add_parser("clone-voice", help="Register a new voice profile from reference audio")
    clone_parser.add_argument("--name", "-n", type=str, required=True, help="Unique profile name")
    clone_parser.add_argument("--audio", "-a", type=str, required=True, help="Path to 5-15s reference WAV/MP3 clip")
    clone_parser.add_argument("--gender", type=str, default="neutral", choices=["male", "female", "neutral"])
    clone_parser.add_argument("--lang", type=str, default="multilingual", help="Primary language for this voice")
    clone_parser.add_argument("--description", "-d", type=str, default="", help="Description notes for the voice")
    clone_parser.add_argument("--authorized", action="store_true", help="Confirm authorization to clone this voice")
    clone_parser.set_defaults(func=cmd_clone_voice)

    # Server health subcommand
    health_parser = subparsers.add_parser("server-health", help="Check status of Chatterbox API server")
    health_parser.add_argument("--server", type=str, help="Server URL to check")
    health_parser.set_defaults(func=cmd_server_health)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
