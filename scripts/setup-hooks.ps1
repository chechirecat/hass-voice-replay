# Cross-platform Git hooks setup for version consistency checking (PowerShell version)
# Run this script from PowerShell after cloning the repository to enable local version checks

Write-Host "Setting up Git hooks for version consistency checking..." -ForegroundColor Cyan

# Detect environment
$IsWindows = $env:OS -eq "Windows_NT"
$IsGitBash = ($env:TERM -eq "xterm") -or ($env:MSYSTEM -ne $null)
$IsWSL = $env:WSL_DISTRO_NAME -ne $null

if ($IsWindows -and !$IsWSL) {
    $Environment = "windows-powershell"
} elseif ($IsWSL) {
    $Environment = "wsl"
} else {
    $Environment = "unix-like"
}

Write-Host "Detected environment: $Environment" -ForegroundColor Gray

# Create hooks directory if it doesn't exist
if (!(Test-Path ".git\hooks")) {
    New-Item -ItemType Directory -Path ".git\hooks" -Force | Out-Null
}

# Copy the pre-commit hook
if (Test-Path "scripts\hooks\pre-commit") {
    Copy-Item "scripts\hooks\pre-commit" ".git\hooks\pre-commit" -Force
    # Set executable attribute (Windows equivalent)
    if ($IsWindows) {
        try {
            attrib +x ".git\hooks\pre-commit" 2>$null
        } catch {
            # Ignore errors setting executable attribute on Windows
        }
    }
    Write-Host "Pre-commit hook installed successfully!" -ForegroundColor Green
    Write-Host "   Version consistency will be checked before each commit." -ForegroundColor Gray
} else {
    Write-Host "Error: Hook template not found at scripts\hooks\pre-commit" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Hook setup complete for $Environment!" -ForegroundColor Green
Write-Host "   * Commits will be rejected if versions are inconsistent" -ForegroundColor Gray
Write-Host "   * Manual check commands:" -ForegroundColor Gray

switch ($Environment) {
    "windows-powershell" {
        Write-Host "     - PowerShell: powershell -ExecutionPolicy Bypass -File .\scripts\check-version-consistency.ps1" -ForegroundColor Gray
        Write-Host "     - Git Bash: bash scripts/check-version-consistency.sh" -ForegroundColor Gray
    }
    "wsl" {
        Write-Host "     - WSL/Bash: bash scripts/check-version-consistency.sh" -ForegroundColor Gray
        Write-Host "     - PowerShell: powershell -ExecutionPolicy Bypass -File .\scripts\check-version-consistency.ps1" -ForegroundColor Gray
    }
    default {
        Write-Host "     - Terminal: bash scripts/check-version-consistency.sh" -ForegroundColor Gray
    }
}

Write-Host "   * To bypass the hook temporarily: git commit --no-verify" -ForegroundColor Gray
Write-Host ""