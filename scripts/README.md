# Git Hooks Setup & Release Automation

This directory contains Git hooks for automated version consistency checking and release automation tools.

## Quick Setup

### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-hooks.ps1
```

### Unix/Linux/macOS/Git Bash
```bash
bash scripts/setup-hooks.sh
```

## Release Automation 🚀

### Automated Release Process

Instead of manually running `git tag` and `git push`, use the automated release script:

#### Windows (PowerShell)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release.ps1
```

#### Unix/Linux/macOS/Git Bash
```bash
bash scripts/release.sh
```

### What the Release Script Does

1. **Version Consistency Check**: Verifies all version files match
2. **Remote Tag Check**: Checks if current version already exists as a tag
3. **Version Increment**: Auto-increment or manual version specification
4. **File Updates**: Updates all version files with new version
5. **Git Operations**: Commits changes, creates tag, pushes everything
6. **Release Trigger**: Automatically triggers the release workflow

### Release Script Options

When current version already exists as a tag, you can:
- **Auto-increment patch** (0.4.2 → 0.4.3) - Recommended for bug fixes
- **Auto-increment minor** (0.4.2 → 0.5.0) - For new features
- **Auto-increment major** (0.4.2 → 1.0.0) - For breaking changes
- **Manual version** - Specify exact version (e.g., 1.2.3)

## Version Consistency Checking

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
- `scripts/release.sh` - Automated release script (Bash)
- `scripts/release.ps1` - Automated release script (PowerShell)