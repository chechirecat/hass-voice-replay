# Release Automation Guide

This guide describes the automated release process for the Voice Replay Integration.

## Overview

The Voice Replay Integration uses automated release scripts to manage version increments, git tagging, and release triggers. The system is designed to be safe and reliable, with multiple validation steps to prevent release errors.

## Script Locations

- **Bash Script:** `scripts/release.sh` (Linux/macOS/WSL)
- **PowerShell Script:** `scripts/release.ps1` (Windows/Cross-platform)

Both scripts provide identical functionality with platform-appropriate implementations.

## Quick Start

### Basic Usage

```bash
# Show help and options
./scripts/release.sh --help

# Create a patch release (recommended for bug fixes)
./scripts/release.sh

# Create a minor release (for new features)
./scripts/release.sh --increment minor

# Create a major release (for breaking changes)
./scripts/release.sh --increment major
```

### PowerShell Usage

**Important:** Before running PowerShell scripts, you may need to set the execution policy. See **[PowerShell Execution Policy Guide](POWERSHELL_EXECUTION_POLICY.md)** for complete details.

```powershell
# Quick setup - required for most Windows systems
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then you can run the release scripts:

```powershell
# Show help and options
.\scripts\release.ps1 -Help

# Create releases
.\scripts\release.ps1
.\scripts\release.ps1 -Increment minor
.\scripts\release.ps1 -Increment major

# Check version consistency
.\scripts\check-version-consistency.ps1 -Verbose
```

## Release Process Flow

### 1. Pre-Release Validation
- ✅ **Working Directory Check:** Ensures no uncommitted changes
- ✅ **Branch Check:** Confirms you're on the `main` branch
- ✅ **Remote Access:** Verifies git remote connectivity
- ✅ **Version Consistency:** Validates all version files match

### 2. Version Management
- 🔢 **Multi-File Detection:** Reads versions from manifest.json, pyproject.toml, and test.js
- 🔍 **Consistency Check:** Ensures all version files have the same value
- ➕ **Version Increment:** Calculates new version based on increment type
- 🔍 **Duplicate Check:** Verifies new version doesn't already exist remotely

### 3. Release Execution
- 📁 **File Updates:** Modifies version in all three files simultaneously
- 💾 **Git Commit:** Commits version changes with standard message
- 🔖 **Tag Creation:** Creates annotated git tag with version
- 🚀 **Push Operations:** Pushes both commit and tag to remote
- ⚙️ **CI Trigger:** Triggers GitHub Actions release workflow

## Version Management

### Multiple Source Files

The integration maintains version consistency across three files:

```json
// custom_components/voice-replay/manifest.json
{
  "version": "1.2.3"
}
```

```toml
# pyproject.toml
[project]
version = "1.2.3"
```

```javascript
// tests/test.js
const INTEGRATION_VERSION = "1.2.3";
```

### Version Consistency Validation

Before each release, the script validates that all three files contain the same version:

```bash
# Extract versions from each file
MANIFEST_VERSION=$(jq -r '.version' custom_components/voice-replay/manifest.json)
PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
TEST_VERSION=$(grep 'INTEGRATION_VERSION = ' tests/test.js | sed 's/.*"\(.*\)".*/\1/')

# Ensure they all match
if [[ "$MANIFEST_VERSION" != "$PYPROJECT_VERSION" ]] || [[ "$MANIFEST_VERSION" != "$TEST_VERSION" ]]; then
    echo "❌ Version mismatch detected!"
    exit 1
