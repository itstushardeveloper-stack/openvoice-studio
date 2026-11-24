"""Language specifications, detection, and validation for VoiceStudio & Chatterbox Voice Engine."""

import re
from dataclasses import dataclass
from typing import Optional, Tuple, Dict

# Official languages supported by the multilingual engine (Hindi and English primary)
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "ar": "Arabic",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fi": "Finnish",
    "fr": "French",
    "he": "Hebrew",
    "hi": "Hindi",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
    "sv": "Swedish",
    "sw": "Swahili",
    "tr": "Turkish",
    "zh": "Chinese",
}

# Alias map for case-insensitive matching
LANGUAGE_ALIASES: Dict[str, str] = {
    # Hindi
    "hindi": "hi",
    "hin": "hi",
    "devanagari": "hi",
    "हिन्दी": "hi",
    "हिंदी": "hi",
    # English
    "english": "en",
    "eng": "en",
    # Spanish
    "spanish": "es",
    "espanol": "es",
    "español": "es",
    # French
    "french": "fr",
    "francais": "fr",
    # German
    "german": "de",
    "deutsch": "de",
    # Arabic
    "arabic": "ar",
    "عربي": "ar",
    # Russian
    "russian": "ru",
    # Chinese
    "chinese": "zh",
    "mandarin": "zh",
    "cmn": "zh",
    "中文": "zh",
    # Japanese
    "japanese": "ja",
    "nihongo": "ja",
    "日本語": "ja",
    # Korean
    "korean": "ko",
    "hangul": "ko",
    "한국어": "ko",
    # Italian
    "italian": "it",
    "italiano": "it",
    # Portuguese
    "portuguese": "pt",
    "português": "pt",
    # Dutch
    "dutch": "nl",
    "nederlands": "nl",
    # Polish
    "polish": "pl",
    "polski": "pl",
    # Turkish
    "turkish": "tr",
    "türkçe": "tr",
    # Swedish
    "swedish": "sv",
    "svenska": "sv",
    # Norwegian
    "norwegian": "no",
    "norsk": "no",
    # Danish
    "danish": "da",
    "dansk": "da",
    # Finnish
    "finnish": "fi",
    "suomi": "fi",
    # Greek
    "greek": "el",
    "ελληνικά": "el",
    # Hebrew
    "hebrew": "he",
    "עבריत": "he",
    # Swahili
    "swahili": "sw",
    "kiswahili": "sw",
    # Malay
    "malay": "ms",
    "bahasa melayu": "ms",
    # Languages that require acoustic verification / unsupported handling
    "gujarati": "gu",
    "guj": "gu",
    "ગુજરાતી": "gu",
    "bengali": "bn",
    "marathi": "mr",
    "tamil": "ta",
    "telugu": "te",
    "kannada": "kn",
    "malayalam": "ml",
    "punjabi": "pa",
    "urdu": "ur",
}

# Regex Unicode ranges for script detection
SCRIPT_PATTERNS = [
    (re.compile(r"[\u0900-\u097F]"), "hi", "Hindi (Devanagari script)"),
    (re.compile(r"[\u0A80-\u0AFF]"), "gu", "Gujarati (Gujarati script)"),
    (re.compile(r"[\u0600-\u06FF]"), "ar", "Arabic (Arabic script)"),
    (re.compile(r"[\u0400-\u04FF]"), "ru", "Russian (Cyrillic script)"),
    (re.compile(r"[\u3040-\u309F\u30A0-\u30FF]"), "ja", "Japanese (Kana)"),
    (re.compile(r"[\uAC00-\uD7AF]"), "ko", "Korean (Hangul)"),
    (re.compile(r"[\u4E00-\u9FFF]"), "zh", "Chinese (CJK Ideographs)"),
    (re.compile(r"[\u0370-\u03FF]"), "el", "Greek (Greek script)"),
    (re.compile(r"[\u0590-\u05FF]"), "he", "Hebrew (Hebrew script)"),
]


