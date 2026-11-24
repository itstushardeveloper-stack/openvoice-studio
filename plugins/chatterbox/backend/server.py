"""FastAPI REST API server for VoiceStudio & Chatterbox Voice Studio."""

import io
import os
from pathlib import Path
from typing import List, Optional

from fastapi import (
    FastAPI,
    HTTPException,
    Security,
    UploadFile,
    File,
    Form,
    status,
    Depends,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse, Response
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .audio_utils import sanitize_filename, validate_audio_file
from .config import config
from .engine import engine, GenerationResult
from .languages import (
    SUPPORTED_LANGUAGES,
    validate_and_resolve_language,
)
from .profiles import profile_manager, VoiceProfile

app = FastAPI(
    title="Chatterbox & VoiceStudio AI Voice API",
    description="High-fidelity AI voice generation, multilingual TTS (Hindi, English, etc.), and voice cloning API.",
    version="1.2.0",
)

# Enable CORS for dashboard and external frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: Optional[str] = Security(api_key_header)):
    """Verify API key if configured; otherwise allow local access."""
    if config.api_key:
        if not key or key != config.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-Key authentication header.",
            )
    return key


# --- Pydantic Request Models ---
class TTSGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Script or narration text to synthesize")
    language_id: Optional[str] = Field(None, description="Language code e.g. 'hi' for Hindi, 'en' for English")
    voice_profile: Optional[str] = Field(None, description="Name of saved voice profile")
    audio_prompt_path: Optional[str] = Field(None, description="Direct path to reference audio")
    exaggeration: float = Field(0.5, ge=0.0, le=1.0, description="Emotion and expressiveness weight")
    cfg_weight: float = Field(0.5, ge=0.0, le=1.0, description="Guidance scale")
    title: Optional[str] = Field("narration", description="Title for output file")


class OpenAISpeechRequest(BaseModel):
    model: str = "tts-1"
    voice: Optional[str] = "alloy"
    input: str = Field(..., min_length=1)
    response_format: Optional[str] = "wav"
    speed: Optional[float] = 1.0


class LanguageCheckRequest(BaseModel):
    language: Optional[str] = Field(None, description="Target language name or code")
    content: Optional[str] = Field(None, description="Optional text content to analyze script")


# --- Public Endpoints ---
@app.get("/health")
def health():
    """Health check endpoint providing engine status, device, and capabilities."""
    return {
        "status": "healthy",
        "engine": "VoiceStudio & Chatterbox V3",
        "device": engine.device,
        "t3_model": config.t3_model,
        "mode": config.mode,
        "mock_inference": config.mock_inference,
        "is_model_loaded": engine._is_model_loaded,
        "supported_languages_count": len(SUPPORTED_LANGUAGES),
        "storage_dir": str(config.storage_dir),
    }


@app.get("/v1/languages")
def get_languages():
    """List all official Chatterbox & VoiceStudio supported languages."""
    return {
        "supported_languages": SUPPORTED_LANGUAGES,
        "count": len(SUPPORTED_LANGUAGES),
        "primary": ["hi", "en"],
    }


@app.post("/v1/languages/check")
def check_language(req: LanguageCheckRequest):
    """Check language support and detect script."""
    res = validate_and_resolve_language(
        explicit_language=req.language,
        content_text=req.content,
    )
    return {
        "code": res.code,
        "name": res.name,
        "is_supported": res.is_supported,
        "detected_script": res.detected_script,
        "message": res.message,
        "can_generate_audio": res.can_generate_audio,
    }


# --- Authenticated Endpoints ---
@app.post("/v1/audio/speech", dependencies=[Depends(verify_api_key)])
def openai_speech(req: OpenAISpeechRequest):
    """OpenAI & VoiceStudio-compatible audio speech endpoint."""
    try:
        result: GenerationResult = engine.synthesize(
            text=req.input,
            voice_profile=req.voice,
            title="openai_speech",
        )
        if result.audio_path and Path(result.audio_path).exists():
            with open(result.audio_path, "rb") as f:
                content = f.read()
            return Response(content=content, media_type="audio/wav")
        raise HTTPException(status_code=500, detail="Audio generation failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/tts/generate", dependencies=[Depends(verify_api_key)])
