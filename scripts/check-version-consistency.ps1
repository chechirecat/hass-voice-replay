# PowerShell version of version consistency check
# This script checks if versions match across manifest.json, pyproject.toml, and test.js
#
# IMPORTANT: You may need to set PowerShell execution policy before running:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# See docs/POWERSHELL_EXECUTION_POLICY.md for complete details
#
# Usage: .\scripts\check-version-consistency.ps1 [-Verbose]

param(
    [switch]$Verbose = $false
)

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    switch ($Color) {
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Cyan" { Write-Host $Message -ForegroundColor Cyan }
        "Gray" { Write-Host $Message -ForegroundColor Gray }
        default { Write-Host $Message }
    }
}

function Get-ManifestVersion {
    if (Test-Path "custom_components\voice-replay\manifest.json") {
        try {
            $manifest = Get-Content "custom_components\voice-replay\manifest.json" -Raw | ConvertFrom-Json
            return $manifest.version
        }
        catch {
            Write-ColorOutput "Error reading manifest.json: $_" "Red"
            return $null
        }
    }
    return $null
}

function Get-PyProjectVersion {
    if (Test-Path "pyproject.toml") {
        try {
            $lines = Get-Content "pyproject.toml"
            $inProjectSection = $false
            foreach ($line in $lines) {
                if ($line -match '^\[project\]') {
                    $inProjectSection = $true
                    continue
                }
                if ($line -match '^\[' -and $line -notmatch '^\[project\]') {
                    $inProjectSection = $false
                    continue
                }
                if ($inProjectSection -and $line -match '^version\s*=\s*"([^"]+)"') {
                    return $matches[1]
                }
            }
        }
        catch {
            Write-ColorOutput "Error reading pyproject.toml: $_" "Red"
        }
    }
    return $null
}

function Get-TestJsVersion {
    if (Test-Path "custom_components\voice-replay\test.js") {
        try {
            $content = Get-Content "custom_components\voice-replay\test.js" -Raw
            # Look for the version pattern in console.info output: Version 0.4.2
            if ($content -match 'Version\s+([0-9]+\.[0-9]+\.[0-9]+)') {
                return $matches[1]
            }
        }
        catch {
            Write-ColorOutput "Error reading test.js: $_" "Red"
        }
    }
    return $null
}

function Get-CardVersion {
    if (Test-Path "voice-replay-card.js") {
        try {
            $content = Get-Content "voice-replay-card.js" -Raw
            if ($content -match "CARD_VERSION = '([^']+)'") {
                return $matches[1]
            }
        }
        catch {
            Write-ColorOutput "Error reading voice-replay-card.js: $_" "Red"
        }
    }
    return $null
}

function Get-PackageVersion {
    if (Test-Path "package.json") {
        try {
            $content = Get-Content "package.json" -Raw | ConvertFrom-Json
            return $content.version
        }
        catch {
            Write-ColorOutput "Error reading package.json: $_" "Red"
        }
    }
    return $null
}

function Get-LatestGitTag {
    try {
        # Get the latest tag that matches v*.*.* pattern
        $latestTag = git describe --tags --abbrev=0 --match="v*.*.*" 2>$null
        if ($latestTag -and $latestTag -match '^v(.+)$') {
            return $matches[1]  # Return version without 'v' prefix
        }
    }
    catch {
        Write-ColorOutput "Error getting git tags: $_" "Red"
    }
    return $null
}

# Main execution
Write-ColorOutput "Checking version consistency..." "Cyan"
Write-Host ""

