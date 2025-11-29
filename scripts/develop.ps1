#!/usr/bin/env pwsh

# Development Script for hass-voice-replay
# This script sets up and starts Home Assistant in development mode

$ErrorActionPreference = "Stop"

# Change to project root directory
Set-Location (Split-Path $PSScriptRoot -Parent)

# Create config dir if not present
$ConfigPath = Join-Path $PWD "config"
if (-not (Test-Path $ConfigPath)) {
    Write-Host "📁 Creating config directory..." -ForegroundColor Blue
    New-Item -ItemType Directory -Path $ConfigPath -Force | Out-Null
    hass --config $ConfigPath --script ensure_config
}

# Home Assistant will use 'import custom_components' to load custom components
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$($env:PYTHONPATH);$PWD" } else { $PWD }

Write-Host "🚀 Starting Home Assistant in development mode..." -ForegroundColor Green
Write-Host "📍 Config directory: $ConfigPath" -ForegroundColor Cyan
Write-Host "🐍 PYTHONPATH: $($env:PYTHONPATH)" -ForegroundColor Cyan

# Start Home Assistant
hass --config $ConfigPath --debug
