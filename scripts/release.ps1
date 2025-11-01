# Automated Release Script for hass-voice-replay (PowerShell version)
# This script automates the entire release process
#
# IMPORTANT: You may need to set PowerShell execution policy before running:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# See docs/POWERSHELL_EXECUTION_POLICY.md for complete details
#
# Usage: .\scripts\release.ps1 [-Help]

param(
    [switch]$Help
)

# Configuration
$ManifestFile = "custom_components\voice-replay\manifest.json"
$PyProjectFile = "pyproject.toml"
$TestJsFile = "custom_components\voice-replay\test.js"

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "INFO: $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "SUCCESS: $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "WARNING: $Message" -ForegroundColor Yellow
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Test-GitRepo {
    try {
        git rev-parse --git-dir 2>$null | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Test-WorkingDirectory {
    $status = git status --porcelain
    return $status.Length -eq 0
}

function Get-ManifestVersion {
    if (Test-Path $ManifestFile) {
        $content = Get-Content $ManifestFile -Raw
        $pattern = '"version":\s*"([^"]*)"'
        if ($content -match $pattern) {
            return $matches[1]
        }
    }
    return $null
}

function Get-PyProjectVersion {
    if (Test-Path $PyProjectFile) {
        $content = Get-Content $PyProjectFile -Raw
        $pattern = 'version\s*=\s*"([^"]*)"'
        if ($content -match $pattern) {
            return $matches[1]
        }
    }
    return $null
}

function Get-TestJsVersion {
    if (Test-Path $TestJsFile) {
        $content = Get-Content $TestJsFile -Raw
        $pattern = 'Version\s+(\d+\.\d+\.\d+)'
        if ($content -match $pattern) {
            return $matches[1]
        }
    }
    return $null
}

function Test-VersionConsistency {
    $manifestVersion = Get-ManifestVersion
    $pyprojectVersion = Get-PyProjectVersion
    $testjsVersion = Get-TestJsVersion

    Write-Info "Current versions:"
    Write-Host "  manifest.json: $manifestVersion"
    Write-Host "  pyproject.toml: $pyprojectVersion"
    Write-Host "  test.js: $testjsVersion"

    if (($manifestVersion -ne $pyprojectVersion) -or 
        ($manifestVersion -ne $testjsVersion) -or 
        ($pyprojectVersion -ne $testjsVersion)) {
        Write-ErrorMessage "Version mismatch detected! Please fix version consistency first."
        exit 1
    }

    return $manifestVersion
}

function Test-RemoteTag {
    param([string]$Version)
    $tag = "v$Version"

    # Fetch latest tags from remote
    git fetch --tags 2>$null

    # Check if tag exists locally after fetch
    $localTags = git tag -l
    return $localTags -contains $tag
}

function Step-Version {
    param([string]$Version, [string]$IncrementType)
    $versionParts = $Version.Split('.')
    $major = [int]$versionParts[0]
    $minor = [int]$versionParts[1]
    $patch = [int]$versionParts[2]

    switch ($IncrementType) {
        "major" {
            $major++
            $minor = 0
            $patch = 0
        }
        "minor" {
            $minor++
            $patch = 0
        }
        "patch" {
            $patch++
        }
        default {
            Write-ErrorMessage "Invalid increment type: $IncrementType"
            exit 1
        }
    }

    return "$major.$minor.$patch"
}

function Update-ManifestVersion {
    param([string]$NewVersion)
    Write-Info "Updating manifest.json to version $NewVersion"

    $content = Get-Content $ManifestFile -Raw
    $pattern = '"version":\s*"[^"]*"'
    $replacement = '"version": "' + $NewVersion + '"'
    $content = $content -replace $pattern, $replacement
    Set-Content $ManifestFile $content -NoNewline
}

function Update-PyProjectVersion {
    param([string]$NewVersion)
    Write-Info "Updating pyproject.toml to version $NewVersion"

    $lines = Get-Content $PyProjectFile
    $inProjectSection = $false
    $updated = $false
    
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\[project\]') {
            $inProjectSection = $true
            continue
        }
        if ($lines[$i] -match '^\[' -and $lines[$i] -notmatch '^\[project\]') {
            $inProjectSection = $false
            continue
        }
        if ($inProjectSection -and $lines[$i] -match '^version\s*=\s*"[^"]*"' -and -not $updated) {
            $lines[$i] = 'version = "' + $NewVersion + '"'
            $updated = $true
            break
        }
    }
    
    $lines | Set-Content $PyProjectFile
}

