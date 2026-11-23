# Chatterbox AI Voice Plugin for Claude Code

This directory contains the official **Chatterbox AI Voice Studio Plugin** for Claude Code.

## Plugin Structure

- `.claude-plugin/plugin.json`: Plugin manifest registering metadata and skills.
- `skills/voice-studio/SKILL.md`: Natural-language instruction skill for Claude Code.
- `backend/`: Core Chatterbox Multilingual V3 engine, REST API server, language detection, and profile management.
- `scripts/`: Standalone CLI (`voice_studio_cli.py`) and content pipeline (`content_pipeline.py`).
- `dashboard/`: Interactive Voice Studio web dashboard.
- `tests/`: Automated unit tests covering all components.

## Installation in Claude Code

From the parent marketplace:

```bash
/plugin marketplace add YOUR_USERNAME/chatterbox-claude-marketplace
/plugin install chatterbox@chatterbox-voice-marketplace
```

## How It Works

Once installed, Claude automatically handles voice-over, script generation, and speech synthesis requests in natural language without requiring slash commands.

Claude writes the script in your requested content language (e.g. Hindi in Devanagari script, English, etc.), verifies that Chatterbox Multilingual V3 supports the language, cleans stage directions, invokes the backend engine to synthesize audio, and returns both the Markdown script file and the generated 24kHz WAV audio file.
