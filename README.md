# Chatterbox AI Voice Studio — Claude Code Marketplace

[![CI](https://github.com/itstushardeveloper-stack/openvoice-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/itstushardeveloper-stack/openvoice-studio/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Chatterbox: Multilingual V3](https://img.shields.io/badge/Chatterbox-Multilingual%20V3-blue.svg)](https://github.com/resemble-ai/chatterbox)
[![Claude Code: Plugin Ready](https://img.shields.io/badge/Claude%20Code-Marketplace%20Plugin-green.svg)](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code)

A complete, production-grade **Claude Code Marketplace and Voice Studio** powered by the original [Chatterbox](https://github.com/resemble-ai/chatterbox) Multilingual V3 text-to-speech and zero-shot voice cloning engine by Resemble AI.

---

## 🌟 Key Architecture & Responsibilities

This integration combines the creative reasoning of Claude with the acoustic fidelity of Chatterbox Multilingual V3:

$$\text{User Request} \longrightarrow \underbrace{\text{Claude (Script Authoring)}}_{\text{Prompt, Format, Language, Pacing}} \longrightarrow \underbrace{\text{Chatterbox Multilingual V3}}_{\text{Acoustic Modeling, Multilingual TTS, Voice Cloning}} \longrightarrow \text{WAV Audio}$$

- **Claude Writes the Script:** Generates tailored, format-specific scripts (YouTube videos, Shorts, Instagram Reels, Documentaries, Podcasts, Explainer videos, Storytelling, News).
- **Chatterbox Synthesizes the Audio:** Converts spoken dialogue into broadcast-quality 24 kHz WAV audio with voice cloning and Perth watermarking.
- **Natural Language Interaction:** **No slash commands required!** You do not need `/chatterbox:speak` or `/chatterbox:clone`. Normal conversational requests trigger the pipeline automatically.

---

## ⚡ Quick Start: Marketplace Installation

Install directly into your Claude Code environment using the official marketplace commands:

```bash
# 1. Add this repository as a Claude Code marketplace
/plugin marketplace add YOUR_USERNAME/chatterbox-claude-marketplace

# 2. Install the Chatterbox voice studio plugin
/plugin install chatterbox@chatterbox-voice-marketplace
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
2. Cleans stage directions (`[Visual: ...]`, `(Music in)`) from spoken narration.
3. Synthesizes Hindi audio using Chatterbox Multilingual V3 (`language_id="hi"`).
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
2. Verifies whether the installed Chatterbox V3 speech model supports Gujarati.
3. **Safely bypasses audio generation** because Gujarati is not among Chatterbox V3's 23 supported languages.
4. Preserves and returns the Gujarati script while clearly explaining the model limitation:
   > *"Language 'Gujarati' (gu) is currently not supported by Chatterbox Multilingual V3. Chatterbox V3 supports 23 languages including Hindi (hi) and English (en). Your complete script in Gujarati script has been preserved and saved, but audio generation was skipped to prevent corrupted output."*

---

## 🌐 Supported Languages (23 Total)

Chatterbox Multilingual V3 supports 23 languages natively:

| Code | Language | Code | Language | Code | Language |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `hi` | **Hindi** (Primary) | `en` | **English** (Primary) | `es` | Spanish |
| `fr` | French | `de` | German | `ar` | Arabic |
| `ja` | Japanese | `ko` | Korean | `zh` | Chinese |
| `it` | Italian | `pt` | Portuguese | `ru` | Russian |
| `nl` | Dutch | `pl` | Polish | `tr` | Turkish |
| `sv` | Swedish | `no` | Norwegian | `da` | Danish |
| `fi` | Finnish | `el` | Greek | `he` | Hebrew |
| `ms` | Malay | `sw` | Swahili | | |

---

## 🚀 Deployment: Local & Remote

### Option A: Local Deployment (Windows, Linux, macOS)

#### Automated Setup

**Windows (PowerShell):**
```powershell
.\install.ps1
# To download and configure full local GPU weights:
.\install.ps1 -FullModel
```

**Linux / macOS (Bash):**
```bash
chmod +x install.sh start-server.sh
./install.sh
# To install full GPU weights:
./install.sh --full-model
```

#### Run the Voice Studio Server
```powershell
# Windows
.\start-server.ps1 -Port 8000

# Linux / macOS
./start-server.sh 0.0.0.0 8000
```
- Interactive Web Voice Studio: `http://localhost:8000/dashboard/index.html`
- REST API Health Check: `http://localhost:8000/health`

### Option B: Remote Cloud GPU / VPS Deployment

Run the Chatterbox backend on a GPU-enabled cloud server (AWS, GCP, RunPod, Lambda Labs, or your own VPS):

1. Configure `.env` on your server:
   ```env
   CHATTERBOX_MODE=local
   CHATTERBOX_PORT=8000
   CHATTERBOX_API_KEY=your-secure-secret-token
   CHATTERBOX_DEVICE=cuda
   ```
2. Start the server behind HTTPS (e.g., Caddy or Nginx reverse proxy).
3. In Claude Code or on your local machine, configure `.env`:
   ```env
   CHATTERBOX_MODE=remote
   CHATTERBOX_SERVER_URL=https://your-gpu-server.example.com
   CHATTERBOX_API_KEY=your-secure-secret-token
   ```
Now all voice generation commands executed by Claude Code seamlessly delegate inference to your remote GPU server!

---

## 🎛️ CLI Usage

The plugin includes a unified CLI for direct terminal usage or headless automation:

```bash
# Check language support
python plugins/chatterbox/scripts/voice_studio_cli.py check-lang --lang hi
python plugins/chatterbox/scripts/voice_studio_cli.py check-lang --lang gu

# Generate speech from text
python plugins/chatterbox/scripts/voice_studio_cli.py generate \
  --text "नमस्ते दोस्तों, आर्टिफिशियल इंटेलिजेंस में आपका स्वागत है।" \
  --lang hi \
  --out hindi_sample.wav

# Run end-to-end content pipeline
python plugins/chatterbox/scripts/content_pipeline.py \
  --title "Cosmic_Wonders" \
  --script "Deep within the universe, stars are born inside stellar nurseries..." \
  --lang en \
  --format documentary
```

---

## 🎙️ Ethical Voice Cloning

Chatterbox allows zero-shot voice cloning from a 5–15 second reference audio clip.

```bash
python plugins/chatterbox/scripts/voice_studio_cli.py clone-voice \
  --name "custom_narrator" \
  --audio "path/to/reference_voice.wav" \
  --gender "female" \
  --lang "hi" \
  --authorized
```

> [!CAUTION]
> **Biometric Voice Safeguards:** The `--authorized` flag is strictly required. You must only clone voices from recordings that you own or have explicit legal consent to use. Unauthorized cloning of individuals or public figures without permission is strictly prohibited.

---

## 🧪 Automated Test Suite

A complete test suite is included, verifying all manifests, language detection algorithms, text chunking, profiles, API endpoints, and CLI scripts:

```bash
# Run all automated tests (with mock inference enabled)
python -m pytest plugins/chatterbox/tests -v
```

All expensive model weights are automatically mocked during unit tests so the test suite runs in seconds without GPU requirements.

---

## 📂 Repository Structure

```
openvoice-studio/
├── .claude-plugin/
│   └── marketplace.json            # Claude Code Marketplace Catalog Manifest
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions Multi-OS CI Workflow
├── .env.example                    # Environment variable configuration template
├── .gitignore                      # Git exclusion rules (safeguarding audio/keys/weights)
├── README.md                       # Main Documentation
├── requirements.txt                # Core Server, CLI, and API dependencies
├── install.ps1                     # Windows PowerShell Installer
├── install.sh                      # Linux / macOS Bash Installer
├── start-server.ps1                # Windows Server Runner
├── start-server.sh                 # Linux / macOS Server Runner
├── plugins/
│   └── chatterbox/
│       ├── .claude-plugin/
│       │   └── plugin.json         # Plugin Manifest for Claude Code
│       ├── skills/
│       │   └── voice-studio/
│       │       └── SKILL.md        # Natural-Language Voice Studio Skill
│       ├── backend/
│       │   ├── __init__.py
│       │   ├── config.py           # Application Settings (Local & Remote)
│       │   ├── languages.py        # 23 Languages, Script Detection, Unicode checks
│       │   ├── audio_utils.py      # Script cleaning, Chunking, WAV concatenation
│       │   ├── profiles.py         # Voice Cloning Profile Manager & Safeguards
│       │   ├── engine.py           # Chatterbox Multilingual V3 Engine Wrapper
│       │   └── server.py           # FastAPI REST API & Dashboard Host
│       ├── scripts/
│       │   ├── __init__.py
│       │   ├── voice_studio_cli.py # Standalone CLI for synthesis & cloning
│       │   └── content_pipeline.py # End-to-end Script + Audio Orchestrator
│       ├── dashboard/
│       │   ├── index.html          # Modern Voice Studio Web Dashboard
│       │   ├── app.js              # Live Audio Visualizer & Waveform Controller
│       │   └── style.css           # Custom styles & Dark Theme UI
│       ├── tests/                  # 100% Automated Pytest Suite
│       │   ├── conftest.py
│       │   ├── test_manifests.py
│       │   ├── test_languages.py
│       │   ├── test_audio_utils.py
│       │   ├── test_profiles.py
│       │   ├── test_engine.py
│       │   ├── test_server_api.py
│       │   └── test_cli_and_pipeline.py
│       └── README.md
└── upstream/
    └── chatterbox/                 # Official Upstream Chatterbox Repository Clone
```

---

## 📜 Licensing

- The integration, API server, CLI scripts, Claude Code plugin, and web dashboard are released under the **MIT License**.
- Upstream Chatterbox models and source code are developed and released by Resemble AI under the **MIT License** (Copyright 2025 Resemble AI).
- Built-in Perth watermarking is provided under its respective open-source license.
