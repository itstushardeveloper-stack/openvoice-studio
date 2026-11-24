"""
VoiceStudio & Chatterbox Voice Studio - Model Context Protocol (MCP) Server.

Provides native stdio JSON-RPC 2.0 tools for Claude Code and Claude Desktop
to synthesize speech, check language support, manage voice profiles, design voices,
and execute the end-to-end content pipeline.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure parent package directories are resolvable
_BACKEND_DIR = Path(__file__).resolve().parent
_PLUGIN_DIR = _BACKEND_DIR.parent
for _p in [str(_PLUGIN_DIR), str(_BACKEND_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from backend.config import config
from backend.languages import (
    SUPPORTED_LANGUAGES,
    validate_and_resolve_language,
)
from backend.profiles import profile_manager
from backend.engine import engine, GenerationResult
from scripts.content_pipeline import execute_content_pipeline

# Configure stderr logging (stdout is strictly reserved for JSON-RPC messages)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [VoiceStudio MCP] %(message)s",
)
logger = logging.getLogger("voicestudio.mcp")

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "voicestudio-voice-engine"
SERVER_VERSION = "1.2.0"

# Tool Definitions
TOOLS_SCHEMA = [
    {
        "name": "voicestudio_content_pipeline",
        "description": (
            "Complete script & audio pipeline: Saves script (.md and .txt), checks language support "
            "against the multilingual voice engine (supports Hindi in Devanagari, English, and 646 languages; "
            "safely preserves unsupported languages like Gujarati without audio corruption), "
            "cleans stage cues, synthesizes 24kHz master WAV audio, and returns full file paths."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the script / episode (e.g. 'Hindi AI Revolution')",
                },
                "script_content": {
                    "type": "string",
                    "description": "Full script text written in the target language (e.g. Hindi in Devanagari script, English, etc.)",
                },
                "language": {
                    "type": "string",
                    "description": "Target language code or name (e.g. 'hi' for Hindi, 'en' for English, 'gu' for Gujarati)",
                },
                "format": {
                    "type": "string",
                    "enum": ["youtube", "shorts", "reels", "documentary", "podcast", "storytelling", "news"],
                    "description": "Content format type",
                    "default": "youtube",
                },
                "voice_profile": {
                    "type": "string",
                    "description": "Voice profile name (e.g. 'standard_hindi_narrator', 'standard_english_narrator', 'conversational_turbo')",
                },
                "audio_ref": {
                    "type": "string",
                    "description": "Optional direct path to reference audio clip for zero-shot cloning",
                },
            },
            "required": ["title", "script_content"],
        },
    },
    {
        "name": "chatterbox_content_pipeline",
        "description": "Compatibility alias for voicestudio_content_pipeline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "script_content": {"type": "string"},
                "language": {"type": "string"},
                "format": {"type": "string"},
                "voice_profile": {"type": "string"},
                "audio_ref": {"type": "string"},
            },
            "required": ["title", "script_content"],
        },
    },
    {
        "name": "voicestudio_generate_speech",
        "description": "Synthesize speech audio (24kHz WAV) from plain narration text using VoiceStudio / Chatterbox.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Clean spoken dialogue or narration text to synthesize",
                },
                "language_id": {
                    "type": "string",
                    "description": "Language code or name (e.g. 'hi' for Hindi, 'en' for English). Auto-detected if omitted.",
                },
                "voice_profile": {
                    "type": "string",
                    "description": "Saved voice profile name",
                },
                "title": {
                    "type": "string",
                    "description": "Title or filename prefix for the audio output",
                    "default": "narration",
                },
                "exaggeration": {
                    "type": "number",
                    "description": "Emotion / expressiveness scale (0.0 to 1.0)",
                    "default": 0.5,
                },
                "cfg_weight": {
                    "type": "number",
                    "description": "Classifier-free guidance weight (0.0 to 1.0)",
                    "default": 0.5,
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "chatterbox_generate_speech",
        "description": "Compatibility alias for voicestudio_generate_speech.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "language_id": {"type": "string"},
                "voice_profile": {"type": "string"},
                "title": {"type": "string"},
                "exaggeration": {"type": "number"},
                "cfg_weight": {"type": "number"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "voicestudio_check_language",
        "description": "Verify whether a requested content language or script is supported by the voice synthesis engine.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "Language code or name (e.g. 'Hindi', 'hi', 'Gujarati', 'gu', 'English', 'en')",
                },
                "content": {
                    "type": "string",
                    "description": "Optional text snippet to auto-detect writing script (Devanagari, Gujarati, Latin, etc.)",
                },
            },
        },
    },
    {
        "name": "chatterbox_check_language",
        "description": "Compatibility alias for voicestudio_check_language.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "language": {"type": "string"},
                "content": {"type": "string"},
            },
        },
    },
    {
        "name": "voicestudio_list_profiles",
        "description": "List all available voice profiles (standard built-ins, designed voices, and cloned voices).",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "chatterbox_list_profiles",
        "description": "Compatibility alias for voicestudio_list_profiles.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "voicestudio_clone_voice",
        "description": "Register a new voice cloning profile from reference audio with mandatory ethical authorization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique profile identifier (e.g. 'my_narrator')",
                },
                "audio_path": {
                    "type": "string",
                    "description": "Path to 5-15s clean reference WAV/MP3 clip",
                },
                "authorized": {
                    "type": "boolean",
                    "description": "Explicit affirmation that user owns or is authorized to clone this voice",
                },
                "gender": {
                    "type": "string",
                    "enum": ["male", "female", "neutral"],
                    "default": "neutral",
                },
                "language": {
                    "type": "string",
                    "default": "multilingual",
                },
                "description": {
                    "type": "string",
                    "default": "",
                },
            },
            "required": ["name", "audio_path", "authorized"],
        },
    },
    {
        "name": "chatterbox_clone_voice",
        "description": "Compatibility alias for voicestudio_clone_voice.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "audio_path": {"type": "string"},
                "authorized": {"type": "boolean"},
                "gender": {"type": "string"},
                "language": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["name", "audio_path", "authorized"],
        },
    },
    {
        "name": "voicestudio_design_voice",
        "description": "Create a synthetic voice profile from text description attributes (ElevenLabs Voice Design alternative).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique profile identifier for the new voice",
                },
                "description": {
                    "type": "string",
                    "description": "Free-form description (e.g. 'middle-aged male with calm, deep British accent')",
                },
                "language": {
                    "type": "string",
                    "description": "Target language ISO code or 'Auto'",
                    "default": "Auto",
                },
            },
            "required": ["name", "description"],
        },
    },
    {
        "name": "voicestudio_get_status",
        "description": "Get VoiceStudio runtime status, active compute device, and storage directories.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "chatterbox_get_status",
        "description": "Compatibility alias for voicestudio_get_status.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP initialize handshake."""
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
        "capabilities": {
            "tools": {},
        },
    }


