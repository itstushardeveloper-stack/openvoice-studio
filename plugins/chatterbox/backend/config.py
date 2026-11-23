"""Configuration settings for Chatterbox AI Voice Studio."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChatterboxConfig:
    """Application settings supporting local and remote inference."""

    mode: str = field(
        default_factory=lambda: os.getenv("CHATTERBOX_MODE", "local").lower()
    )
    server_url: str = field(
        default_factory=lambda: os.getenv("CHATTERBOX_SERVER_URL", "http://localhost:8000")
    )
    api_key: Optional[str] = field(
        default_factory=lambda: os.getenv("CHATTERBOX_API_KEY", None)
    )
    host: str = field(
        default_factory=lambda: os.getenv("CHATTERBOX_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.getenv("CHATTERBOX_PORT", "8000"))
    )
    device: str = field(
        default_factory=lambda: os.getenv("CHATTERBOX_DEVICE", "auto")
    )
    t3_model: str = field(
        default_factory=lambda: os.getenv("CHATTERBOX_T3_MODEL", "v3")
    )
    storage_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("CHATTERBOX_STORAGE_DIR", "generated_audio")
        ).resolve()
    )
    profiles_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("CHATTERBOX_PROFILES_DIR", "voice_profiles")
        ).resolve()
    )
    max_upload_bytes: int = field(
        default_factory=lambda: int(os.getenv("CHATTERBOX_MAX_UPLOAD_MB", "25")) * 1024 * 1024
    )
    mock_inference: bool = field(
        default_factory=lambda: os.getenv("CHATTERBOX_MOCK_INFERENCE", "false").lower() in ("1", "true", "yes")
    )
    sample_rate: int = 24000

    def __post_init__(self):
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def resolve_device(self) -> str:
        """Resolve 'auto' device to cuda, mps, or cpu."""
        if self.device != "auto":
            return self.device
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"


# Global singleton instance
config = ChatterboxConfig()
