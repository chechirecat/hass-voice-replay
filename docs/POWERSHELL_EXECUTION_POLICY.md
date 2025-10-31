# PowerShell Execution Policy Documentation Update

## Summary

Added comprehensive documentation about PowerShell execution policy requirements for running PowerShell scripts in the Voice Replay project.

## Files Updated

### Documentation Files:
1. **`docs/DEVELOPMENT.md`** - Added execution policy note to "Running Development Tools" section
2. **`docs/RELEASE_AUTOMATION.md`** - Added execution policy info to "PowerShell Usage" section

### Script Files (Header Comments):
3. **`scripts/check-version-consistency.ps1`** - Added execution policy note in script header
4. **`scripts/release.ps1`** - Added execution policy note in script header  
5. **`../hass-voice-replay-card/scripts/release.ps1`** - Added execution policy note in script header

## What Was Added

### Required Command:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Why This Is Needed:
- **Windows Default:** PowerShell execution policy is set to "Restricted" by default
- **Security Measure:** Prevents execution of unsigned scripts from the internet
- **Local Scripts:** `RemoteSigned` allows locally created scripts to run
- **User Scope:** `-Scope CurrentUser` doesn't require Administrator privileges

### Where Users Will See This:
1. **Development Setup:** Clear instructions in development guide
2. **Release Process:** Prominent warning in release automation guide  
3. **Script Headers:** Immediate guidance when viewing script files
4. **Error Context:** Users encountering execution errors will find help

## Example Documentation Added:

### Development Guide:
```markdown
**Note for Windows PowerShell users:** Before running PowerShell scripts, you may need to set the execution policy:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Script Headers:
```powershell
# IMPORTANT: You may need to set PowerShell execution policy before running:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Impact:
- ✅ **Prevents User Confusion:** Clear upfront guidance about execution policy
- ✅ **Reduces Support Issues:** Users won't get stuck on execution policy errors
- ✅ **Cross-Platform Clarity:** Windows users have specific guidance they need
- ✅ **Security Awareness:** Users understand what the command does and why it's safe