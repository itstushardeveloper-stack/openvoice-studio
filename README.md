# OpenVoice Studio — Claude Code Marketplace

[![CI](https://github.com/itstushardeveloper-stack/openvoice-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/itstushardeveloper-stack/openvoice-studio/actions/workflows/ci.yml)
[![License: AGPL-3.0 / MIT](https://img.shields.io/badge/License-AGPL--3.0%20%2F%20MIT-purple.svg)](LICENSE)
[![VoiceStudio: ElevenLabs Alternative](https://img.shields.io/badge/VoiceStudio-ElevenLabs%20Alternative-gradient.svg)](https://github.com/debpalash/voicestudio)
[![Chatterbox: Multilingual V3](https://img.shields.io/badge/Chatterbox-Multilingual%20V3-blue.svg)](https://github.com/resemble-ai/chatterbox)
[![Claude Code: Plugin Ready](https://img.shields.io/badge/Claude%20Code-Marketplace%20Plugin-green.svg)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code)

A complete, production-grade **Claude Code Marketplace & AI Voice Studio** integrating **[VoiceStudio](https://github.com/debpalash/voicestudio)** (the open-source ElevenLabs alternative for voice cloning, voice design, and 646 languages) and **[Chatterbox](https://github.com/resemble-ai/chatterbox)** Multilingual V3.

---

## 🌟 Key Architecture & Responsibilities

This integration combines the creative scriptwriting of Claude with the acoustic fidelity of local VoiceStudio and Chatterbox engines:

$$\text{User Request} \longrightarrow \underbrace{\text{Claude (Script Authoring)}}_{\text{Prompt, Format, Language, Pacing}} \longrightarrow \underbrace{\text{VoiceStudio Engine}}_{\text{Acoustic Modeling, Multilingual TTS, Voice Cloning/Design}} \longrightarrow \text{24kHz Master WAV Audio}$$

- **Claude Writes the Script:** Generates tailored, format-specific scripts (YouTube videos, Shorts, Instagram Reels, Documentaries, Podcasts, Explainer videos, Storytelling, News).
- **VoiceStudio Synthesizes the Audio:** Converts spoken dialogue into broadcast-quality 24 kHz WAV audio with voice cloning, voice design, and zero-latency local synthesis.
- **Natural Language Interaction:** **No slash commands required!** You do not need to memorize commands like `/voice-studio` or `/chatterbox:speak`. Normal conversational requests trigger the full pipeline automatically.
- **Native MCP Server:** Direct stdio JSON-RPC tool calling for Claude Code and Claude Desktop (`voicestudio_content_pipeline`, `voicestudio_generate_speech`, `voicestudio_check_language`, `voicestudio_clone_voice`, `voicestudio_design_voice`).

---

## ⚡ Quick Start: Marketplace Installation

Install directly into your Claude Code environment using the official marketplace commands:

```bash
# 1. Add this repository as a Claude Code marketplace
/plugin marketplace add YOUR_USERNAME/openvoice-studio

# 2. Install VoiceStudio (open-source ElevenLabs alternative)
/plugin install voicestudio@openvoice-studio

# (Optional) You can also install the Chatterbox engine plugin
/plugin install chatterbox@openvoice-studio
```

---

## 🗣️ Automatic Content Language Detection

The plugin detects the language of the **CONTENT** you want to generate, not merely the language of your prompt to Claude.

### Real-World Examples

#### 1. Hindi YouTube Video Script & Voice-Over
```
User: "Claude, create a 5-minute Hindi YouTube video script about artificial intelligence and generate voice-over."
```
**Outcome:**
1. Writes the full script in natural, culturally resonant Hindi using **Devanagari script**.
2. Cleans stage directions (`[Visual: ...]`, `(Music in)`, Hindi `दृश्य:`) from spoken narration.
3. Synthesizes Hindi audio (`language_id="hi"`).
4. Saves both `Hindi_AI_script.md` and `Hindi_AI.wav`.
5. Returns direct clickable links to both files.

#### 2. English Documentary Script & Narration
```
User: "Create an English documentary script about deep space exploration and generate narration."
```
**Outcome:**
1. Writes a cinematic documentary script with dramatic pacing.
2. Synthesizes high-fidelity English voice-over (`language_id="en"`).
3. Saves and returns the Markdown script and WAV audio file.

#### 3. Gujarati Script (Unsupported Language Handling)
```
User: "Create a Gujarati Instagram Reel script and generate narration."
```
**Outcome:**
1. Writes the complete reel script in authentic Gujarati script (ગુજરાતી).
2. Verifies whether the installed speech model supports Gujarati.
3. **Safely bypasses audio generation** if Gujarati acoustic weights are absent to prevent corrupted output.
4. Preserves and returns the Gujarati script while clearly explaining the model limitation:
   > *"Language 'Gujarati' (gu) is currently not supported by the active speech model. The model supports 23 primary languages including Hindi (hi) and English (en). Your complete script in Gujarati script has been preserved and saved, but audio generation was skipped to prevent corrupted output."*

---

## 🌐 Supported Languages (646 Total, Primary Shown)

| Code | Language | Code | Language | Code | Language |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `hi` | **Hindi** (Primary) | `en` | **English** (Primary) | `es` | Spanish |
| `fr` | French | `de` | German | `ar` | Arabic |
| `ja` | Japanese | `ko` | Korean | `zh` | Chinese |
| `it` | Italian | `pt` | Portuguese | `ru` | Russian |
| `nl` | Dutch | `pl` | Polish | `tr` | Turkish |
| `sv` | Swedish | `no` | Norwegian | `da` | Danish |
| `fi` | Finnish | `el` | Greek | `he` | Hebrew |
| `ms` | Malay | `sw` | Swahili | `id` | Indonesian |

---

## 🚀 Deployment: Local & Remote

### Option A: Local Deployment (Windows, Linux, macOS)

#### Automated Setup

**Windows (PowerShell):**
```powershell
.\install.ps1
.\start-server.ps1
```

**Linux / macOS (Bash):**
```bash
chmod +x install.sh start-server.sh
./install.sh
./start-server.sh
```

The Web Voice Studio Dashboard will be live at: `http://localhost:8000/dashboard/index.html`.

### Option B: Remote Server Deployment

Run VoiceStudio as a headless server on GPU clouds:

```bash
uvicorn plugins.voicestudio.backend.server:app --host 0.0.0.0 --port 8000
```

Configure your environment with `VOICESTUDIO_SERVER_URL` and `VOICESTUDIO_API_KEY`.

---

## 🛠️ MCP Tools for Claude Code & Claude Desktop

| Tool Name | Description |
| :--- | :--- |
| `voicestudio_content_pipeline` | Authors/cleans script, verifies language, generates 24kHz WAV, saves files. |
| `voicestudio_generate_speech` | Synthesizes speech from raw narration text. |
| `voicestudio_check_language` | Verifies language compatibility and detects writing script. |
| `voicestudio_list_profiles` | Enumerates available built-in, designed, and cloned voices. |
| `voicestudio_clone_voice` | Clones reference voice from audio with mandatory consent flag. |
| `voicestudio_design_voice` | Designs a synthetic voice from text prompts (gender, age, pitch, accent). |
| `voicestudio_get_status` | Health check and device compute inspection (CUDA/MPS/CPU). |

*(All `chatterbox_*` tool aliases remain supported for backwards compatibility.)*

---

## 🧪 Testing & Verification

Run the full cross-platform automated test suites:

```bash
# Run VoiceStudio test suite (49 tests)
python -m pytest plugins/voicestudio/tests -v

# Run Chatterbox test suite (48 tests)
python -m pytest plugins/chatterbox/tests -v
```

All 97 tests pass with zero external dependencies in headless/mock mode.

---

## 📜 Licenses & Upstream Acknowledgments

- **VoiceStudio:** Open-source ElevenLabs alternative created by Palash Debnath ([debpalash/voicestudio](https://github.com/debpalash/voicestudio)), AGPL-3.0.
- **Chatterbox:** Open-source multilingual speech engine created by Resemble AI ([resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox)), MIT License.
- **OpenVoice Studio Integration:** Claude Code plugin, MCP server, and Web Studio dashboard, AGPL-3.0 / MIT.