def generate_speech(req: TTSGenerateRequest):
    """Generate audio voice-over from text with automatic language handling."""
    try:
        result: GenerationResult = engine.synthesize(
            text=req.text,
            language_id=req.language_id,
            voice_profile=req.voice_profile,
            audio_prompt_path=req.audio_prompt_path,
            exaggeration=req.exaggeration,
            cfg_weight=req.cfg_weight,
            title=req.title,
        )

        audio_filename = Path(result.audio_path).name if result.audio_path else None
        audio_url = f"/v1/audio/{audio_filename}" if audio_filename else None

        return {
            "status": result.status,
            "id": result.id,
            "audio_url": audio_url,
            "audio_path": result.audio_path,
            "script_path": result.script_path,
            "language_id": result.language_id,
            "language_name": result.language_name,
            "duration_seconds": result.duration_seconds,
            "sample_rate": result.sample_rate,
            "chunks_count": result.chunks_count,
            "char_count": result.char_count,
            "voice_profile": result.voice_profile,
            "message": result.message,
            "created_at": result.created_at,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/audio/{filename}")
def get_audio_file(filename: str):
    """Retrieve and stream synthesized audio WAV file."""
    safe_name = sanitize_filename(filename)
    base_dir = config.storage_dir.resolve()
    audio_path = (base_dir / safe_name).resolve()

    try:
        audio_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied.")

    if not audio_path.exists() or audio_path == base_dir:
        raise HTTPException(status_code=404, detail="Audio file not found.")

    return FileResponse(
        path=audio_path,
        media_type="audio/wav",
        filename=safe_name,
    )


@app.get("/v1/voices/profiles")
@app.get("/profiles")
def list_voice_profiles():
    """List available voice profiles."""
    profiles = profile_manager.list_profiles()
    return {"profiles": [p.to_dict() for p in profiles]}


@app.post("/v1/voices/clone", dependencies=[Depends(verify_api_key)])
@app.post("/profiles", dependencies=[Depends(verify_api_key)])
async def clone_voice_profile(
    name: str = Form(...),
    gender: str = Form("neutral"),
    language_tag: str = Form("multilingual"),
    description: str = Form(""),
    authorized: bool = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload reference audio to create a cloned voice profile.
    
    Requires explicit authorization confirmation.
    """
    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization required: You must confirm ownership or authorized permission to clone this voice.",
        )

    safe_name = sanitize_filename(name.strip().lower().replace(" ", "_"))
    temp_dir = config.profiles_dir / ".tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"upload_{safe_name}_{file.filename}"

    try:
        content = await file.read()
        if len(content) > config.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file exceeds {config.max_upload_bytes // (1024 * 1024)}MB limit.",
            )

        with open(temp_path, "wb") as f:
            f.write(content)

        profile = profile_manager.create_profile(
            name=name,
            audio_file_path=temp_path,
            authorized=authorized,
            gender=gender,
            language_tag=language_tag,
            description=description,
        )
        return {"status": "success", "profile": profile.to_dict()}
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


@app.delete("/v1/voices/profiles/{name}", dependencies=[Depends(verify_api_key)])
def delete_voice_profile(name: str):
    """Delete a custom voice profile."""
    try:
        success = profile_manager.delete_profile(name)
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found.")
        return {"status": "success", "deleted": name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/history")
def get_generation_history(limit: int = 50):
    """Retrieve history of synthesized audio recordings."""
    history = engine.get_history(limit=limit)
    return {"history": history, "count": len(history)}


# --- Dashboard Static Files & Root Redirect ---
DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"
if DASHBOARD_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")


@app.get("/")
def root_redirect():
    """Redirect root path to interactive Voice Studio dashboard."""
    return RedirectResponse(url="/dashboard/index.html")
