#!/usr/bin/env pwsh

# Linting Script for hass-voice-replay
# This script runs ruff linting and formatting checks

$ErrorActionPreference = "Stop"

# Change to project root directory
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "🔍 Running ruff linting with auto-fix..." -ForegroundColor Blue
ruff check . --fix

Write-Host "🎨 Running ruff formatting..." -ForegroundColor Blue
ruff format

Write-Host "✅ Linting and formatting complete!" -ForegroundColor Green
