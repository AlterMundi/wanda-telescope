#!/bin/bash

# WANDA Telescope Service Uninstallation Script
# This script removes the WANDA telescope service from the system

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
SYSTEMD_DIR="/etc/systemd/system"

# Check if running as root
check_permissions() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root for service removal"
        print_info "Please run: sudo bash scripts/uninstall-service.sh"
        exit 1
    fi
}

# Uninstall service
uninstall_service() {
    print_info "Removing WANDA Telescope service..."
    
    # Stop service if running
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_info "Stopping service..."
        systemctl stop "$SERVICE_NAME"
        print_success "Service stopped"
    fi
    
    # Disable service
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        print_info "Disabling service..."
        systemctl disable "$SERVICE_NAME"
        print_success "Service disabled"
    fi
    
    # Remove service file
    if [ -f "$SYSTEMD_DIR/$SERVICE_NAME.service" ]; then
        rm -f "$SYSTEMD_DIR/$SERVICE_NAME.service"
        print_success "Service file removed"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    print_success "Systemd daemon reloaded"
}

# Clean up logs and files
cleanup() {
    print_info "Cleaning up service files..."
    
    # Remove log file (optional)
    read -p "Remove log file (/var/log/wanda-telescope.log)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f /var/log/wanda-telescope.log
        print_success "Log file removed"
    fi
    
    # Remove lock file
    rm -f /tmp/wanda-telescope.lock
    
    print_success "Cleanup completed"
}

# Main uninstallation
main() {
    echo
    print_info "=== WANDA Telescope Service Uninstallation ==="
    echo
    
    check_permissions
    uninstall_service
    cleanup
    
    echo
    print_success "=== Uninstallation Completed Successfully ==="
    echo
    print_info "The WANDA telescope service has been removed from the system."
    print_info "The application can still be run manually using './run-wanda.sh'"
    echo
}

# Run main function
main "$@"