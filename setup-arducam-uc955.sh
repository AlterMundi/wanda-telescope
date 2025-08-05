#!/bin/bash
# Arducam UC-955 (Pivariety) Camera Setup Script for WANDA Telescope System
# 
# This script automates the installation of Arducam UC-955 drivers and configuration
# for use with the WANDA astrophotography system on Raspberry Pi 5.
#
# Official Arducam documentation:
# https://docs.arducam.com/Raspberry-Pi-Camera/Pivariety-Camera/Quick-Start-Guide/

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if running on Raspberry Pi
check_platform() {
    log "Checking platform compatibility..."
    
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        error "This script is designed for Raspberry Pi only"
        exit 1
    fi
    
    # Check for Pi 5 (recommended)
    if grep -q "Pi 5" /proc/cpuinfo; then
        success "Raspberry Pi 5 detected (recommended platform)"
    else
        warning "Raspberry Pi 5 recommended for optimal UC-955 performance"
    fi
    
    # Check OS version
    if ! grep -q "bookworm" /etc/os-release 2>/dev/null; then
        warning "Raspberry Pi OS Bookworm recommended for UC-955 support"
    fi
}

# Download Arducam installation script
download_installer() {
    log "Downloading Arducam Pivariety installation script..."
    
    if [ -f "install_pivariety_pkgs.sh" ]; then
        warning "Installation script already exists, removing old version"
        rm -f install_pivariety_pkgs.sh
    fi
    
    wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
    chmod +x install_pivariety_pkgs.sh
    
    success "Downloaded Arducam installation script"
}

# Install Arducam packages
install_packages() {
    log "Installing Arducam libcamera packages..."
    
    # Install libcamera development packages
    log "Installing libcamera_dev packages..."
    ./install_pivariety_pkgs.sh -p libcamera_dev
    
    # Install libcamera applications
    log "Installing libcamera_apps packages..."
    if ! ./install_pivariety_pkgs.sh -p libcamera_apps; then
        warning "libcamera_apps installation had warnings, attempting to fix dependencies..."
        sudo apt --fix-broken install -y
    fi
    
    success "Arducam packages installed"
}

# Configure device tree overlay
configure_overlay() {
    log "Configuring device tree overlay..."
    
    local config_file="/boot/firmware/config.txt"
    
    # Backup original config
    if [ ! -f "${config_file}.backup" ]; then
        sudo cp "$config_file" "${config_file}.backup"
        log "Created backup of config.txt"
    fi
    
    # Check if overlay already configured
    if grep -q "dtoverlay=arducam-pivariety" "$config_file"; then
        success "arducam-pivariety overlay already configured"
        return
    fi
    
    # Replace imx477 overlay if present
    if grep -q "dtoverlay=imx477" "$config_file"; then
        log "Replacing imx477 overlay with arducam-pivariety"
        sudo sed -i 's/dtoverlay=imx477/dtoverlay=arducam-pivariety/' "$config_file"
    else
        # Add overlay after camera_auto_detect=0
        if grep -q "camera_auto_detect=0" "$config_file"; then
            sudo sed -i '/camera_auto_detect=0/a dtoverlay=arducam-pivariety' "$config_file"
        else
            # Add at end of file
            echo "dtoverlay=arducam-pivariety" | sudo tee -a "$config_file" > /dev/null
        fi
    fi
    
    success "Device tree overlay configured"
}

# Install missing tuning file
install_tuning_file() {
    log "Installing libcamera tuning file..."
    
    local tuning_dir="/usr/share/libcamera/ipa/rpi/pisp"
    local source_file="$tuning_dir/arducam_64mp.json"
    local target_file="$tuning_dir/arducam-pivariety.json"
    
    if [ ! -f "$source_file" ]; then
        error "Source tuning file not found: $source_file"
        error "libcamera packages may not be properly installed"
        exit 1
    fi
    
    if [ -f "$target_file" ]; then
        success "Tuning file already exists"
        return
    fi
    
    sudo cp "$source_file" "$target_file"
    success "Tuning file installed: $target_file"
}

# Verify installation
verify_installation() {
    log "Verifying installation (requires reboot first)..."
    
    # Check if we've rebooted since overlay change
    if ! grep -q "arducam-pivariety" /proc/device-tree/chosen/overlays/*/name 2>/dev/null; then
        warning "Device tree overlay not loaded - reboot required"
        return 1
    fi
    
    # Test camera detection
    log "Testing camera detection..."
    if ! command -v rpicam-hello >/dev/null 2>&1; then
        error "rpicam-hello command not found"
        return 1
    fi
    
    # Try listing cameras
    local camera_output
    if camera_output=$(rpicam-hello --list-cameras 2>&1); then
        if echo "$camera_output" | grep -q "arducam-pivariety"; then
            success "Camera detected successfully!"
            echo "$camera_output" | grep -A2 "arducam-pivariety"
            return 0
        else
            error "Camera not detected in rpicam-hello output"
            echo "$camera_output"
            return 1
        fi
    else
        error "Failed to run rpicam-hello"
        echo "$camera_output"
        return 1
    fi
}

# Main installation function
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Arducam UC-955 Setup for WANDA       ${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
    echo "This script will install and configure the Arducam UC-955 (Pivariety)"
    echo "camera module for use with the WANDA telescope system."
    echo
    echo "Official documentation:"
    echo "https://docs.arducam.com/Raspberry-Pi-Camera/Pivariety-Camera/Quick-Start-Guide/"
    echo
    
    # Confirm installation
    read -p "Continue with installation? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Installation cancelled by user"
        exit 0
    fi
    
    # Run installation steps
    check_platform
    download_installer
    install_packages
    configure_overlay
    install_tuning_file
    
    echo
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Installation Complete!               ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo
    echo "Next steps:"
    echo "1. Reboot your Raspberry Pi: sudo reboot"
    echo "2. After reboot, test camera: rpicam-hello --list-cameras"
    echo "3. Test WANDA application: ./run-wanda.sh"
    echo
    echo "If you encounter issues, see: docs/ARDUCAM_UC955_SETUP.md"
    echo
    
    # Offer to reboot
    read -p "Reboot now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Rebooting system..."
        sudo reboot
    else
        warning "Remember to reboot before testing the camera!"
    fi
}

# Run main function
main "$@"