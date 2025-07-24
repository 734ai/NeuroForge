#!/bin/bash
# NeuroForge Release Automation Script
# Author: Muzan Sano

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXTENSION_DIR="$PROJECT_ROOT/extension"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git is required but not installed"
        exit 1
    fi
    
    # Check vsce
    if ! command -v vsce &> /dev/null && ! npx vsce --version &> /dev/null; then
        log_error "vsce is required for packaging extensions"
        exit 1
    fi
    
    log_success "All dependencies are available"
}

check_git_status() {
    log_info "Checking git status..."
    
    if [ -n "$(git status --porcelain)" ]; then
        log_error "Working directory is not clean. Please commit or stash changes."
        git status --short
        exit 1
    fi
    
    # Check if we're on main branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "main" ]; then
        log_warning "Not on main branch (current: $current_branch)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "Git status is clean"
}

run_tests() {
    log_info "Running test suite..."
    
    cd "$PROJECT_ROOT"
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Run Python tests
    log_info "Running Python core tests..."
    python test_core.py
    
    log_info "Running Python LLM tests..."
    python test_llm.py
    
    # Test extension compilation
    log_info "Testing extension compilation..."
    cd "$EXTENSION_DIR"
    npm run compile
    
    log_success "All tests passed"
}

bump_version() {
    local version_type=$1
    
    log_info "Bumping version ($version_type)..."
    
    cd "$EXTENSION_DIR"
    
    # Get current version from package.json
    current_version=$(node -p "require('./package.json').version")
    log_info "Current version: $current_version"
    
    # Use npm version to bump
    npm version "$version_type" --no-git-tag-version
    
    new_version=$(node -p "require('./package.json').version")
    log_success "New version: $new_version"
    
    echo "$new_version"
}

build_extension() {
    log_info "Building extension..."
    
    cd "$EXTENSION_DIR"
    
    # Clean previous builds
    rm -f *.vsix
    
    # Install dependencies
    npm ci
    
    # Compile TypeScript
    npm run compile
    
    # Package extension
    npx vsce package
    
    log_success "Extension built successfully"
}

create_release_commit() {
    local version=$1
    
    log_info "Creating release commit..."
    
    cd "$PROJECT_ROOT"
    
    # Add all changes
    git add .
    
    # Commit changes
    git commit -m "🚀 Release v$version

- Updated extension to v$version
- All tests passing
- Ready for deployment"
    
    # Create git tag
    git tag "v$version"
    
    log_success "Release commit and tag created"
}

push_release() {
    local version=$1
    
    log_info "Pushing release to remote..."
    
    cd "$PROJECT_ROOT"
    
    # Push commit and tag
    git push origin main
    git push origin "v$version"
    
    log_success "Release pushed to remote repository"
}

update_todo() {
    local version=$1
    
    log_info "Updating project documentation..."
    
    cd "$PROJECT_ROOT"
    
    # Update todo.md with completion status
    sed -i "s/\[ \] CI\/CD pipeline setup/[x] CI\/CD pipeline setup/" todo.md
    sed -i "s/\[ \] Release automation/[x] Release automation/" todo.md
    sed -i "s/Last Updated: [0-9-]*/Last Updated: $(date +%Y-%m-%d)/" todo.md
    
    log_success "Documentation updated"
}

show_summary() {
    local version=$1
    
    log_success "🎉 Release v$version completed successfully!"
    echo
    log_info "Summary:"
    echo "  ✅ Tests passed"
    echo "  ✅ Version bumped to $version"
    echo "  ✅ Extension packaged"
    echo "  ✅ Git tag created"
    echo "  ✅ Changes pushed to remote"
    echo
    log_info "Next steps:"
    echo "  1. GitHub Actions will automatically build and test"
    echo "  2. Create a GitHub release from the tag"
    echo "  3. Upload the .vsix file to the release"
    echo "  4. Publish to VS Code Marketplace (if configured)"
    echo
    log_info "Extension file: $EXTENSION_DIR/neuroforge-$version.vsix"
}

# Main execution
main() {
    local version_type=${1:-patch}
    
    echo "🚀 NeuroForge Release Automation"
    echo "=================================="
    echo
    
    # Validate input
    if [[ ! "$version_type" =~ ^(major|minor|patch)$ ]]; then
        log_error "Invalid version type: $version_type"
        echo "Usage: $0 [major|minor|patch]"
        exit 1
    fi
    
    # Run all steps
    check_dependencies
    check_git_status
    run_tests
    
    # Get confirmation before proceeding
    read -p "Ready to create $version_type release. Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Release cancelled"
        exit 0
    fi
    
    new_version=$(bump_version "$version_type")
    update_todo "$new_version"
    build_extension
    create_release_commit "$new_version"
    push_release "$new_version"
    show_summary "$new_version"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