fi
```

### Version Increment Types

| Type | Example Change | Use Case |
|------|----------------|----------|
| `patch` | `1.2.3` → `1.2.4` | Bug fixes, small improvements |
| `minor` | `1.2.3` → `1.3.0` | New features, enhancements |
| `major` | `1.2.3` → `2.0.0` | Breaking changes, major updates |

## Safety Features

### Pre-Release Checks

1. **Clean Working Directory**
   ```bash
   # Checks for uncommitted changes
   git status --porcelain
   ```

2. **Correct Branch**
   ```bash
   # Ensures you're on main branch
   git branch --show-current
   ```

3. **Remote Connectivity**
   ```bash
   # Verifies git remote access
   git ls-remote --heads origin main
   ```

4. **Version File Existence**
   ```bash
   # Confirms all required files exist
   [ -f "custom_components/voice-replay/manifest.json" ]
   [ -f "pyproject.toml" ]
   [ -f "tests/test.js" ]
   ```

5. **Version Consistency**
   ```bash
   # Validates all versions match
   check_version_consistency
   ```

6. **Semantic Versioning**
   ```bash
   # Confirms version follows semantic versioning
   [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
   ```

7. **Duplicate Prevention**
   ```bash
   # Checks if tag already exists remotely
   git ls-remote --tags origin "v$new_version"
   ```

### Error Handling

The scripts include comprehensive error handling:

- **Invalid Increment Type:** Clear error message with valid options
- **Version Inconsistency:** Detailed report of mismatched versions
- **File Not Found:** Helpful guidance about required files
- **Remote Tag Exists:** Prevents overwriting existing releases
- **Git Errors:** Detailed error reporting for git operations
- **Permission Issues:** Clear guidance for access problems

## CI/CD Integration

### GitHub Actions Workflow

The release process integrates with GitHub Actions (`.github/workflows/release.yaml`):

1. **Trigger:** Git tag push (created by release script)
2. **Version Detection:** Automatic from git tag
3. **Prerelease Logic:** Smart detection based on version patterns
4. **Asset Creation:** Automated packaging and upload
5. **Release Notes:** Automatic generation from commits

### Prerelease Detection

The GitHub Actions workflow automatically determines prerelease status:

```yaml
prerelease: ${{ contains(github.ref_name, '-') || contains(github.ref_name, 'alpha') || contains(github.ref_name, 'beta') || contains(github.ref_name, 'rc') }}
```

Examples:
- `v1.2.4` → Stable release
- `v1.3.0-beta` → Prerelease
- `v2.0.0-alpha.1` → Prerelease

### Version Consistency in CI

The CI pipeline includes version consistency checks in the lint workflow:

```yaml
- name: Check version consistency
  run: |
    ./scripts/check-version-consistency.sh
```

This ensures version drift is caught early, before release time.

## Troubleshooting

### Common Issues

#### "Working directory is not clean"
```bash
# Check what files are changed
git status

# Either commit changes or stash them
git add . && git commit -m "Prepare for release"
# OR
git stash
```

#### "Not on main branch"
```bash
# Switch to main branch
git checkout main

# Make sure it's up to date
git pull origin main
```

#### "Version mismatch detected"
The script found inconsistent versions across the three files.

```bash
# Check current versions
./scripts/check-version-consistency.sh

# Manually fix versions to match, then commit
git add . && git commit -m "Fix version consistency"
```

#### "Version already exists remotely"
The script detected that the target version already has a git tag.

```bash
# Check existing tags
git tag -l | grep "v1.2"

# Use a different increment type or check what version you actually want
./scripts/release.sh --increment minor
```

#### "Permission denied" or "Authentication failed"
```bash
# Check git remote configuration
git remote -v

# Ensure you have push access to the repository
# May need to configure SSH keys or personal access tokens
```

#### "Required file not found"
One of the three version files is missing or in the wrong location.

```bash
# Check file structure
ls -la custom_components/voice-replay/manifest.json
ls -la pyproject.toml
ls -la tests/test.js

# Ensure you're in the repository root directory
```

### Getting Help

1. **Script Help:** Use `--help` flag for detailed usage information
2. **Verbose Output:** Scripts provide detailed progress information
3. **Version Check:** Use `./scripts/check-version-consistency.sh` to diagnose version issues
4. **Git Status:** Check `git status` and `git log --oneline -5` for context
5. **Remote Check:** Use `git ls-remote origin` to verify remote connectivity

## Best Practices

### Before Releasing

1. **Test Thoroughly:** Ensure integration works in Home Assistant
2. **Update Documentation:** Keep README.md and docstrings current
3. **Check Dependencies:** Verify compatibility with HA versions
4. **Review Changes:** Use `git log` to review commits since last release
5. **Validate Version Consistency:** Run version check script

### Version Selection

- **Patch releases** for bug fixes and minor improvements
- **Minor releases** for new features that maintain backward compatibility
- **Major releases** for breaking changes or significant architectural updates

### Release Timing

- **Regular Schedule:** Consider regular release cycles (e.g., monthly)
- **Hotfixes:** Use patch releases for critical bug fixes
- **Feature Releases:** Bundle related features into minor releases
- **Breaking Changes:** Clearly communicate major releases with migration guides

### Post-Release

1. **Verify Release:** Check GitHub Releases page for successful deployment
2. **Update HACS:** Monitor HACS integration for proper discovery
3. **Community Updates:** Consider posting to Home Assistant Community Forum
4. **Documentation:** Update any external documentation or guides

## Advanced Usage

### Manual Version Override

If you need to set a specific version (not recommended for normal use):

```bash
# Manually edit all three files to the same version
# manifest.json: "version": "2.0.0"
# pyproject.toml: version = "2.0.0"  
# test.js: const INTEGRATION_VERSION = "2.0.0";

# Commit the changes
git add . && git commit -m "Set version to 2.0.0"

# Then run release script normally
./scripts/release.sh
```

### Release from Feature Branch

While not recommended, you can technically release from other branches:

```bash
# The script will warn you but can be modified to allow this
# Edit the script to comment out the branch check if needed
# (Not recommended for production releases)
```

### Dry Run Testing

To test the release process without actually releasing:

```bash
# Create a test script that shows what would happen
./scripts/release.sh --help  # Study the process
git tag -l | head -5         # Check current tags
git status                   # Verify clean state
./scripts/check-version-consistency.sh  # Check versions
```

## Script Maintenance

### Updating Release Scripts

When modifying the release scripts:

1. **Test Both Versions:** Ensure bash and PowerShell scripts remain synchronized
2. **Validate Version Detection:** Test with various version formats
3. **Error Scenarios:** Test error conditions and edge cases
4. **Cross-Platform:** Verify functionality on Windows, macOS, and Linux

### Version File Format Updates

If version file formats change:

1. Update the parsing logic in both scripts
2. Update the version consistency check script
3. Test with the new format
4. Update this documentation
5. Consider backward compatibility

### Adding New Version Files

If new files need version tracking:

1. Add to version extraction logic
2. Add to version update logic  
3. Add to consistency checking
4. Update documentation
5. Test thoroughly

---

This guide covers the complete release automation system for the Voice Replay Integration. For questions or improvements, please open an issue or discussion in the repository.