@dataclass
class LanguageValidationResult:
    """Result of language detection or validation."""
    code: str
    name: str
    is_supported: bool
    detected_script: Optional[str] = None
    message: str = ""
    can_generate_audio: bool = False


def normalize_language_code(lang_str: Optional[str]) -> Optional[str]:
    """Normalize input language name, code, or alias to standard ISO code."""
    if not lang_str:
        return None
    cleaned = lang_str.strip().lower()
    if cleaned in SUPPORTED_LANGUAGES:
        return cleaned
    if cleaned in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[cleaned]
    # Check prefixes
    for alias, code in LANGUAGE_ALIASES.items():
        if alias in cleaned:
            return code
    return cleaned


def detect_script_from_text(text: str) -> Optional[Tuple[str, str]]:
    """Detect dominant writing script from text content using Unicode ranges."""
    if not text:
        return None
    counts = {}
    for pattern, code, script_name in SCRIPT_PATTERNS:
        matches = len(pattern.findall(text))
        if matches > 0:
            counts[code] = (matches, script_name)

    if counts:
        # Get script with maximum character matches
        dominant_code = max(counts.keys(), key=lambda k: counts[k][0])
        return dominant_code, counts[dominant_code][1]

    # If predominantly Latin letters
    latin_count = len(re.findall(r"[A-Za-z]", text))
    if latin_count > 10:
        return "en", "Latin script"

    return None


def validate_and_resolve_language(
    explicit_language: Optional[str] = None,
    content_text: Optional[str] = None
) -> LanguageValidationResult:
    """
    Validate requested language or infer from content text.
    
    Priority Rules:
    1. Explicit requested language has top priority.
    2. If no explicit language is provided, infer from content text Unicode script.
    3. If neither is specified or detectable, default to 'en' (English).
    4. Check if resolved language is supported by the active model engine.
    5. If unsupported (e.g., Gujarati 'gu'), generate clear explanatory message
       and prevent sending unsupported language IDs to TTS engine.
    """
    resolved_code = None
    detected_script = None

    # Step 1: Explicit language requested
    if explicit_language:
        normalized = normalize_language_code(explicit_language)
        if normalized:
            resolved_code = normalized

    # Step 2: Inferred from content text if not explicit
    if not resolved_code and content_text:
        script_info = detect_script_from_text(content_text)
        if script_info:
            resolved_code, detected_script = script_info

    # Step 3: Default to English if ambiguous
    if not resolved_code:
        resolved_code = "en"

    # Step 4: Check if supported
    is_supported = resolved_code in SUPPORTED_LANGUAGES

    if is_supported:
        lang_name = SUPPORTED_LANGUAGES[resolved_code]
        message = (
            f"Language '{lang_name}' ({resolved_code}) is fully supported by "
            f"the voice synthesis engine. Audio narration will be synthesized."
        )
        return LanguageValidationResult(
            code=resolved_code,
            name=lang_name,
            is_supported=True,
            detected_script=detected_script,
            message=message,
            can_generate_audio=True
        )
    else:
        # Unsupported language handling (e.g. Gujarati)
        unsupported_names = {
            "gu": "Gujarati",
            "bn": "Bengali",
            "mr": "Marathi",
            "ta": "Tamil",
            "te": "Telugu",
            "kn": "Kannada",
            "ml": "Malayalam",
            "pa": "Punjabi",
            "ur": "Urdu",
        }
        lang_name = unsupported_names.get(resolved_code, resolved_code.upper())
        message = (
            f"Language '{lang_name}' ({resolved_code}) is currently NOT supported by "
            f"the voice synthesis engine (VoiceStudio / Chatterbox Multilingual V3). "
            f"The voice engine supports 23 primary languages: "
            f"{', '.join(sorted(SUPPORTED_LANGUAGES.values()))}. "
            f"The complete script has been written in {lang_name} and saved as requested, "
            f"but audio generation was safely bypassed to prevent corrupted output."
        )
        return LanguageValidationResult(
            code=resolved_code,
            name=lang_name,
            is_supported=False,
            detected_script=detected_script,
            message=message,
            can_generate_audio=False
        )
