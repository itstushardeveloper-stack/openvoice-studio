"""Voice Profile management for Chatterbox Voice Studio."""

import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .audio_utils import sanitize_filename, validate_audio_file
from .config import config


@dataclass
class VoiceProfile:
    """Metadata representing a voice cloning profile."""
    name: str
    description: str
    gender: str  # "male", "female", "neutral"
    language_tag: str  # "en", "hi", "multilingual"
    audio_path: Optional[str]
    authorized: bool
    created_at: str
    speaker_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "VoiceProfile":
        return cls(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            gender=data.get("gender", "neutral"),
            language_tag=data.get("language_tag", "multilingual"),
            audio_path=data.get("audio_path"),
            authorized=bool(data.get("authorized", False)),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            speaker_id=data.get("speaker_id"),
        )


class VoiceProfileManager:
    """Manages storage, retrieval, and authorization of voice profiles."""

    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = profiles_dir or config.profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_builtin_profiles()

    def _ensure_builtin_profiles(self):
        """Seed default built-in profile descriptors."""
        default_profiles = [
            VoiceProfile(
                name="standard_hindi_narrator",
                description="Natural, warm Hindi narration voice optimized for Devanagari storytelling and YouTube scripts.",
                gender="female",
                language_tag="hi",
                audio_path=None,
                authorized=True,
                created_at="2026-01-01T00:00:00Z",
                speaker_id="hi_standard",
            ),
            VoiceProfile(
                name="standard_english_narrator",
                description="Clear, expressive English voice for documentaries, explainers, and podcasts.",
                gender="neutral",
                language_tag="en",
                audio_path=None,
                authorized=True,
                created_at="2026-01-01T00:00:00Z",
                speaker_id="en_standard",
            ),
            VoiceProfile(
                name="conversational_turbo",
                description="Dynamic, upbeat conversational voice supporting paralinguistic expressions.",
                gender="neutral",
                language_tag="en",
                audio_path=None,
                authorized=True,
                created_at="2026-01-01T00:00:00Z",
                speaker_id="turbo_standard",
            ),
        ]
        for p in default_profiles:
            meta_path = self.profiles_dir / f"{p.name}.json"
            if not meta_path.exists():
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(p.to_dict(), f, indent=2)

    def create_profile(
        self,
        name: str,
        audio_file_path: Optional[Path],
        authorized: bool,
        gender: str = "neutral",
        language_tag: str = "multilingual",
        description: str = "",
    ) -> VoiceProfile:
        """
        Create and persist a new voice profile.
        
        Requires explicit authorization confirming ownership or license to clone voice.
        """
        if not authorized:
            raise PermissionError(
                "Voice cloning requires explicit user authorization confirming ownership "
                "or legal permission to use the reference voice recording."
            )

        safe_name = sanitize_filename(name.strip().lower().replace(" ", "_"))
        if not safe_name:
            raise ValueError("Profile name is invalid.")

        dest_audio_path = None
        if audio_file_path:
            audio_path = Path(audio_file_path)
            valid, msg = validate_audio_file(audio_path, config.max_upload_bytes)
            if not valid:
                raise ValueError(f"Invalid reference audio: {msg}")

            dest_filename = f"{safe_name}{audio_path.suffix.lower()}"
            dest_audio_path = self.profiles_dir / dest_filename
            shutil.copyfile(audio_path, dest_audio_path)

        profile = VoiceProfile(
            name=safe_name,
            description=description or f"Custom profile for {safe_name}",
            gender=gender.lower(),
            language_tag=language_tag.lower(),
            audio_path=str(dest_audio_path) if dest_audio_path else None,
            authorized=True,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        meta_path = self.profiles_dir / f"{safe_name}.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2)

        return profile

    def get_profile(self, name: str) -> Optional[VoiceProfile]:
        """Fetch profile by name."""
        safe_name = sanitize_filename(name.strip().lower().replace(" ", "_"))
        meta_path = self.profiles_dir / f"{safe_name}.json"
        if not meta_path.exists():
            return None
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return VoiceProfile.from_dict(data)
        except Exception:
            return None

    def list_profiles(self) -> List[VoiceProfile]:
        """List all available voice profiles."""
        profiles = []
        for file in self.profiles_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                profiles.append(VoiceProfile.from_dict(data))
            except Exception:
                continue
        profiles.sort(key=lambda p: p.name)
        return profiles

    def delete_profile(self, name: str) -> bool:
        """Delete custom voice profile (cannot delete builtins)."""
        if name in ("standard_hindi_narrator", "standard_english_narrator", "conversational_turbo"):
            raise ValueError("Cannot delete system built-in profiles.")
        safe_name = sanitize_filename(name.strip().lower().replace(" ", "_"))
        meta_path = self.profiles_dir / f"{safe_name}.json"
        if not meta_path.exists():
            return False

        profile = self.get_profile(safe_name)
        if profile and profile.audio_path:
            audio_p = Path(profile.audio_path)
            if audio_p.exists():
                audio_p.unlink(missing_ok=True)

        meta_path.unlink(missing_ok=True)
        return True


# Global manager instance
profile_manager = VoiceProfileManager()
