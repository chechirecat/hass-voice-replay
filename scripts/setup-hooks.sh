#!/bin/bash

# Cross-platform Git hooks setup for version consistency checking
# Run this script after cloning the repository to enable local version checks
# Works on Unix-like systems (Linux, macOS) and Windows (Git Bash, WSL)

echo "🔧 Setting up Git hooks for version consistency checking..."

# Detect the operating system
detect_environment() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        echo "windows-gitbash"
    elif [[ -n "$WSL_DISTRO_NAME" ]]; then
        echo "wsl"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unix"
    fi
}

ENV=$(detect_environment)
echo "🔍 Detected environment: $ENV"

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Copy the pre-commit hook
if [ -f "scripts/hooks/pre-commit" ]; then
    cp scripts/hooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "✅ Pre-commit hook installed successfully!"
    echo "   Version consistency will be checked before each commit."
else
    echo "❌ Error: Hook template not found at scripts/hooks/pre-commit"
    exit 1
fi

echo ""
echo "🎯 Hook setup complete for $ENV!"
echo "   • Commits will be rejected if versions are inconsistent"
echo "   • Manual check commands:"

case $ENV in
    "windows-gitbash")
        echo "     - Git Bash: bash scripts/check-version-consistency.sh"
        echo "     - PowerShell: powershell -File scripts/check-version-consistency.ps1"
        ;;
    "wsl"|"linux"|"macos"|"unix")
        echo "     - Terminal: bash scripts/check-version-consistency.sh"
        ;;
esac

echo "   • To bypass the hook temporarily: git commit --no-verify"
echo ""