function Update-TestJsVersion {
    param([string]$NewVersion)
    Write-Info "Updating test.js to version $NewVersion"

    $content = Get-Content $TestJsFile -Raw
    $pattern = 'Version\s+\d+\.\d+\.\d+'
    $replacement = "Version $NewVersion"
    $content = $content -replace $pattern, $replacement
    Set-Content $TestJsFile $content -NoNewline
}

function Update-AllVersions {
    param([string]$NewVersion)

    Update-ManifestVersion $NewVersion
    Update-PyProjectVersion $NewVersion
    Update-TestJsVersion $NewVersion

    Write-Success "All version files updated to $NewVersion"
}

# Show help if requested
if ($Help) {
    Write-Host "Automated Release Script for hass-voice-replay (PowerShell)"
    Write-Host ""
    Write-Host "Usage: .\scripts\release.ps1"
    Write-Host ""
    Write-Host "This script will:"
    Write-Host "1. Check version consistency across all files"
    Write-Host "2. Check if current version is already tagged"
    Write-Host "3. Allow version increment if needed"
    Write-Host "4. Update all version files"
    Write-Host "5. Commit and push changes"
    Write-Host "6. Create and push release tag"
    Write-Host ""
    Write-Host "Prerequisites:"
    Write-Host "- Clean working directory (no uncommitted changes)"
    Write-Host "- All version files must be consistent"
    Write-Host ""
    exit 0
}

# Main execution
Write-Host "Release Script" -ForegroundColor Cyan
Write-Host "==============" -ForegroundColor Cyan

# Pre-flight checks
if (-not (Test-GitRepo)) {
    Write-ErrorMessage "Not in a git repository!"
    exit 1
}

if (-not (Test-WorkingDirectory)) {
    Write-ErrorMessage "Working directory is not clean! Please commit or stash your changes."
    git status --porcelain
    exit 1
}

# Check current version consistency
Write-Info "Checking current version consistency..."
$currentVersion = Test-VersionConsistency
Write-Success "All versions are consistent: $currentVersion"

# Check if current version already exists as tag
if (Test-RemoteTag $currentVersion) {
    Write-Warning "Version $currentVersion already exists as remote tag!"

    Write-Host ""
    Write-Host "Options:"
    Write-Host "1) Auto-increment patch version - recommended"
    Write-Host "2) Auto-increment minor version"
    Write-Host "3) Auto-increment major version"
    Write-Host "4) Manually specify new version"
    Write-Host "5) Exit"

    $choice = Read-Host "Choose option (1-5)"

    switch ($choice) {
        "1" {
            $newVersion = Step-Version $currentVersion "patch"
        }
        "2" {
            $newVersion = Step-Version $currentVersion "minor"
        }
        "3" {
            $newVersion = Step-Version $currentVersion "major"
        }
        "4" {
            $newVersion = Read-Host "Enter new version e.g. 1.2.3"
            # Basic validation
            if ($newVersion -notmatch '^\d+\.\d+\.\d+$') {
                Write-ErrorMessage "Invalid version format! Use semantic versioning e.g. 1.2.3"
                exit 1
            }
        }
        "5" {
            Write-Info "Release cancelled."
            exit 0
        }
        default {
            Write-ErrorMessage "Invalid choice!"
            exit 1
        }
    }

    # Check if new version already exists
    if (Test-RemoteTag $newVersion) {
        Write-ErrorMessage "Version $newVersion also already exists as remote tag!"
        exit 1
    }
}
else {
    Write-Info "Current version $currentVersion is not yet tagged. Using it for release."
    $newVersion = $currentVersion
}

Write-Info "Releasing version: $newVersion"

# Confirmation
Write-Host ""
$confirm = Read-Host "Proceed with release $newVersion? (y/N)"
if ($confirm -notmatch '^[Yy]$') {
    Write-Info "Release cancelled."
    exit 0
}

# Update versions if needed
if ($newVersion -ne $currentVersion) {
    Write-Info "Updating version files..."
    Update-AllVersions $newVersion

    # Commit version changes
    git add $ManifestFile $PyProjectFile $TestJsFile
    git commit -m "chore: bump version to $newVersion"
    Write-Success "Version changes committed"

    # Push changes
    Write-Info "Pushing version changes to remote..."
    git push origin main
    Write-Success "Version changes pushed to remote"
}

# Create and push tag
$tag = "v$newVersion"
Write-Info "Creating tag $tag..."
git tag $tag
Write-Success "Tag $tag created"

Write-Info "Pushing tag to remote..."
git push origin $tag
Write-Success "Tag $tag pushed to remote"

Write-Host ""
Write-Success "Release $newVersion completed successfully!"
Write-Info "The release workflow should now be triggered automatically."
Write-Host ""