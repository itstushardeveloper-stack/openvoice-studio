---
name: voice-studio
description: Generates video scripts (YouTube, Shorts, Reels, Documentaries, Podcasts, Storytelling) and synthesizes high-fidelity voice-overs, narration, TTS, voice design, and voice cloning in Hindi, English, and multilingual languages using VoiceStudio (open-source ElevenLabs alternative) and Chatterbox. Activates automatically via natural language requests or via /voice-studio.
---

# VoiceStudio & Chatterbox AI Voice Studio

Use this skill whenever the user asks in natural language or via command to:
- Write video scripts with voice-over (YouTube, Shorts, Instagram Reels, Documentaries, Explainers).
- Generate text-to-speech (TTS) or audio narration.
- Synthesize voices or generate speech files (24kHz master WAV).
- Design new voices using descriptive text (age, gender, accent, tone).
- Clone voices using reference recordings with user authorization.
- Produce podcast narration or storytelling audio.
- Create Hindi voice-over or English voice-over.

> [!IMPORTANT]
> **NO SLASH COMMANDS REQUIRED:** Users do not need to memorize or run slash commands. Normal natural language requests (e.g., *"Create a 5-minute Hindi YouTube video script on AI and generate voice-over"*) trigger the full script authoring and voice synthesis pipeline automatically.
>
> **INTERACTIVE COMMAND HANDLING:** If a user *does* type `/voice-studio` without details, do NOT simply state that instructions loaded. Actively guide them and prompt for:
> 1. **Topic / Idea** (e.g., "Future of Artificial Intelligence in 2026")
> 2. **Target Language** (Hindi in natural Devanagari, English, etc.)
> 3. **Format** (YouTube 16:9, Shorts/Reels 9:16, Documentary, Podcast)
> 4. **Voice Style / Tone** (Energetic, Calm Narrator, Professional, Dramatic)
>
> **UNRELATED REQUESTS:** Do NOT activate voice synthesis for unrelated coding, debugging, database, or general chat queries.

---

## Tool Execution Bridge: VoiceStudio & Chatterbox MCP Tools

The plugin provides native MCP (Model Context Protocol) tools for direct execution:

1. `voicestudio_content_pipeline(title, script_content, language, format, voice_profile)` (or alias `chatterbox_content_pipeline`):
   - Takes your authored script.
   - Validates language against the multilingual voice engine.
   - Cleans stage cues (`[Visual: ...]`, `(Music in)`, Hindi `दृश्य:`) from spoken dialogue.
   - Saves formatted script (`.md` and `.txt`).
   - Synthesizes 24kHz master WAV audio (or safely preserves script and explains limitation if language is unsupported like Gujarati).
   - Returns absolute file paths, audio duration, and language details.

2. `voicestudio_generate_speech(text, language_id, voice_profile, title)` (or alias `chatterbox_generate_speech`):
   - Synthesizes speech from raw narration text.

3. `voicestudio_check_language(language, content)`:
   - Checks model compatibility before synthesis.

4. `voicestudio_list_profiles()`:
   - Lists available voice profiles (`standard_hindi_narrator`, `standard_english_narrator`, `conversational_turbo`, `documentary_deep`).

5. `voicestudio_clone_voice(name, ref_audio_path, user_consent)`:
   - Clones a voice from reference audio. Requires explicit user authorization (`user_consent=True`).

6. `voicestudio_design_voice(name, description, language)`:
   - Designs a synthetic voice from text prompts (e.g., "Middle-aged male with calm, deep British accent for storytelling").

7. `voicestudio_check_health()`:
   - Returns voice engine backend status, active GPU device, and model readiness.

*(If running in an environment without MCP tool calling, fall back to executing via terminal: `python plugins/voicestudio/scripts/content_pipeline.py ...`)*

---

## Core Principle: Automatic Content Language Detection

Always identify the language of the **CONTENT** the user wants to create, not merely the language of their prompt.

### Real-World Examples:

1. **User (in English):** *"Claude, create a 5-minute Hindi YouTube video script about artificial intelligence and generate voice-over."*
   - **Target Content Language:** Hindi (`hi`).
   - **Writing Script:** Devanagari script (e.g., नमस्ते दोस्तों! आज के इस वीडियो में हम बात करेंगे कृत्रिम बुद्धिमत्ता यानी AI के भविष्य के बारे में...).
   - **Action:** Author full script in natural Devanagari Hindi, invoke `voicestudio_content_pipeline(..., language="hi")`, and return both the Markdown script and WAV audio file.

2. **User (in English):** *"Create an English documentary script about space and generate narration."*
   - **Target Content Language:** English (`en`).
   - **Action:** Author English script, invoke `voicestudio_content_pipeline(..., language="en")`, and return both files.

3. **User (in English or Hindi):** *"Create a Gujarati Instagram Reel script and generate narration."*
   - **Target Content Language:** Gujarati (`gu`).
   - **Model Verification:** When checking Gujarati against a model configuration that lacks Gujarati acoustic weights:
   - **Action:** Author the complete script in authentic Gujarati script (ગુજરાતી), invoke `voicestudio_content_pipeline(..., language="gu")`. The tool safely **bypasses audio generation** to prevent corrupted audio, preserves the Gujarati script file, and returns a clear explanation of the model limitation.

### Language Rules:
1. **Explicit Request Priority:** If the user specifies "Hindi", "English", "French", "German", etc., that language takes top priority.
2. **Never Auto-Translate Without Permission:** Keep the content strictly in the requested language.
3. **Implicit Detection:** If the user supplies existing text without specifying language, detect the script Unicode range (Devanagari $\rightarrow$ Hindi, Latin $\rightarrow$ English, etc.).
4. **Preserve Native Writing System:** Always write Hindi in Devanagari, Russian in Cyrillic, Japanese in Kana/Kanji, etc.

---

## Supported Multilingual Languages (646 Total, Primary Shown)

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

## Complete End-to-End Execution Workflow

Follow these steps on every voice-generation request:

### Step 1: Understand Content Requirements
- Determine topic, format, target duration, audience, and preferred voice tone (e.g. Hindi male narrator).

### Step 2: Author the Script
- Format with markdown headers and timestamps.
- Structure for spoken flow (130-150 words per minute).
- Include visual cues in square brackets (`[Visual: Drone shot of city skyline]`) — these will be automatically stripped before audio synthesis.

### Step 3: Call `voicestudio_content_pipeline`
- Pass the authored script text, title, requested language (`hi`, `en`, etc.), format, and voice profile.

### Step 4: Deliver Files
- Return:
  1. Script file link (`.md`).
  2. Spoken dialogue text (`.txt`).
  3. Master 24kHz audio file link (`.wav`), along with duration.
  4. Web dashboard link to preview/play audio: `http://localhost:8000`.
