# PowerShell version of version consistency check
# This script checks if versions match across manifest.json, pyproject.toml, and test.js

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
            $content = Get-Content "pyproject.toml" -Raw
            if ($content -match 'version\s*=\s*"([^"]+)"') {
                return $matches[1]
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

# Main execution
Write-ColorOutput "Checking version consistency..." "Cyan"
Write-Host ""

$manifestVersion = Get-ManifestVersion
$pyprojectVersion = Get-PyProjectVersion
$testJsVersion = Get-TestJsVersion

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
    Write-ColorOutput "Please update all files to use the same version." "Red"
    exit 1
}