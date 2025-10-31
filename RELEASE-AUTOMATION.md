# Release Automation - Usage Examples 🚀

## Quick Release Guide

### Current Workflow (Manual)
```bash
# Old way - manual process
git tag v0.4.3
git push origin v0.4.3
```

### New Workflow (Automated) ✨
```bash
# New way - fully automated
bash scripts/release.sh
```

## Example Scenarios

### Scenario 1: Simple Patch Release
```bash
$ bash scripts/release.sh

🚀 Automated Release Script
==========================
ℹ️  Checking current version consistency...
  📄 manifest.json: 0.4.2
  📄 pyproject.toml: 0.4.2
  📄 test.js: 0.4.2
✅ All versions are consistent: 0.4.2
⚠️  Version 0.4.2 already exists as remote tag!

Options:
1) Auto-increment patch version (recommended)
2) Auto-increment minor version  
3) Auto-increment major version
4) Manually specify new version
5) Exit

Choose option (1-5): 1

ℹ️  Releasing version: 0.4.3

Proceed with release 0.4.3? (y/N): y

ℹ️  Updating version files...
ℹ️  Updating manifest.json to version 0.4.3
ℹ️  Updating pyproject.toml to version 0.4.3  
ℹ️  Updating test.js to version 0.4.3
✅ All version files updated to 0.4.3
✅ Version changes committed
ℹ️  Pushing version changes to remote...
✅ Version changes pushed to remote
ℹ️  Creating tag v0.4.3...
✅ Tag v0.4.3 created
ℹ️  Pushing tag to remote...
✅ Tag v0.4.3 pushed to remote

✅ 🎉 Release 0.4.3 completed successfully!
ℹ️  The release workflow should now be triggered automatically.
```

### Scenario 2: First Release (No Tag Exists)
```bash
$ bash scripts/release.sh

🚀 Automated Release Script  
==========================
ℹ️  Checking current version consistency...
✅ All versions are consistent: 0.4.2
ℹ️  Current version 0.4.2 is not yet tagged. Using it for release.
ℹ️  Releasing version: 0.4.2

Proceed with release 0.4.2? (y/N): y

ℹ️  Creating tag v0.4.2...
✅ Tag v0.4.2 created
ℹ️  Pushing tag to remote...  
✅ Tag v0.4.2 pushed to remote

✅ 🎉 Release 0.4.2 completed successfully!
```

### Scenario 3: Custom Version
```bash
Choose option (1-5): 4
Enter new version (e.g., 1.2.3): 1.0.0

ℹ️  Releasing version: 1.0.0
```

### Scenario 4: Safety Check Failed
```bash
$ bash scripts/release.sh

🚀 Automated Release Script
==========================  
❌ Working directory is not clean! Please commit or stash your changes.
 M custom_components/voice-replay/ui.py
?? new-feature.py
```

## Safety Features

### ✅ Pre-flight Checks
- **Git Repository**: Ensures you're in a git repo
- **Clean Working Directory**: No uncommitted changes allowed  
- **Version Consistency**: All version files must match
- **Remote Tag Check**: Prevents duplicate tags

### ✅ User Confirmations
- **Release Confirmation**: Explicit "Proceed?" prompt
- **Version Validation**: Semantic versioning format check
- **Duplicate Prevention**: Won't create existing tags

### ✅ Atomic Operations
- **Version Updates**: All files updated together
- **Single Commit**: Version changes in one commit
- **Tag Creation**: Only after successful push

## Error Handling

### Version Mismatch
```bash
❌ Version mismatch detected! Please fix version consistency first.
```
**Solution**: Run `bash scripts/check-version-consistency.sh` first

### Invalid Version Format  
```bash
❌ Invalid version format! Use semantic versioning (e.g., 1.2.3)
```
**Solution**: Use format like `1.2.3` (major.minor.patch)

### Duplicate Tag
```bash
❌ Version 1.0.0 also already exists as remote tag!
```
**Solution**: Choose a different version number

## Benefits Over Manual Process

| Manual Process | Automated Script |
|---------------|------------------|
| ❌ Error-prone | ✅ Consistent & safe |
| ❌ Multi-step | ✅ Single command |
| ❌ No validation | ✅ Built-in checks |
| ❌ Easy to forget steps | ✅ Automated workflow |
| ❌ Version inconsistency risk | ✅ Guaranteed consistency |

## PowerShell Usage (Windows)

All examples work the same with PowerShell:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\release.ps1
```