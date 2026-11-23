---
name: voice-studio
description: Generates video scripts (YouTube, Shorts, Reels, Documentaries, Podcasts, Storytelling) and synthesizes high-fidelity voice-overs, narration, TTS, and voice cloning in Hindi, English, and 23+ languages using Chatterbox Multilingual V3. Activates automatically via natural language requests without any slash commands.
---

# Chatterbox AI Voice Studio

Use this skill whenever the user asks in natural language to:
- Write video scripts with voice-over (YouTube, Shorts, Instagram Reels, Documentaries, Explainers).
- Generate text-to-speech (TTS) or audio narration.
- Synthesize voices or generate speech files (WAV).
- Clone voices using reference recordings.
- Produce podcast narration or storytelling audio.
- Create Hindi voice-over or English voice-over.

> [!IMPORTANT]
> **NO SLASH COMMANDS REQUIRED:** Never ask the user to type `/chatterbox:speak`, `/chatterbox:setup`, or `/chatterbox:clone-voice`. You handle the entire script-to-audio workflow naturally within the conversation.
>
> **UNRELATED REQUESTS:** Do NOT activate or invoke voice generation for unrelated programming, debugging, database, or general chat requests.

---

## Core Principle: Automatic Content Language Detection

The most important user experience requirement is to determine the language of the **CONTENT** the user wants to create, not merely the conversational language in which the user chats with Claude.

### Real-World Examples:

1. **User (in English):** *"Claude, create a 5-minute Hindi YouTube video script about artificial intelligence and generate voice-over."*
   - **Target Content Language:** Hindi (`hi`).
   - **Writing Script:** Devanagari script (e.g., नमस्ते दोस्तों, आज हम AI के बारे में बात करेंगे...).
   - **Narration Language:** `hi`.
   - **Action:** Write full script in natural Devanagari Hindi, save script as Markdown/TXT, synthesize WAV audio using Chatterbox Multilingual V3 Hindi model, and return both files.

2. **User (in English):** *"Create an English documentary script about space and generate narration."*
   - **Target Content Language:** English (`en`).
   - **Action:** Write English script, save script file, synthesize English voice-over, return both files.

3. **User (in English or Hindi):** *"Create a Gujarati Instagram Reel script and generate narration."*
   - **Target Content Language:** Gujarati (`gu`).
   - **Model Verification:** Check Chatterbox Multilingual V3 support. Chatterbox V3 supports 23 languages (including Hindi and English), but does **NOT** support Gujarati.
   - **Action:** Write the complete script in authentic Gujarati script (ગુજરાતી), save the script file, safely **BYPASS** audio generation to prevent corrupted audio, and politely inform the user of the model limitation while delivering their saved Gujarati script.

### Language Rules:
1. **Explicit Request Priority:** If the user specifies "Hindi", "English", "French", "German", etc., that language takes top priority.
2. **Never Auto-Translate Without Permission:** Keep the content strictly in the requested language.
3. **Implicit Detection:** If the user pastes an existing script without specifying language, detect the script Unicode range (Devanagari $\rightarrow$ Hindi, Latin $\rightarrow$ English, etc.).
4. **Preserve Native Writing System:** Always write Hindi in Devanagari, Russian in Cyrillic, Japanese in Kana/Kanji, etc.

---

## Supported Chatterbox Multilingual V3 Languages (23 Total)

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

*If a requested language is NOT in this table (e.g. Gujarati `gu`, Bengali `bn`, Marathi `mr`, Tamil `ta`), write and preserve the script, but do NOT send unsupported language codes to the model.*

---

## Complete End-to-End Execution Workflow

Follow these steps on every voice-generation request:

### Step 1: Understand Content Requirements
Extract key elements from user request:
- **Format:** YouTube (16:9), YouTube Shorts / Instagram Reels (9:16), Documentary, Explainer, Podcast, Storytelling, News.
- **Duration / Word Count:**
  - YouTube (5 min): ~650–750 words
  - Shorts / Reels (30–60s): ~75–140 words
  - Documentary: paced at ~125 words/min
- **Tone & Style:** Cinematic, dramatic, energetic, conversational, educational.
- **Voice Preference:** Male, female, standard Hindi narrator, or custom voice profile.

### Step 2: Language Resolution Check
Verify language code.
- If supported (`hi`, `en`, etc.): proceed to script and audio generation.
- If unsupported (`gu`, etc.): proceed to script generation, but flag audio generation as skipped.

### Step 3: Write the Complete Script
Author the complete, engaging script in Claude with:
- Hook / Introduction
- Main Body / Key Points
- Climax / Insights
- Call-to-action / Outro

### Step 4: Save Script & Synthesize Audio
Save the script and execute the Chatterbox pipeline via CLI:

```powershell
# For Windows
python plugins/chatterbox/scripts/content_pipeline.py --title "AI_Revolution" --script "SCRIPT_TEXT" --lang "hi" --format "youtube"
```

Or for single audio generation:
```powershell
python plugins/chatterbox/scripts/voice_studio_cli.py generate --text "CLEAN_SPOKEN_TEXT" --lang "hi" --voice "standard_hindi_narrator" --title "AI_Revolution"
```

*(On Linux / macOS, use standard python3).*

### Step 5: Deliver Results to User
Present:
1. Complete script text with visual structure.
2. Clickable link to saved script file (`.md` or `.txt`).
3. Clickable link to generated WAV audio file (`.wav`) with duration and sample rate.
4. If an unsupported language was requested, state the limitation transparently while providing the completed script.

---

## Ethical Voice Cloning Policy
When the user asks to clone a voice using reference audio:
- Only reference audio that the user owns or has explicit consent/rights to use.
- Reference clips should be 5 to 15 seconds of clean, background-noise-free speech.
- Pass `--authorized` flag to confirm authorization.
