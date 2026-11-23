<#
.SYNOPSIS
    Chatterbox AI Voice Studio - Windows Installation Script
.DESCRIPTION
    Installs Python dependencies, sets up local storage directories,
    and configures the Chatterbox Multilingual V3 engine.
#>

[CmdletBinding()]
param(
    [switch]$FullModel = $false,
    [switch]$SkipVenv = $false
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Chatterbox AI Voice Studio - Installation (Windows)    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Verify Python Installation
try {
    $pyVersion = python --version 2>&1
    Write-Host "[✓] Found Python: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[X] Python is not installed or not in PATH. Please install Python 3.10+." -ForegroundColor Red
    exit 1
}

# 2. Virtual Environment Setup
if (-not $SkipVenv) {
    if (-not (Test-Path "venv")) {
        Write-Host "[*] Creating virtual environment 'venv'..." -ForegroundColor Yellow
        python -m venv venv
    }
    Write-Host "[*] Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# 3. Upgrade Pip
Write-Host "[*] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 4. Install Core Server & API Dependencies
Write-Host "[*] Installing core dependencies from requirements.txt..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

# 5. Optional Full Model Dependencies
if ($FullModel) {
    Write-Host "[*] Installing full model dependencies from upstream/chatterbox..." -ForegroundColor Yellow
    if (Test-Path "upstream/chatterbox") {
        python -m pip install -e upstream/chatterbox
    } else {
        Write-Host "[!] upstream/chatterbox not found. Installing from PyPI chatterbox-tts..." -ForegroundColor Yellow
        python -m pip install chatterbox-tts
    }
} else {
    Write-Host "[i] Core API and CLI installed. To install full local GPU weights, re-run with -FullModel." -ForegroundColor Cyan
}

# 6. Initialize Directories
Write-Host "[*] Creating storage and profile directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "generated_audio" | Out-Null
New-Item -ItemType Directory -Force -Path "voice_profiles" | Out-Null
New-Item -ItemType Directory -Force -Path "models" | Out-Null

# 7. Create .env if missing
if (-not (Test-Path ".env")) {
    Write-Host "[*] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "[✓] Installation completed successfully!" -ForegroundColor Green
Write-Host "To start the Voice Studio server, run: .\start-server.ps1" -ForegroundColor Cyan
Write-Host "To run CLI speech generation: python plugins/chatterbox/scripts/voice_studio_cli.py --help" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
