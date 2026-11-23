"""Tests for Claude Code Marketplace and Plugin manifests."""

import json
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[3]
MARKETPLACE_JSON = ROOT_DIR / ".claude-plugin" / "marketplace.json"
PLUGIN_JSON = ROOT_DIR / "plugins" / "chatterbox" / ".claude-plugin" / "plugin.json"
SKILL_MD = ROOT_DIR / "plugins" / "chatterbox" / "skills" / "voice-studio" / "SKILL.md"


def test_marketplace_manifest_exists_and_valid():
    """Verify .claude-plugin/marketplace.json is valid and contains chatterbox plugin."""
    assert MARKETPLACE_JSON.exists(), f"Marketplace manifest missing at {MARKETPLACE_JSON}"

    with open(MARKETPLACE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("name") == "chatterbox-voice-marketplace"
    assert "version" in data
    assert "description" in data
    assert "plugins" in data
    assert isinstance(data["plugins"], list)

    plugin_names = [p.get("name") for p in data["plugins"]]
    assert "chatterbox" in plugin_names, "chatterbox plugin must be registered in marketplace.json"

    # Verify source directory points to existing plugins/chatterbox
    chatterbox_entry = next(p for p in data["plugins"] if p["name"] == "chatterbox")
    source_path = ROOT_DIR / chatterbox_entry["source"]
    assert source_path.exists(), f"Source path {source_path} does not exist"


def test_plugin_manifest_exists_and_valid():
    """Verify plugins/chatterbox/.claude-plugin/plugin.json is valid."""
    assert PLUGIN_JSON.exists(), f"Plugin manifest missing at {PLUGIN_JSON}"

    with open(PLUGIN_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("name") == "chatterbox"
    assert "version" in data
    assert "description" in data
    assert "skills" in data
    assert isinstance(data["skills"], list)

    # Check skills resolution
    plugin_dir = PLUGIN_JSON.parent.parent
    for skill_rel in data["skills"]:
        skill_path = (plugin_dir / skill_rel / "SKILL.md").resolve()
        assert skill_path.exists(), f"Declared skill {skill_path} does not exist"


def test_skill_instructions_and_triggers():
    """Verify SKILL.md has valid frontmatter and required trigger guidelines."""
    assert SKILL_MD.exists(), f"SKILL.md missing at {SKILL_MD}"

    content = SKILL_MD.read_text(encoding="utf-8")
    assert content.startswith("---"), "SKILL.md must begin with YAML frontmatter"

    # Check frontmatter fields
    parts = content.split("---", 2)
    assert len(parts) >= 3, "Frontmatter must be delimited by ---"
    frontmatter = parts[1]
    assert "name: voice-studio" in frontmatter
    assert "description:" in frontmatter

    # Verify key natural-language requirements and absence of mandatory slash commands
    body = parts[2]
    assert "NO SLASH COMMANDS REQUIRED" in body
    assert "Hindi" in body
    assert "English" in body
    assert "Gujarati" in body
    assert "Devanagari" in body
    assert "Chatterbox Multilingual V3" in body
