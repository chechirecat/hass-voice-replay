#!/bin/bash

# Version Consistency Checker for Voice Replay Project
# This script validates that all version occurrences match across files

set -e

echo "🔍 Checking version consistency..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to extract version from manifest.json
get_manifest_version() {
    if [[ -f "custom_components/voice-replay/manifest.json" ]]; then
        grep '"version"' custom_components/voice-replay/manifest.json | sed 's/.*"version": *"\([^"]*\)".*/\1/'
    else
        echo ""
    fi
}

# Function to extract version from pyproject.toml
get_pyproject_version() {
    if [[ -f "pyproject.toml" ]]; then
        grep '^version = ' pyproject.toml | sed 's/version = "\([^"]*\)".*/\1/'
    else
        echo ""
    fi
}

# Function to extract version from test.js
get_testjs_version() {
    if [[ -f "custom_components/voice-replay/test.js" ]]; then
        grep "Version [0-9]" custom_components/voice-replay/test.js | sed 's/.*Version \([0-9.]*\).*/\1/'
    else
        echo ""
    fi
}

# Function to extract version from card JS file
get_card_version() {
    if [[ -f "voice-replay-card.js" ]]; then
        grep "CARD_VERSION = " voice-replay-card.js | sed "s/.*CARD_VERSION = '\([^']*\)'.*/\1/"
    else
        echo ""
    fi
}

# Function to extract version from package.json
get_package_version() {
    if [[ -f "package.json" ]]; then
        grep '"version"' package.json | sed 's/.*"version": *"\([^"]*\)".*/\1/'
    else
        echo ""
    fi
}

# Function to get all version occurrences in a repository
check_repository_versions() {
    local repo_name="$1"
    local expected_version="$2"
    local errors=0
    
    echo -e "\n📦 Checking ${YELLOW}${repo_name}${NC} repository..."
    
    if [[ "$repo_name" == "hass-voice-replay" ]]; then
        # Backend repository checks
        manifest_version=$(get_manifest_version)
        pyproject_version=$(get_pyproject_version)
        testjs_version=$(get_testjs_version)
        
        if [[ -n "$manifest_version" ]]; then
            if [[ "$manifest_version" == "$expected_version" ]]; then
                echo -e "  ✅ manifest.json: ${GREEN}${manifest_version}${NC}"
            else
                echo -e "  ❌ manifest.json: ${RED}${manifest_version}${NC} (expected: ${expected_version})"
                errors=$((errors + 1))
            fi
        fi
        
        if [[ -n "$pyproject_version" ]]; then
            if [[ "$pyproject_version" == "$expected_version" ]]; then
                echo -e "  ✅ pyproject.toml: ${GREEN}${pyproject_version}${NC}"
            else
                echo -e "  ❌ pyproject.toml: ${RED}${pyproject_version}${NC} (expected: ${expected_version})"
                errors=$((errors + 1))
            fi
        fi
        
        if [[ -n "$testjs_version" ]]; then
            if [[ "$testjs_version" == "$expected_version" ]]; then
                echo -e "  ✅ test.js: ${GREEN}${testjs_version}${NC}"
            else
                echo -e "  ❌ test.js: ${RED}${testjs_version}${NC} (expected: ${expected_version})"
                errors=$((errors + 1))
            fi
        fi
        
        # Check if there are any other version references in Python files
        if grep -r "version.*=.*['\"].*[0-9]" custom_components/ --include="*.py" 2>/dev/null | grep -v "__pycache__" | grep -v ".pyc"; then
            echo -e "  ⚠️  ${YELLOW}Found version references in Python files - please verify manually${NC}"
        fi
        
    elif [[ "$repo_name" == "hass-voice-replay-card" ]]; then
        # Frontend repository checks
        card_version=$(get_card_version)
        package_version=$(get_package_version)
        
        if [[ -n "$card_version" ]]; then
            if [[ "$card_version" == "$expected_version" ]]; then
                echo -e "  ✅ voice-replay-card.js: ${GREEN}${card_version}${NC}"
            else
                echo -e "  ❌ voice-replay-card.js: ${RED}${card_version}${NC} (expected: ${expected_version})"
                errors=$((errors + 1))
            fi
        fi
        
        if [[ -n "$package_version" ]]; then
            if [[ "$package_version" == "$expected_version" ]]; then
                echo -e "  ✅ package.json: ${GREEN}${package_version}${NC}"
            else
                echo -e "  ❌ package.json: ${RED}${package_version}${NC} (expected: ${expected_version})"
                errors=$((errors + 1))
            fi
        fi
    fi
    
    return $errors
}

# Auto-detect which repository we're in
if [[ -f "custom_components/voice-replay/manifest.json" ]]; then
    # We're in the backend repository
    REPO_NAME="hass-voice-replay"
    VERSION=$(get_manifest_version)
    echo -e "📍 Detected repository: ${YELLOW}${REPO_NAME}${NC}"
    echo -e "🎯 Target version: ${GREEN}${VERSION}${NC}"
    
elif [[ -f "voice-replay-card.js" ]]; then
    # We're in the frontend repository
    REPO_NAME="hass-voice-replay-card"
    VERSION=$(get_card_version)
    echo -e "📍 Detected repository: ${YELLOW}${REPO_NAME}${NC}"
    echo -e "🎯 Target version: ${GREEN}${VERSION}${NC}"
    
else
    echo -e "${RED}❌ Could not detect Voice Replay repository type${NC}"
    echo "This script should be run from either:"
    echo "  - hass-voice-replay repository (contains custom_components/)"
    echo "  - hass-voice-replay-card repository (contains voice-replay-card.js)"
    exit 1
fi

if [[ -z "$VERSION" ]]; then
    echo -e "${RED}❌ Could not extract version from primary source${NC}"
    exit 1
fi

# Check version consistency
total_errors=0
check_repository_versions "$REPO_NAME" "$VERSION"
total_errors=$?

# Summary
echo -e "\n📊 Version Consistency Check Summary:"
if [[ $total_errors -eq 0 ]]; then
    echo -e "✅ ${GREEN}All versions are consistent!${NC}"
    echo -e "📌 Version: ${GREEN}${VERSION}${NC}"
    exit 0
else
    echo -e "❌ ${RED}Found ${total_errors} version inconsistency/ies${NC}"
    echo -e "\n🔧 To fix version inconsistencies:"
    
    if [[ "$REPO_NAME" == "hass-voice-replay" ]]; then
        echo "  1. Update custom_components/voice-replay/manifest.json"
        echo "  2. Update pyproject.toml"
        echo "  3. Update custom_components/voice-replay/test.js"
        echo "  4. Check any Python files for hardcoded versions"
    elif [[ "$REPO_NAME" == "hass-voice-replay-card" ]]; then
        echo "  1. Update CARD_VERSION in voice-replay-card.js"
        echo "  2. Update version in package.json"
    fi
    
    echo -e "\n💡 All versions should be: ${GREEN}${VERSION}${NC}"
    exit 1
fi