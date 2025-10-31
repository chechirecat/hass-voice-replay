#!/bin/bash

# Automated Release Script for hass-voice-replay
# This script automates the entire release process:
# 1. Check current version across all files
# 2. Verify if version already exists as remote tag
# 3. Increment version (auto or manual)
# 4. Update all version files
# 5. Commit and push changes
# 6. Create and push release tag

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MANIFEST_FILE="custom_components/voice-replay/manifest.json"
PYPROJECT_FILE="pyproject.toml"
TESTJS_FILE="custom_components/voice-replay/test.js"

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository!"
        exit 1
    fi
}

# Check if working directory is clean
check_working_directory() {
    if ! git diff-index --quiet HEAD --; then
        log_error "Working directory is not clean! Please commit or stash your changes."
        git status --porcelain
        exit 1
    fi
}

# Extract version from manifest.json
get_manifest_version() {
    if [[ -f "$MANIFEST_FILE" ]]; then
        grep '"version"' "$MANIFEST_FILE" | sed 's/.*"version":\s*"\([^"]*\)".*/\1/'
    fi
}

# Extract version from pyproject.toml
get_pyproject_version() {
    if [[ -f "$PYPROJECT_FILE" ]]; then
        grep 'version = ' "$PYPROJECT_FILE" | sed 's/.*version = "\([^"]*\)".*/\1/'
    fi
}

# Extract version from test.js
get_testjs_version() {
    if [[ -f "$TESTJS_FILE" ]]; then
        grep "Version [0-9]" "$TESTJS_FILE" | sed 's/.*Version \([0-9.]*\).*/\1/'
    fi
}

# Check version consistency
check_version_consistency() {
    local manifest_version=$(get_manifest_version)
    local pyproject_version=$(get_pyproject_version)
    local testjs_version=$(get_testjs_version)

    log_info "Current versions:"
    echo "  📄 manifest.json: $manifest_version"
    echo "  📄 pyproject.toml: $pyproject_version"
    echo "  📄 test.js: $testjs_version"

    if [[ "$manifest_version" != "$pyproject_version" ]] || 
       [[ "$manifest_version" != "$testjs_version" ]] || 
       [[ "$pyproject_version" != "$testjs_version" ]]; then
        log_error "Version mismatch detected! Please fix version consistency first."
        exit 1
    fi

    return 0
}

# Get current version (separate from consistency check)
get_current_version() {
    get_manifest_version
}

# Check if version tag exists remotely
check_remote_tag() {
    local version="$1"
    local tag="v$version"

    # Fetch latest tags from remote
    git fetch --tags > /dev/null 2>&1

    # Check if tag exists locally after fetch
    if git tag -l | grep -q "^$tag$"; then
        return 0  # Tag exists
    else
        return 1  # Tag doesn't exist
    fi
}

# Increment version number
increment_version() {
    local version="$1"
    local increment_type="$2"

    # Parse version (assuming semantic versioning: major.minor.patch)
    local IFS='.'
    read -ra VERSION_PARTS <<< "$version"
    local major="${VERSION_PARTS[0]}"
    local minor="${VERSION_PARTS[1]}"
    local patch="${VERSION_PARTS[2]}"

    case "$increment_type" in
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "patch")
            patch=$((patch + 1))
            ;;
        *)
            log_error "Invalid increment type: $increment_type"
            exit 1
            ;;
    esac

    echo "$major.$minor.$patch"
}

# Update version in manifest.json
update_manifest_version() {
    local new_version="$1"
    log_info "Updating manifest.json to version $new_version"

    # Use sed to replace the version
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed
        sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$new_version\"/" "$MANIFEST_FILE"
    else
        # Linux sed
        sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$new_version\"/" "$MANIFEST_FILE"
    fi
}

# Update version in pyproject.toml
update_pyproject_version() {
    local new_version="$1"
    log_info "Updating pyproject.toml to version $new_version"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed
        sed -i '' "s/version = \"[^\"]*\"/version = \"$new_version\"/" "$PYPROJECT_FILE"
    else
        # Linux sed
        sed -i "s/version = \"[^\"]*\"/version = \"$new_version\"/" "$PYPROJECT_FILE"
    fi
}