def handle_tools_list() -> Dict[str, Any]:
    """Return available MCP tools."""
    return {"tools": TOOLS_SCHEMA}


def handle_tool_call(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute requested MCP tool and return formatted result."""
    try:
        if name in ("voicestudio_content_pipeline", "chatterbox_content_pipeline"):
            result = execute_content_pipeline(
                script_content=arguments.get("script_content", ""),
                title=arguments.get("title", "Voice_Narration"),
                requested_language=arguments.get("language"),
                content_format=arguments.get("format", "youtube"),
                voice_profile=arguments.get("voice_profile"),
                audio_ref=arguments.get("audio_ref"),
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, ensure_ascii=False),
                    }
                ],
                "isError": False,
            }

        elif name in ("voicestudio_generate_speech", "chatterbox_generate_speech"):
            gen_res: GenerationResult = engine.synthesize(
                text=arguments.get("text", ""),
                language_id=arguments.get("language_id"),
                voice_profile=arguments.get("voice_profile"),
                exaggeration=float(arguments.get("exaggeration", 0.5)),
                cfg_weight=float(arguments.get("cfg_weight", 0.5)),
                title=arguments.get("title", "narration"),
            )
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(gen_res.to_dict(), indent=2, ensure_ascii=False),
                    }
                ],
                "isError": False,
            }

        elif name in ("voicestudio_check_language", "chatterbox_check_language"):
            res = validate_and_resolve_language(
                explicit_language=arguments.get("language"),
                content_text=arguments.get("content"),
            )
            data = {
                "code": res.code,
                "name": res.name,
                "is_supported": res.is_supported,
                "detected_script": res.detected_script,
                "can_generate_audio": res.can_generate_audio,
                "message": res.message,
            }
            return {
                "content": [
                    {"type": "text", "text": json.dumps(data, indent=2, ensure_ascii=False)}
                ],
                "isError": False,
            }

        elif name in ("voicestudio_list_profiles", "chatterbox_list_profiles"):
            profiles = profile_manager.list_profiles()
            data = [p.to_dict() for p in profiles]
            return {
                "content": [
                    {"type": "text", "text": json.dumps(data, indent=2, ensure_ascii=False)}
                ],
                "isError": False,
            }

        elif name in ("voicestudio_clone_voice", "chatterbox_clone_voice", "clone_voice"):
            prof = profile_manager.create_profile(
                name=arguments["name"],
                audio_file_path=Path(arguments["audio_path"]),
                authorized=bool(arguments.get("authorized", False)),
                gender=arguments.get("gender", "neutral"),
                language_tag=arguments.get("language", "multilingual"),
                description=arguments.get("description", ""),
            )
            return {
                "content": [
                    {"type": "text", "text": json.dumps(prof.to_dict(), indent=2, ensure_ascii=False)}
                ],
                "isError": False,
            }

        elif name in ("voicestudio_design_voice", "design_voice"):
            prof = engine.design_voice(
                name=arguments["name"],
                description=arguments["description"],
                language=arguments.get("language", "Auto"),
            )
            return {
                "content": [
                    {"type": "text", "text": json.dumps(prof.to_dict(), indent=2, ensure_ascii=False)}
                ],
                "isError": False,
            }

        elif name in ("voicestudio_get_status", "chatterbox_get_status", "check_health"):
            status_data = {
                "status": "online",
                "engine": "VoiceStudio (ElevenLabs Alternative) & Chatterbox V3",
                "device": config.resolve_device(),
                "storage_dir": str(config.storage_dir),
                "profiles_dir": str(config.profiles_dir),
                "supported_languages_count": len(SUPPORTED_LANGUAGES),
                "mock_inference": config.mock_inference,
            }
            return {
                "content": [
                    {"type": "text", "text": json.dumps(status_data, indent=2, ensure_ascii=False)}
                ],
                "isError": False,
            }

        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {name}"}],
                "isError": True,
            }

    except Exception as exc:
        logger.exception(f"Error executing tool {name}: {exc}")
        return {
            "content": [{"type": "text", "text": f"Tool execution failed: {str(exc)}"}],
            "isError": True,
        }


def process_message(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process single JSON-RPC 2.0 message."""
    msg_id = msg.get("id")
    method = msg.get("method")
    params = msg.get("params", {})

    if not method:
        return None

    if method == "initialize":
        result = handle_initialize(params)
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    elif method == "notifications/initialized":
        logger.info("Client completed MCP initialization.")
        return None

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

    elif method == "tools/list":
        result = handle_tools_list()
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        result = handle_tool_call(tool_name, arguments)
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    else:
        logger.warning(f"Unrecognized MCP method: {method}")
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def run_stdio_server():
    """Run standard I/O JSON-RPC loop for Claude Code and Claude Desktop."""
    logger.info("Starting VoiceStudio MCP server over stdio...")

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Malformed JSON on stdin: {e}")
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
                continue

            response = process_message(msg)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()

        except KeyboardInterrupt:
            break
        except Exception as exc:
            logger.exception(f"Unhandled error in stdio server loop: {exc}")
            break

    logger.info("VoiceStudio MCP server shutting down.")


if __name__ == "__main__":
    run_stdio_server()
