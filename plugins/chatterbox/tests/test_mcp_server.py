"""Tests for Chatterbox & VoiceStudio Model Context Protocol (MCP) Server and JSON-RPC tools."""

import json
from pathlib import Path
import pytest

from backend.mcp_server import (
    handle_initialize,
    handle_tools_list,
    handle_tool_call,
    process_message,
    TOOLS_SCHEMA,
    SERVER_NAME,
    PROTOCOL_VERSION,
)
from backend.audio_utils import create_mock_wav_bytes


def test_mcp_initialize():
    """Verify MCP initialization handshake."""
    res = handle_initialize({"protocolVersion": PROTOCOL_VERSION})
    assert res["protocolVersion"] == PROTOCOL_VERSION
    assert res["serverInfo"]["name"] == SERVER_NAME
    assert "tools" in res["capabilities"]


def test_mcp_tools_list():
    """Verify Chatterbox & VoiceStudio MCP tools are declared."""
    res = handle_tools_list()
    assert "tools" in res
    tools = res["tools"]
    tool_names = [t["name"] for t in tools]

    expected_tools = [
        "chatterbox_content_pipeline",
        "voicestudio_content_pipeline",
        "chatterbox_generate_speech",
        "voicestudio_generate_speech",
        "chatterbox_check_language",
        "voicestudio_check_language",
        "chatterbox_list_profiles",
        "voicestudio_list_profiles",
        "chatterbox_clone_voice",
        "voicestudio_clone_voice",
        "chatterbox_get_status",
        "voicestudio_get_status",
    ]
    for et in expected_tools:
        assert et in tool_names, f"Tool {et} must be in tools/list"

    # Verify input schema format for each tool
    for t in tools:
        assert "inputSchema" in t
        assert t["inputSchema"].get("type") == "object"
        assert "description" in t


def test_mcp_tool_check_language_hindi():
    """Verify chatterbox_check_language tool for supported Hindi."""
    res = handle_tool_call("chatterbox_check_language", {"language": "Hindi"})
    assert res["isError"] is False
    data = json.loads(res["content"][0]["text"])
    assert data["code"] == "hi"
    assert data["is_supported"] is True
    assert data["can_generate_audio"] is True


def test_mcp_tool_check_language_gujarati():
    """Verify chatterbox_check_language tool for unsupported Gujarati."""
    res = handle_tool_call("chatterbox_check_language", {"language": "Gujarati"})
    assert res["isError"] is False
    data = json.loads(res["content"][0]["text"])
    assert data["code"] == "gu"
    assert data["is_supported"] is False
    assert data["can_generate_audio"] is False
    assert "NOT supported" in data["message"]


def test_mcp_tool_generate_speech(setup_test_environment):
    """Verify chatterbox_generate_speech tool synthesizes speech."""
    args = {
        "text": "Welcome to Chatterbox AI Voice Studio MCP integration.",
        "language_id": "en",
        "title": "MCP_Test_Narration",
    }
    res = handle_tool_call("chatterbox_generate_speech", args)
    assert res["isError"] is False
    data = json.loads(res["content"][0]["text"])
    assert data["status"] == "completed"
    assert data["language_id"] == "en"
    assert data["audio_path"] is not None
    assert Path(data["audio_path"]).exists()


def test_mcp_tool_content_pipeline_hindi(setup_test_environment):
    """Verify chatterbox_content_pipeline tool generates Hindi script and audio."""
    script = (
        "# AI क्रांति\n\n"
        "[Visual: भविष्य का शहर]\n"
        "नमस्ते दोस्तों! आर्टिफिशियल इंटेलिजेंस आज हमारे जीवन को तेजी से बदल रहा है।"
    )
    args = {
        "title": "Hindi_AI_Pipeline",
        "script_content": script,
        "language": "hi",
        "format": "youtube",
    }
    res = handle_tool_call("chatterbox_content_pipeline", args)
    assert res["isError"] is False
    data = json.loads(res["content"][0]["text"])
    assert data["status"] == "success"
    assert data["language_code"] == "hi"
    assert data["audio_path"] is not None
    assert Path(data["audio_path"]).exists()
    assert Path(data["script_md_path"]).exists()


def test_mcp_tool_content_pipeline_gujarati_unsupported(setup_test_environment):
    """Verify pipeline safely handles unsupported Gujarati without generating corrupt audio."""
    gujarati_script = "નમસ્તે મિત્રો, આર્ટિફિશિયલ ઇન્ટેલિજન્સ વિશે આજના વિડિયોમાં તમારું સ્વાગત છે."
    args = {
        "title": "Gujarati_Reel",
        "script_content": gujarati_script,
        "language": "gu",
        "format": "reels",
    }
    res = handle_tool_call("chatterbox_content_pipeline", args)
    assert res["isError"] is False
    data = json.loads(res["content"][0]["text"])
    assert data["status"] == "script_saved_audio_unsupported"
    assert data["audio_path"] is None
    assert Path(data["script_md_path"]).exists()
    assert "NOT supported" in data["message"]


def test_mcp_tool_list_profiles(test_profile_manager):
    """Verify chatterbox_list_profiles returns available profiles."""
    res = handle_tool_call("chatterbox_list_profiles", {})
    assert res["isError"] is False
    profiles = json.loads(res["content"][0]["text"])
    assert isinstance(profiles, list)
    names = [p["name"] for p in profiles]
    assert "standard_hindi_narrator" in names
    assert "standard_english_narrator" in names


def test_mcp_tool_get_status():
    """Verify chatterbox_get_status tool returns runtime metadata."""
    res = handle_tool_call("chatterbox_get_status", {})
    assert res["isError"] is False
    data = json.loads(res["content"][0]["text"])
    assert data["status"] == "online"
    assert "device" in data
    assert "storage_dir" in data


def test_mcp_process_message_jsonrpc_protocol():
    """Verify end-to-end JSON-RPC 2.0 message dispatching."""
    req = {
        "jsonrpc": "2.0",
        "id": "req-1",
        "method": "tools/call",
        "params": {
            "name": "chatterbox_check_language",
            "arguments": {"language": "English"},
        },
    }
    resp = process_message(req)
    assert resp is not None
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == "req-1"
    assert "result" in resp
    assert resp["result"]["isError"] is False