# Update version in test.js
update_testjs_version() {
    local new_version="$1"
    log_info "Updating test.js to version $new_version"

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS sed
        sed -i '' "s/Version [0-9.][0-9.]*/Version $new_version/" "$TESTJS_FILE"
    else
        # Linux sed
        sed -i "s/Version [0-9.][0-9.]*/Version $new_version/" "$TESTJS_FILE"
    fi
}

# Update all version files
update_all_versions() {
    local new_version="$1"

    update_manifest_version "$new_version"
    update_pyproject_version "$new_version"
    update_testjs_version "$new_version"

    log_success "All version files updated to $new_version"
}

# Main release process
main() {
    echo "🚀 Automated Release Script"
    echo "=========================="

    # Pre-flight checks
    check_git_repo
    check_working_directory

    # Check current version consistency
    log_info "Checking current version consistency..."
    check_version_consistency
    current_version=$(get_current_version)
    log_success "All versions are consistent: $current_version"    # Check if current version already exists as tag
    if check_remote_tag "$current_version"; then
        log_warning "Version $current_version already exists as remote tag!"

        echo ""
        echo "Options:"
        echo "1) Auto-increment patch version (recommended)"
        echo "2) Auto-increment minor version"
        echo "3) Auto-increment major version"
        echo "4) Manually specify new version"
        echo "5) Exit"

        read -p "Choose option (1-5): " choice

        case "$choice" in
            1)
                new_version=$(increment_version "$current_version" "patch")
                ;;
            2)
                new_version=$(increment_version "$current_version" "minor")
                ;;
            3)
                new_version=$(increment_version "$current_version" "major")
                ;;
            4)
                read -p "Enter new version (e.g., 1.2.3): " new_version
                # Basic validation
                if ! [[ "$new_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                    log_error "Invalid version format! Use semantic versioning (e.g., 1.2.3)"
                    exit 1
                fi
                ;;
            5)
                log_info "Release cancelled."
                exit 0
                ;;
            *)
                log_error "Invalid choice!"
                exit 1
                ;;
        esac

        # Check if new version already exists
        if check_remote_tag "$new_version"; then
            log_error "Version $new_version also already exists as remote tag!"
            exit 1
        fi

    else
        log_info "Current version $current_version is not yet tagged. Using it for release."
        new_version="$current_version"
    fi

    log_info "Releasing version: $new_version"

    # Confirmation
    echo ""
    read -p "Proceed with release $new_version? (y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        log_info "Release cancelled."
        exit 0
    fi

    # Update versions if needed
    if [[ "$new_version" != "$current_version" ]]; then
        log_info "Updating version files..."
        update_all_versions "$new_version"

        # Commit version changes
        git add "$MANIFEST_FILE" "$PYPROJECT_FILE" "$TESTJS_FILE"
        git commit -m "chore: bump version to $new_version"
        log_success "Version changes committed"

        # Push changes
        log_info "Pushing version changes to remote..."
        git push origin main
        log_success "Version changes pushed to remote"
    fi

    # Create and push tag
    local tag="v$new_version"
    log_info "Creating tag $tag..."
    git tag "$tag"
    log_success "Tag $tag created"

    log_info "Pushing tag to remote..."
    git push origin "$tag"
    log_success "Tag $tag pushed to remote"

    echo ""
    log_success "🎉 Release $new_version completed successfully!"
    log_info "The release workflow should now be triggered automatically."
    echo ""
}

# Show usage if help requested
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Automated Release Script for hass-voice-replay"
    echo ""
    echo "Usage: $0"
    echo ""
    echo "This script will:"
    echo "1. Check version consistency across all files"
    echo "2. Check if current version is already tagged"
    echo "3. Allow version increment if needed"
    echo "4. Update all version files"
    echo "5. Commit and push changes"
    echo "6. Create and push release tag"
    echo ""
    echo "Prerequisites:"
    echo "- Clean working directory (no uncommitted changes)"
    echo "- All version files must be consistent"
    echo ""
    exit 0
fi

# Run main function
main "$@"
