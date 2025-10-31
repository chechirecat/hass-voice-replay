# Git Hooks Setup

This directory contains Git hooks for automated version consistency checking.

## Quick Setup

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-hooks.ps1
```

### Unix/Linux/macOS/Git Bash
```bash
bash scripts/setup-hooks.sh
```

## What It Does

The pre-commit hook automatically checks that version numbers are consistent across:
- `custom_components/voice-replay/manifest.json`
- `pyproject.toml` 
- `custom_components/voice-replay/test.js`

If versions don't match, the commit will be rejected with details about the mismatch.

## Manual Version Check

### Windows PowerShell
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-version-consistency.ps1
```

### Git Bash / Unix / Linux / macOS
```bash
bash scripts/check-version-consistency.sh
```

## Bypassing the Hook

If you need to commit temporarily without the version check:
```bash
git commit --no-verify -m "Your commit message"
```

## Files

- `scripts/hooks/pre-commit` - Cross-platform pre-commit hook template
- `scripts/setup-hooks.sh` - Unix/Linux/macOS setup script  
- `scripts/setup-hooks.ps1` - Windows PowerShell setup script
- `scripts/check-version-consistency.sh` - Bash version checker
- `scripts/check-version-consistency.ps1` - PowerShell version checker