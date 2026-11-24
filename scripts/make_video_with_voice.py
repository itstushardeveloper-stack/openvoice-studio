#!/usr/bin/env python3
"""
Automated Video + Voice Synthesizer & Merger.

Connects VoiceStudio / Chatterbox text-to-speech with FFmpeg video muxing.
Takes a silent video (e.g. demo_silent.mp4) and a script file (e.g. demo_script.md),
synthesizes 24kHz broadcast audio, and automatically produces the final voiced video (demo_with_voice.mp4).
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure plugin paths are in sys.path
_ROOT = Path(__file__).resolve().parent.parent
for p in [str(_ROOT), str(_ROOT / "plugins" / "voicestudio"), str(_ROOT / "plugins" / "chatterbox")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from plugins.voicestudio.backend.config import config
from plugins.voicestudio.backend.audio_utils import clean_script_for_tts, sanitize_filename
from plugins.voicestudio.backend.engine import engine, GenerationResult
from plugins.voicestudio.backend.languages import validate_and_resolve_language


def find_ffmpeg() -> str:
    """Locate ffmpeg binary on system PATH."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    
    # Common Windows locations
    win_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe",
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
    ]
    for wp in win_paths:
        if wp.exists():
            return str(wp)
            
    return "ffmpeg"


def create_demo_voice_and_video(
    script_path_or_text: str,
    video_input_path: Optional[str] = None,
    output_audio_path: Optional[str] = None,
    output_video_path: Optional[str] = None,
    language: Optional[str] = None,
    voice_profile: Optional[str] = None,
    speed: float = 1.0,
) -> dict:
    """
    1. Read and clean narration script.
    2. Synthesize broadcast-quality 24kHz audio via VoiceStudio.
    3. If video_input_path provided, mux audio and video via FFmpeg.
    """
    # Step 1: Read script text
    p = Path(script_path_or_text)
    if p.exists() and p.is_file():
        with open(p, "r", encoding="utf-8") as f:
            raw_script = f.read()
    else:
        raw_script = script_path_or_text

    cleaned_text = clean_script_for_tts(raw_script)
    if not cleaned_text:
        cleaned_text = raw_script.strip()

    # Step 2: Validate language
    lang_info = validate_and_resolve_language(
        explicit_language=language,
        content_text=cleaned_text,
    )

    print(f"\n=======================================================")
    print(f" VoiceStudio: Processing Narration & Video")
    print(f"=======================================================")
    print(f" Language : {lang_info.name} ({lang_info.code})")
    print(f" Voice    : {voice_profile or 'Standard Narrator'}")

    # Step 3: Synthesize Audio
    gen_result: GenerationResult = engine.synthesize(
        text=cleaned_text,
        language_id=lang_info.code,
        voice_profile=voice_profile,
        title="demo_voice",
    )

    if not gen_result.audio_path:
        print(f"Error: Audio generation skipped ({gen_result.message})", file=sys.stderr)
        return {"status": "error", "message": gen_result.message}

    generated_wav = Path(gen_result.audio_path).resolve()
    print(f" Generated Audio: {generated_wav}")
    print(f" Audio Duration : {gen_result.duration_seconds:.2f} seconds")

    target_audio = generated_wav
    if output_audio_path:
        target_audio = Path(output_audio_path).resolve()
        target_audio.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(generated_wav, target_audio)
        print(f" Saved WAV to   : {target_audio}")

    # Step 4: If video provided, merge with FFmpeg
    merged_video = None
    if video_input_path:
        video_p = Path(video_input_path).resolve()
        if not video_p.exists():
            print(f"Warning: Video file '{video_p}' not found. Audio generated at {target_audio}.")
        else:
            if not output_video_path:
                output_video_path = str(video_p.parent / f"{video_p.stem}_with_voice.mp4")
            merged_video = Path(output_video_path).resolve()
            merged_video.parent.mkdir(parents=True, exist_ok=True)

            ffmpeg_bin = find_ffmpeg()
            print(f"\n Muxing video and voice with FFmpeg...")
            cmd = [
                ffmpeg_bin,
                "-y",
                "-i", str(video_p),
                "-i", str(target_audio),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(merged_video),
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
                print(f" Final Voiced Video: {merged_video}")
            except Exception as e:
                print(f"FFmpeg error: {e}", file=sys.stderr)
                if hasattr(e, "stderr") and e.stderr:
                    print(e.stderr, file=sys.stderr)

    print(f"=======================================================\n")
    return {
        "status": "success",
        "audio_path": str(target_audio),
        "duration_seconds": gen_result.duration_seconds,
        "video_path": str(merged_video) if merged_video else None,
        "message": f"Successfully synthesized voice ({gen_result.duration_seconds:.1f}s)" + (f" and merged into {merged_video}" if merged_video else ""),
    }


def main():
    parser = argparse.ArgumentParser(description="VoiceStudio Video + Voice Merger")
    parser.add_argument("--script", "-s", required=True, help="Path to demo_script.md or raw script text")
    parser.add_argument("--video", "-v", help="Path to silent demo video (e.g. demo_silent.mp4)")
    parser.add_argument("--audio-out", "-a", help="Output WAV path (default: demo.wav)")
    parser.add_argument("--video-out", "-o", help="Output MP4 path (default: demo_with_voice.mp4)")
    parser.add_argument("--lang", "-l", help="Language code (e.g. 'hi', 'en')")
    parser.add_argument("--voice", help="Voice profile name")

    args = parser.parse_args()

    res = create_demo_voice_and_video(
        script_path_or_text=args.script,
        video_input_path=args.video,
        output_audio_path=args.audio_out,
        output_video_path=args.video_out,
        language=args.lang,
        voice_profile=args.voice,
    )
    if res.get("status") != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