# Auto-detect repository type
if (Test-Path "custom_components\voice-replay\manifest.json") {
    # Backend repository
    $repoName = "hass-voice-replay"
    $primaryVersion = Get-ManifestVersion
    Write-ColorOutput "Detected repository: $repoName" "Yellow"
    
    if (-not $primaryVersion) {
        Write-ColorOutput "Could not extract version from manifest.json" "Red"
        exit 1
    }
    
    $manifestVersion = $primaryVersion
    $pyprojectVersion = Get-PyProjectVersion
    $testJsVersion = Get-TestJsVersion
    $gitTagVersion = Get-LatestGitTag
    
    $foundVersions = @()
    $missingFiles = @()

    if ($manifestVersion) {
        $foundVersions += @{ File = "manifest.json"; Version = $manifestVersion; Path = "custom_components\voice-replay\manifest.json" }
        if ($Verbose) { Write-ColorOutput "manifest.json version: $manifestVersion" "Gray" }
    } else {
        $missingFiles += "custom_components\voice-replay\manifest.json"
    }

    if ($pyprojectVersion) {
        $foundVersions += @{ File = "pyproject.toml"; Version = $pyprojectVersion; Path = "pyproject.toml" }
        if ($Verbose) { Write-ColorOutput "pyproject.toml version: $pyprojectVersion" "Gray" }
    } else {
        $missingFiles += "pyproject.toml"
    }

    if ($testJsVersion) {
        $foundVersions += @{ File = "test.js"; Version = $testJsVersion; Path = "custom_components\voice-replay\test.js" }
        if ($Verbose) { Write-ColorOutput "test.js version: $testJsVersion" "Gray" }
    } else {
        $missingFiles += "custom_components\voice-replay\test.js"
    }
    
} elseif (Test-Path "voice-replay-card.js") {
    # Frontend repository
    $repoName = "hass-voice-replay-card"
    $primaryVersion = Get-CardVersion
    Write-ColorOutput "Detected repository: $repoName" "Yellow"
    
    if (-not $primaryVersion) {
        Write-ColorOutput "Could not extract version from voice-replay-card.js" "Red"
        exit 1
    }
    
    $cardVersion = $primaryVersion
    $gitTagVersion = Get-LatestGitTag
    
    $foundVersions = @()
    $missingFiles = @()

    if ($cardVersion) {
        $foundVersions += @{ File = "voice-replay-card.js"; Version = $cardVersion; Path = "voice-replay-card.js" }
        if ($Verbose) { Write-ColorOutput "voice-replay-card.js version: $cardVersion" "Gray" }
    } else {
        $missingFiles += "voice-replay-card.js"
    }
    
} else {
    Write-ColorOutput "Could not detect Voice Replay repository type" "Red"
    Write-ColorOutput "This script should be run from either:" "Red"
    Write-ColorOutput "  - hass-voice-replay repository (contains custom_components/)" "Red"
    Write-ColorOutput "  - hass-voice-replay-card repository (contains voice-replay-card.js)" "Red"
    exit 1
}

Write-ColorOutput "Target version: $primaryVersion" "Green"

# Add git tag version (common to both repositories) - but handle release commits
if ($gitTagVersion) {
    if ($gitTagVersion -eq $primaryVersion) {
        $foundVersions += @{ File = "git tag"; Version = $gitTagVersion; Path = "latest git tag (v$gitTagVersion)" }
    } else {
        # During release commits, the tag hasn't been created yet
        # Only treat as error if the file versions are older than the latest tag
        $versionComparison = [System.Version]::new($primaryVersion) -lt [System.Version]::new($gitTagVersion)
        if ($versionComparison) {
            Write-ColorOutput "Error: File version $primaryVersion is older than latest tag v$gitTagVersion" "Red"
            $foundVersions += @{ File = "git tag"; Version = $gitTagVersion; Path = "latest git tag (v$gitTagVersion)" }
        } else {
            Write-ColorOutput "Note: Git tag v$gitTagVersion exists, v$primaryVersion will be tagged during release" "Yellow"
        }
    }
    if ($Verbose) { Write-ColorOutput "latest git tag version: $gitTagVersion" "Gray" }
} else {
    if ($Verbose) { Write-ColorOutput "No git tags found matching v*.*.* pattern" "Gray" }
}

if ($missingFiles.Count -gt 0) {
    Write-ColorOutput "Missing version files:" "Yellow"
    foreach ($file in $missingFiles) {
        Write-ColorOutput "  - $file" "Yellow"
    }
    Write-Host ""
}

if ($foundVersions.Count -eq 0) {
    Write-ColorOutput "No version files found!" "Red"
    exit 1
}

# Check for consistency
$uniqueVersions = $foundVersions | ForEach-Object { $_.Version } | Sort-Object -Unique

if ($uniqueVersions.Count -eq 1) {
    $version = $uniqueVersions | Select-Object -First 1
    Write-ColorOutput "All versions are consistent: $version" "Green"
    if ($foundVersions.Count -gt 1) {
        Write-ColorOutput "   Found in $($foundVersions.Count) files:" "Gray"
        foreach ($item in $foundVersions) {
            Write-ColorOutput "   - $($item.File)" "Gray"
        }
    }
    Write-Host ""
    Write-ColorOutput "Version: $version" "Green"
    exit 0
} else {
    Write-ColorOutput "Version mismatch detected!" "Red"
    Write-Host ""
    Write-ColorOutput "Different versions found:" "Red"
    
    # Show each file and its version
    foreach ($item in $foundVersions) {
        Write-ColorOutput "   $($item.File): $($item.Version) ($($item.Path))" "Yellow"
    }
    
    Write-Host ""
    Write-ColorOutput "To fix version inconsistencies:" "Red"
    
    if ($repoName -eq "hass-voice-replay") {
        Write-ColorOutput "  1. Update custom_components/voice-replay/manifest.json" "Red"
        Write-ColorOutput "  2. Update pyproject.toml" "Red"
        Write-ColorOutput "  3. Update custom_components/voice-replay/test.js" "Red"
        Write-ColorOutput "  4. Check any Python files for hardcoded versions" "Red"
    } elseif ($repoName -eq "hass-voice-replay-card") {
        Write-ColorOutput "  1. Update CARD_VERSION in voice-replay-card.js" "Red"
        Write-ColorOutput "  2. Update version in package.json" "Red"
    }
    
    Write-Host ""
    Write-ColorOutput "All versions should be: $primaryVersion" "Green"
    exit 1
}