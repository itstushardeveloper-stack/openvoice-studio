"""Tests for Voice Studio CLI and Content Pipeline scripts."""

import json
from pathlib import Path
import pytest
from scripts.content_pipeline import execute_content_pipeline
from backend.audio_utils import create_mock_wav_bytes


def test_content_pipeline_hindi_youtube_script(setup_test_environment):
    """Test full pipeline execution: Hindi YouTube script with voice-over."""
    script_text = """
    # आर्टिफिशियल इंटेलिजेंस का भविष्य
    [Visual: चमकते हुए भविष्य के शहर का दृश्य]
    (पृष्ठभूमि में प्रेरणादायक संगीत शुरू होता है)
    होस्ट: नमस्ते दोस्तों! टेक्नोलॉजी की इस नई सुबह में आपका स्वागत है।
    आज हम समझेंगे कि AI हमारे समाज और काम करने के तौर-तरीकों को कैसे बदल रहा है।
    [Visual: रोबोट और डॉक्टर साथ काम करते हुए]
    चिकित्सा से लेकर शिक्षा तक हर क्षेत्र में नए आयाम स्थापित हो रहे हैं।
    वीडियो पसंद आया हो तो लाइक और सब्सक्राइब ज़रूर करें!
    """

    result = execute_content_pipeline(
        script_content=script_text,
        title="Hindi_AI_Future",
        requested_language="hi",
        content_format="youtube",
        output_dir=str(setup_test_environment["storage_dir"]),
    )

    assert result["status"] == "success"
    assert result["language_code"] == "hi"
    assert result["language_supported"] is True
    assert result["audio_path"] is not None
    assert Path(result["audio_path"]).exists()
    assert Path(result["script_md_path"]).exists()
    assert Path(result["spoken_txt_path"]).exists()

    # Verify spoken text has stripped visual cues
    with open(result["spoken_txt_path"], "r", encoding="utf-8") as f:
        spoken = f.read()
    assert "Visual:" not in spoken
    assert "नमस्ते दोस्तों" in spoken


def test_content_pipeline_english_documentary(setup_test_environment):
    """Test full pipeline execution: English documentary script with narration."""
    script_text = """
    # Secrets of the Deep Oceans
    **Visual:** Bioluminescent jellyfish glowing in the abyssal zone.
    (Ambient water sounds fade)
    Narrator: Beneath five thousand meters of ocean lies a world untouched by sunlight.
    [Visual: Hydrothermal vents spewing mineral-rich clouds]
    Here, extraordinary organisms thrive in extreme heat and pressure.
    """

    result = execute_content_pipeline(
        script_content=script_text,
        title="Deep_Oceans",
        requested_language="en",
        content_format="documentary",
        output_dir=str(setup_test_environment["storage_dir"]),
    )

    assert result["status"] == "success"
    assert result["language_code"] == "en"
    assert result["audio_path"] is not None
    assert Path(result["audio_path"]).exists()
    assert Path(result["script_md_path"]).exists()


def test_content_pipeline_gujarati_unsupported_handling(setup_test_environment):
    """
    Test pipeline handling of Gujarati:
    - Writes and preserves the Gujarati script
    - Saves the Markdown and text files
    - Skips audio generation and explains limitation
    """
    gujarati_script = """
    # સફળતા માટે ૩ નિયમો
    [Visual: સૂર્યોદયનો સુંદર નજારો]
    (શાંત સંગીત વાગે છે)
    નમસ્તે મિત્રો! જો તમે જીવનમાં આગળ વધવા માંગો છો, તો આ ત્રણ આદતો અપનાવો.
    પહેલી આદત: દરરોજ સવારે સમયસર જાગો અને તમારા લક્ષ્ય પર ધ્યાન કેન્દ્રિત કરો.
    """

    result = execute_content_pipeline(
        script_content=gujarati_script,
        title="Gujarati_Reel_Habits",
        requested_language="gu",
        content_format="reels",
        output_dir=str(setup_test_environment["storage_dir"]),
    )

    assert result["status"] == "script_saved_audio_unsupported"
    assert result["language_code"] == "gu"
    assert result["language_supported"] is False
    assert result["audio_path"] is None, "Audio must not be created for unsupported Gujarati"
    assert Path(result["script_md_path"]).exists()

    # Check script is preserved in Gujarati script
    with open(result["script_md_path"], "r", encoding="utf-8") as f:
        md_content = f.read()
    assert "નમસ્તે મિત્રો" in md_content
    assert "NOT supported" in result["message"]
