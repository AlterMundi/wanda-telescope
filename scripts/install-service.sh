#!/bin/bash

# WANDA Telescope Service Installation Script
# This script installs and configures the WANDA telescope service for automatic startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Print functions
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
SERVICE_NAME="wanda-telescope"
PROJECT_DIR="/home/astro2/repos/wanda-telescope"
SERVICE_FILE="$PROJECT_DIR/wanda-telescope.service"
SYSTEMD_DIR="/etc/systemd/system"
USER="astro2"

# Check if running as root for service installation
check_permissions() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root for service installation"
        print_info "Please run: sudo bash scripts/install-service.sh"
        exit 1
    fi
}

# Validate environment
validate_environment() {
    print_info "Validating environment..."
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    # Check if service file exists
    if [ ! -f "$SERVICE_FILE" ]; then
        print_error "Service file not found: $SERVICE_FILE"
        exit 1
    fi
    
    # Check if startup script exists
    if [ ! -f "$PROJECT_DIR/scripts/wanda-service.sh" ]; then
        print_error "Startup script not found: $PROJECT_DIR/scripts/wanda-service.sh"
        exit 1
    fi
    
    # Check if user exists
    if ! id "$USER" &>/dev/null; then
        print_error "User '$USER' does not exist"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        print_warning "Virtual environment not found. Please run './run-wanda.sh' first to set up the environment."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success "Environment validation completed"
}

# Install service
install_service() {
    print_info "Installing systemd service..."
    
    # Stop existing service if running
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_info "Stopping existing service..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # Copy service file
    cp "$SERVICE_FILE" "$SYSTEMD_DIR/"
    print_success "Service file copied to $SYSTEMD_DIR/"
    
    # Set proper permissions
    chmod 644 "$SYSTEMD_DIR/$SERVICE_NAME.service"
    
    # Reload systemd
    systemctl daemon-reload
    print_success "Systemd daemon reloaded"
}

# Configure service
configure_service() {
    print_info "Configuring service..."
    
    # Enable service for auto-start
    systemctl enable "$SERVICE_NAME"
    print_success "Service enabled for automatic startup"
    
    # Create log directory
    mkdir -p /var/log
    touch /var/log/wanda-telescope.log
    chown "$USER:$USER" /var/log/wanda-telescope.log
    print_success "Log file created and configured"
    
    # Add user to required groups
    usermod -a -G video,gpio "$USER" 2>/dev/null || print_warning "Could not add user to video/gpio groups"
    
    print_success "Service configuration completed"
}

# Test service
test_service() {
    print_info "Testing service configuration..."
    
    # Validate service file
    if systemctl cat "$SERVICE_NAME" >/dev/null 2>&1; then
        print_success "Service file is valid"
    else
        print_error "Service file validation failed"
        return 1
    fi
    
    # Check if service is enabled
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        print_success "Service is enabled for auto-start"
    else
        print_warning "Service is not enabled for auto-start"
    fi
    
    print_success "Service test completed"
}

# Main installation
main() {
    echo
    print_info "=== WANDA Telescope Service Installation ==="
    echo
    
    check_permissions
    validate_environment
    install_service
    configure_service
    test_service
    
    echo
    print_success "=== Installation Completed Successfully ==="
    echo
    print_info "Service Management Commands:"
    print_info "  • Start service:    sudo systemctl start $SERVICE_NAME"
    print_info "  • Stop service:     sudo systemctl stop $SERVICE_NAME"
    print_info "  • Restart service:  sudo systemctl restart $SERVICE_NAME"
    print_info "  • Check status:     sudo systemctl status $SERVICE_NAME"
    print_info "  • View logs:        sudo journalctl -u $SERVICE_NAME -f"
    print_info "  • Disable auto-start: sudo systemctl disable $SERVICE_NAME"
    echo
    print_info "The service will automatically start on boot."
    print_info "To start it now, run: sudo systemctl start $SERVICE_NAME"
    echo
}

# Run main function
main "$@"