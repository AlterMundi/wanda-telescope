#!/bin/bash

# WANDA Telescope Development Deployment Script
# This script sets up the auto-initialization system on a fresh Raspberry Pi
# Usage: curl -sSL https://raw.githubusercontent.com/AlterMundi/wanda-telescope/feat/auto-initialization/scripts/deploy-to-pi.sh | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
BRANCH="feat/auto-initialization"
REPO_URL="https://github.com/AlterMundi/wanda-telescope.git"
PROJECT_DIR="$HOME/repos/wanda-telescope"
USER=$(whoami)

print_banner() {
    echo
    print_info "🔭 WANDA Telescope Development Deployment"
    print_info "=========================================="
    print_info "Branch: $BRANCH"
    print_info "Target: $PROJECT_DIR"
    print_info "User: $USER"
    echo
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if we're on a Raspberry Pi
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        local pi_model=$(cat /proc/device-tree/model)
        print_success "Detected: $pi_model"
    else
        print_warning "Not running on Raspberry Pi - will use mock implementations"
    fi
    
    # Check for required tools
    for tool in git python3 curl; do
        if ! command -v $tool >/dev/null 2>&1; then
            print_error "$tool is not installed"
            exit 1
        fi
    done
    
    print_success "Prerequisites check completed"
}

setup_directories() {
    print_info "Setting up directories..."
    
    # Create repos directory
    mkdir -p "$(dirname "$PROJECT_DIR")"
    
    print_success "Directories created"
}

clone_or_update_repository() {
    print_info "Setting up repository..."
    
    if [ -d "$PROJECT_DIR" ]; then
        print_info "Repository exists, updating..."
        cd "$PROJECT_DIR"
        
        # Fetch latest changes
        git fetch origin
        
        # Switch to development branch
        if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
            git checkout "$BRANCH"
            git pull origin "$BRANCH"
        else
            git checkout -b "$BRANCH" "origin/$BRANCH"
        fi
        
        print_success "Repository updated to latest $BRANCH"
    else
        print_info "Cloning repository..."
        git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
        print_success "Repository cloned"
    fi
}

setup_environment() {
    print_info "Setting up Python environment..."
    cd "$PROJECT_DIR"
    
    # Run the setup script
    if [ -f "run-wanda.sh" ]; then
        print_info "Running WANDA setup script..."
        timeout 300 ./run-wanda.sh --setup-only || {
            print_warning "Setup script timed out or failed, continuing..."
        }
    else
        print_error "run-wanda.sh not found"
        exit 1
    fi
    
    print_success "Environment setup completed"
}

install_auto_startup() {
    print_info "Installing auto-startup service..."
    cd "$PROJECT_DIR"
    
    if [ -f "scripts/install-service.sh" ]; then
        sudo ./scripts/install-service.sh
        print_success "Auto-startup service installed"
    else
        print_error "install-service.sh not found"
        exit 1
    fi
}

test_installation() {
    print_info "Testing installation..."
    
    # Check if service is enabled
    if sudo systemctl is-enabled wanda-telescope >/dev/null 2>&1; then
        print_success "Service is enabled for auto-start"
    else
        print_error "Service is not enabled"
        exit 1
    fi
    
    # Start service for testing
    print_info "Starting WANDA service..."
    sudo systemctl start wanda-telescope
    
    # Wait a moment for startup
    sleep 10
    
    # Check if service is running
    if sudo systemctl is-active wanda-telescope >/dev/null 2>&1; then
        print_success "Service is running"
        
        # Get IP and show access info
        local ip_address=$(hostname -I | awk '{print $1}')
        if [ -n "$ip_address" ]; then
            print_success "WANDA is accessible at: http://$ip_address:5000"
        fi
    else
        print_error "Service failed to start"
        sudo systemctl status wanda-telescope --no-pager
        exit 1
    fi
}

show_completion_info() {
    echo
    print_success "🎉 WANDA Development Deployment Complete!"
    echo
    print_info "Next Steps:"
    print_info "  1. Reboot the Pi to test auto-startup: sudo reboot"
    print_info "  2. Find the Pi's IP using discovery script on your computer:"
    print_info "     python3 scripts/find-wanda.py"
    print_info "  3. Access WANDA web interface at: http://[PI_IP]:5000"
    echo
    print_info "Service Management:"
    print_info "  • Check status: sudo systemctl status wanda-telescope"
    print_info "  • View logs: sudo journalctl -u wanda-telescope -f"
    print_info "  • Stop service: sudo systemctl stop wanda-telescope"
    print_info "  • Start manually: ./run-wanda.sh"
    echo
    print_info "Development Workflow:"
    print_info "  • Pull latest changes: git pull origin $BRANCH"
    print_info "  • Test changes: sudo systemctl restart wanda-telescope"
    print_info "  • Uninstall service: sudo ./scripts/uninstall-service.sh"
    echo
}

# Main deployment process
main() {
    print_banner
    check_prerequisites
    setup_directories
    clone_or_update_repository
    setup_environment
    install_auto_startup
    test_installation
    show_completion_info
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run this script as root. Run as the user that will operate WANDA."
    exit 1
fi

# Run main deployment
main "$@"