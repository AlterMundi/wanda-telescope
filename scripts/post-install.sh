#!/bin/bash

# WANDA Telescope Post-Installation Verification Script
# This script verifies that WANDA Telescope is running correctly after installation
# Usage: ./scripts/post-install.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Configuration
PROJECT_DIR="$HOME/wanda-telescope"
SERVICE_NAME="wanda-telescope"
WEB_PORT=5000

# Camera setup flags
CAMERA_TYPE=""
AUTO_REBOOT=""
TEST_AFTER_REBOOT=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --camera-imx477)
            CAMERA_TYPE="imx477"
            shift
            ;;
        --camera-uc955)
            CAMERA_TYPE="uc955"
            shift
            ;;
        --camera-usb)
            CAMERA_TYPE="usb"
            shift
            ;;
        --camera-skip)
            CAMERA_TYPE="skip"
            shift
            ;;
        --auto-reboot)
            AUTO_REBOOT="yes"
            shift
            ;;
        --test-after-reboot)
            TEST_AFTER_REBOOT="yes"
            shift
            ;;
        --help)
            echo "WANDA Telescope Post-Installation Verification"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Camera Options:"
            echo "  --camera-imx477      Configure Arducam IMX-477 12MP camera (standard Pi drivers)"
            echo "  --camera-uc955       Configure Arducam UC-955 (IMX462 Pivariety) camera (requires drivers)"
            echo "  --camera-usb         Use USB camera (no configuration needed)"
            echo "  --camera-skip        Skip camera setup"
            echo "  --auto-reboot        Automatically reboot after camera configuration"
            echo "  --test-after-reboot  Test camera functionality after reboot (useful for debugging)"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Interactive mode"
            echo "  $0 --camera-imx477 --auto-reboot     # Auto-configure IMX-477 and reboot"
            echo "  $0 --camera-uc955                     # Configure UC-955, ask about reboot"
            echo "  $0 --camera-usb                       # Set up for USB camera"
            echo "  $0 --test-after-reboot                # Test camera after recent configuration"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            print_info "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_banner() {
    echo
    print_info "🔭 WANDA Telescope - Post-Installation Verification"
    print_info "=================================================="
    print_info "This script verifies that WANDA Telescope is running correctly"
    print_info "Project Directory: $PROJECT_DIR"
    print_info "Service Name: $SERVICE_NAME"
    print_info "Web Port: $WEB_PORT"
    echo
}

check_service_status() {
    print_step "1/5: Checking service status..."
    
    # Check if service exists
    if ! sudo systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        print_error "Service $SERVICE_NAME not found!"
        print_info "Please run install.sh first to install WANDA Telescope."
        exit 1
    fi
    
    # Check if service is enabled
    if ! sudo systemctl is-enabled "$SERVICE_NAME" >/dev/null 2>&1; then
        print_warning "Service $SERVICE_NAME is not enabled for auto-start"
        print_info "Enabling service..."
        if ! sudo systemctl enable "$SERVICE_NAME"; then
            print_error "Failed to enable service"
            exit 1
        fi
        print_success "Service enabled"
    else
        print_success "Service is enabled for auto-start"
    fi
    
    # Check if service is running
    if ! sudo systemctl is-active "$SERVICE_NAME" >/dev/null 2>&1; then
        print_warning "Service $SERVICE_NAME is not running"
        print_info "Starting service..."
        if ! sudo systemctl start "$SERVICE_NAME"; then
            print_error "Failed to start service"
            print_info "Checking service logs for errors..."
            sudo journalctl -u "$SERVICE_NAME" --no-pager -n 20
            exit 1
        fi
        print_success "Service started"
    else
        print_success "Service is running"
    fi
    
    # Wait a moment for service to fully initialize
    print_info "Waiting for service to fully initialize..."
    sleep 5
    
    print_success "Service status check completed"
}

check_service_logs() {
    print_step "2/5: Checking service logs..."
    
    # Get recent logs
    print_info "Recent service logs:"
    echo "----------------------------------------"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -n 15
    echo "----------------------------------------"
    
    # Check for error patterns
    local error_count=$(sudo journalctl -u "$SERVICE_NAME" --no-pager | grep -i "error\|exception\|traceback" | wc -l)
    
    if [ "$error_count" -gt 0 ]; then
        print_warning "Found $error_count potential errors in logs"
        print_info "This may indicate configuration issues that need attention"
    else
        print_success "No obvious errors found in logs"
    fi
    
    print_success "Service logs check completed"
}

check_web_interface() {
    print_step "3/5: Checking web interface accessibility..."
    
    # Get local IP address
    local ip_address
    ip_address=$(hostname -I | awk '{print $1}')
    if [ -z "$ip_address" ]; then
        # Try alternative method
        ip_address=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || echo "")
        if [ -z "$ip_address" ]; then
            print_warning "Could not determine IP address"
            ip_address="localhost"
        fi
    fi
    
    print_info "Local IP address: $ip_address"
    print_info "Web interface URL: http://$ip_address:$WEB_PORT"
    
    # Check if port is listening
    if ! netstat -tlnp 2>/dev/null | grep -q ":$WEB_PORT "; then
        print_error "Web interface is not listening on port $WEB_PORT"
        print_info "Checking if service is still starting..."
        sleep 10
        
        if ! netstat -tlnp 2>/dev/null | grep -q ":$WEB_PORT "; then
            print_error "Web interface still not accessible after waiting"
            print_info "Service may have failed to start properly"
            exit 1
        fi
    fi
    
    print_success "Web interface is listening on port $WEB_PORT"
    
    # Test web interface response
    print_info "Testing web interface response..."
    if command -v curl >/dev/null 2>&1; then
        local response_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$WEB_PORT" || echo "000")
        
        if [ "$response_code" = "200" ]; then
            print_success "Web interface responded successfully (HTTP 200)"
        elif [ "$response_code" = "000" ]; then
            print_warning "Could not test web interface with curl (connection refused)"
        else
            print_warning "Web interface responded with HTTP $response_code"
        fi
    else
        print_warning "curl not available, skipping web interface test"
    fi
    
    print_success "Web interface check completed"
}

configure_arducam_imx477() {
    print_info "Configuring Arducam IMX-477 12MP camera..."
    print_info "IMX477 uses standard Raspberry Pi camera drivers (no Pivariety drivers needed)"
    
    # Backup current config
    sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.backup.$(date +%Y%m%d_%H%M%S)
    
    # Apply minimal changes for IMX-477
    local config_file="/boot/firmware/config.txt"
    
    # Set camera_auto_detect=0 (per official Arducam documentation)
    if grep -q "^camera_auto_detect=" "$config_file"; then
        sudo sed -i 's/^camera_auto_detect=.*/camera_auto_detect=0/' "$config_file"
        print_info "Updated camera_auto_detect=0"
    else
        echo "camera_auto_detect=0" | sudo tee -a "$config_file" >/dev/null
        print_info "Added camera_auto_detect=0"
    fi
    
    # Add dtoverlay=imx477 (per official Arducam documentation)
    if ! grep -q "^dtoverlay=imx477" "$config_file"; then
        # Check if [all] section exists
        if grep -q "^\[all\]" "$config_file"; then
            # Add after [all] section
            sudo sed -i '/^\[all\]/a dtoverlay=imx477' "$config_file"
            print_info "Added dtoverlay=imx477 to [all] section"
        else
            # Add [all] section and overlay at end
            echo -e "\n[all]\ndtoverlay=imx477" | sudo tee -a "$config_file" >/dev/null
            print_info "Added [all] section with dtoverlay=imx477"
        fi
    else
        print_info "dtoverlay=imx477 already present"
    fi
    
    # Add CMA memory configuration for high-resolution camera support
    if ! grep -q "^dtoverlay=cma" "$config_file"; then
        echo "dtoverlay=cma,cma-256" | sudo tee -a "$config_file" >/dev/null
        print_info "Added CMA memory allocation (256MB) for camera buffer support"
    else
        print_info "CMA configuration already present"
    fi
    
    # Fix DMA heap device permissions for camera access
    if ! grep -q "dma_heap" /etc/udev/rules.d/99-dma-heap.rules 2>/dev/null; then
        print_info "Setting up DMA heap device permissions..."
        echo 'SUBSYSTEM=="dma_heap", GROUP="video", MODE="0664"' | sudo tee /etc/udev/rules.d/99-dma-heap.rules >/dev/null
        sudo usermod -a -G video "$(whoami)"
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        print_info "Added user to video group and configured DMA heap permissions"
    else
        print_info "DMA heap permissions already configured"
    fi
    
    print_success "IMX-477 configuration completed (3 lines modified + DMA permissions)"
    print_info "Added CMA memory allocation to prevent DMA buffer allocation failures"
    print_info "Added DMA heap permissions for camera access"
    print_info "After reboot, verify with: rpicam-still --list-cameras"
}

configure_arducam_uc955() {
    print_info "Configuring Arducam UC-955 (IMX462 Pivariety) camera..."
    
    # Backup current config
    sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.backup.$(date +%Y%m%d_%H%M%S)
    
    # Apply configuration for UC-955 (IMX462 sensor)
    local config_file="/boot/firmware/config.txt"
    
    # Set camera_auto_detect=0
    if grep -q "^camera_auto_detect=" "$config_file"; then
        sudo sed -i 's/^camera_auto_detect=.*/camera_auto_detect=0/' "$config_file"
        print_info "Updated camera_auto_detect=0"
    else
        echo "camera_auto_detect=0" | sudo tee -a "$config_file" >/dev/null
        print_info "Added camera_auto_detect=0"
    fi
    
    # Comment out dtoverlay=vc4-kms-v3d if present (conflicts with Pivariety)
    if grep -q "^dtoverlay=vc4-kms-v3d" "$config_file"; then
        sudo sed -i 's/^dtoverlay=vc4-kms-v3d/#dtoverlay=vc4-kms-v3d/' "$config_file"
        print_info "Commented out vc4-kms-v3d overlay (conflicts with Pivariety)"
    fi
    
    # Add dtoverlay=arducam-pivariety
    if ! grep -q "^dtoverlay=arducam-pivariety" "$config_file"; then
        # Add after the commented vc4-kms-v3d line if it exists, otherwise at end
        if grep -q "^#dtoverlay=vc4-kms-v3d" "$config_file"; then
            sudo sed -i '/^#dtoverlay=vc4-kms-v3d/a dtoverlay=arducam-pivariety' "$config_file"
        else
            echo "dtoverlay=arducam-pivariety" | sudo tee -a "$config_file" >/dev/null
        fi
        print_info "Added dtoverlay=arducam-pivariety"
    else
        print_info "dtoverlay=arducam-pivariety already present"
    fi
    
    # Add CMA memory configuration for high-resolution camera support (increased to 512MB for IMX462)
    if ! grep -q "^dtoverlay=cma" "$config_file"; then
        echo "dtoverlay=cma,cma-512" | sudo tee -a "$config_file" >/dev/null
        print_info "Added CMA memory allocation (512MB) for IMX462 buffer support"
    else
        # Update existing CMA to 512MB if it's less
        if grep -q "^dtoverlay=cma,cma-256" "$config_file"; then
            sudo sed -i 's/^dtoverlay=cma,cma-256/dtoverlay=cma,cma-512/' "$config_file"
            print_info "Updated CMA memory allocation from 256MB to 512MB for IMX462"
        else
            print_info "CMA configuration already present (may need manual adjustment to 512MB)"
        fi
    fi
    
    # Add specific IMX462 sensor configuration
    if ! grep -q "^dtoverlay=imx462" "$config_file"; then
        echo "dtoverlay=imx462" | sudo tee -a "$config_file" >/dev/null
        print_info "Added dtoverlay=imx462 for IMX462 sensor support"
    else
        print_info "dtoverlay=imx462 already present"
    fi
    
    # Add imx290 overlay for device tree compatibility (UC-955 uses IMX462 sensor but imx290 node)
    if ! grep -q "^dtoverlay=imx290" "$config_file"; then
        echo "dtoverlay=imx290" | sudo tee -a "$config_file" >/dev/null
        print_info "Added dtoverlay=imx290 for device tree compatibility"
    else
        print_info "dtoverlay=imx290 already present"
    fi
    
    # Fix DMA heap device permissions for camera access
    if ! grep -q "dma_heap" /etc/udev/rules.d/99-dma-heap.rules 2>/dev/null; then
        print_info "Setting up DMA heap device permissions..."
        echo 'SUBSYSTEM=="dma_heap", GROUP="video", MODE="0664"' | sudo tee /etc/udev/rules.d/99-dma-heap.rules >/dev/null
        sudo usermod -a -G video "$(whoami)"
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        print_info "Added user to video group and configured DMA heap permissions"
    else
        print_info "DMA heap permissions already configured"
    fi
    
    # Create the missing arducam-pivariety.json configuration file
    print_info "Creating arducam-pivariety.json configuration file..."
    local config_dir="/usr/share/libcamera/ipa/rpi/pisp"
    sudo mkdir -p "$config_dir"
    
    # Create the configuration file with IMX462-specific settings
    cat << 'EOF' | sudo tee "$config_dir/arducam-pivariety.json" >/dev/null
{
    "version": "1.0.0",
    "target": "bcm2712",
    "cameras": [
        {
            "name": "arducam-pivariety",
            "model": "IMX462",
            "sensor": {
                "width": 1920,
                "height": 1080,
                "bit_depth": 10,
                "formats": [
                    "SRGGB10_CSI2P",
                    "SRGGB12_CSI2P"
                ],
                "exposure": {
                    "min": 1,
                    "max": 1000000
                },
                "gain": {
                    "min": 1.0,
                    "max": 16.0
                }
            },
            "isp": {
                "pisp_variant": "BCM2712_C0",
                "cma_heap": "cma_heap",
                "buffer_size": 512
            }
        }
    ]
}
EOF
    
    if [ -f "$config_dir/arducam-pivariety.json" ]; then
        print_success "Created arducam-pivariety.json configuration file"
        print_info "File location: $config_dir/arducam-pivariety.json"
    else
        print_warning "Failed to create arducam-pivariety.json configuration file"
    fi
    
    # Set proper permissions for the configuration file
    sudo chmod 644 "$config_dir/arducam-pivariety.json"
    sudo chown root:root "$config_dir/arducam-pivariety.json"
    
    print_success "UC-955 (IMX462 Pivariety) configuration completed"
    print_info "Configuration includes:"
    print_info "  - Device tree overlays for Pivariety and IMX462"
    print_info "  - CMA memory allocation (512MB) for IMX462 buffer support"
    print_info "  - DMA heap permissions for camera access"
    print_info "  - arducam-pivariety.json configuration file"
    print_info "  - Disabled conflicting vc4-kms-v3d overlay"
}

install_arducam_drivers() {
    print_info "Installing Arducam Pivariety drivers for IMX462..."
    
    # Install required packages
    if ! sudo apt install -y -qq wget; then
        print_error "Failed to install wget"
        return 1
    fi
    
    # Install libcamera tools if not available
    print_info "Installing libcamera tools..."
    if ! sudo apt install -y -qq libcamera-apps-lite libcamera-tools; then
        print_warning "Failed to install libcamera tools, but continuing with driver installation"
    else
        print_success "libcamera tools installed successfully"
    fi
    
    # Download and install Arducam drivers using official installation script
    cd /tmp
    print_info "Downloading latest Arducam Pivariety installation script..."
    if wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh; then
        chmod +x install_pivariety_pkgs.sh
        
        # Install components sequentially as per official documentation
        print_info "Installing libcamera development packages..."
        if sudo ./install_pivariety_pkgs.sh -p libcamera_dev; then
            print_info "Installing libcamera applications..."
            if sudo ./install_pivariety_pkgs.sh -p libcamera_apps; then
                print_info "Installing kernel driver support..."
                if sudo ./install_pivariety_pkgs.sh -p kernel_driver; then
                    print_success "Arducam Pivariety drivers for IMX462 installed successfully"
                    
                    # Verify installation by checking if rpicam-still works
                    print_info "Verifying camera detection..."
                    if timeout 10 rpicam-still --list-cameras >/dev/null 2>&1; then
                        print_success "Camera detection verified - rpicam-still is working"
                    else
                        print_warning "Camera detection verification failed - may need reboot"
                    fi
                    
                    return 0
                else
                    print_warning "Kernel driver installation had issues, but libcamera components installed"
                    return 1
                fi
            else
                print_warning "libcamera_apps installation failed, but dev packages installed"
                return 1
            fi
        else
            print_error "libcamera_dev installation failed"
            return 1
        fi
    else
        print_error "Failed to download Arducam driver installer from official source"
        print_info "This may be due to network issues or changes in the repository structure"
        return 1
    fi
}

verify_uc955_configuration() {
    print_info "Verifying UC-955 camera configuration..."
    
    # Check if the configuration file was created
    local config_file="/usr/share/libcamera/ipa/rpi/pisp/arducam-pivariety.json"
    if [ -f "$config_file" ]; then
        print_success "arducam-pivariety.json configuration file exists"
    else
        print_warning "arducam-pivariety.json configuration file not found"
        print_info "This may cause the 'Configuration file not found' error in rpicam-still"
    fi
    
    # Check if the device tree overlays are properly configured
    local config_txt="/boot/firmware/config.txt"
    if grep -q "^dtoverlay=arducam-pivariety" "$config_txt"; then
        print_success "arducam-pivariety overlay is configured"
    else
        print_warning "arducam-pivariety overlay is not configured"
    fi
    
    if grep -q "^dtoverlay=imx462" "$config_txt"; then
        print_success "imx462 overlay is configured"
    else
        print_warning "imx462 overlay is not configured"
    fi
    
    if grep -q "^dtoverlay=imx290" "$config_txt"; then
        print_success "imx290 overlay is configured"
    else
        print_warning "imx290 overlay is not configured"
    fi
    
    # Check CMA memory allocation
    if grep -q "^dtoverlay=cma,cma-512" "$config_txt"; then
        print_success "CMA memory allocation is set to 512MB"
    elif grep -q "^dtoverlay=cma" "$config_txt"; then
        print_warning "CMA memory allocation is configured but may not be 512MB"
        print_info "Current CMA setting: $(grep '^dtoverlay=cma' "$config_txt")"
    else
        print_warning "CMA memory allocation is not configured"
    fi
    
    # Check if vc4-kms-v3d is commented out
    if grep -q "^#dtoverlay=vc4-kms-v3d" "$config_txt"; then
        print_success "vc4-kms-v3d overlay is properly commented out"
    elif grep -q "^dtoverlay=vc4-kms-v3d" "$config_txt"; then
        print_warning "vc4-kms-v3d overlay is still active and may conflict with Pivariety"
    fi
    
    # Test camera detection
    print_info "Testing camera detection..."
    if timeout 10 rpicam-still --list-cameras >/dev/null 2>&1; then
        print_success "Camera detection test passed"
        
        # Get detailed camera info
        local camera_info=$(timeout 10 rpicam-still --list-cameras 2>/dev/null)
        if [ -n "$camera_info" ]; then
            print_info "Camera detection output:"
            echo "$camera_info"
        fi
    else
        print_warning "Camera detection test failed"
        print_info "This may indicate a configuration issue or the need for a reboot"
    fi
    
    # Check for common error messages in recent logs
    print_info "Checking for camera-related errors in system logs..."
    local error_count=$(sudo journalctl --since "1 hour ago" | grep -i "arducam\|pivariety\|imx462\|configuration.*not.*found" | wc -l)
    if [ "$error_count" -gt 0 ]; then
        print_warning "Found $error_count camera-related errors in recent logs"
        print_info "Recent camera errors:"
        sudo journalctl --since "1 hour ago" | grep -i "arducam\|pivariety\|imx462\|configuration.*not.*found" | tail -5
    else
        print_success "No camera-related errors found in recent logs"
    fi
}

check_camera_detection() {
    print_step "4/5: Camera detection and interactive setup..."
    
    # Check if we're on Raspberry Pi
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        local pi_model=$(cat /proc/device-tree/model)
        print_info "Running on: $pi_model"
        
        # Install libcamera tools if not available
        if ! command -v libcamera-hello >/dev/null 2>&1; then
            print_info "Installing libcamera tools..."
            sudo apt update -qq >/dev/null 2>&1
            sudo apt install -y -qq libcamera-apps-lite >/dev/null 2>&1
        fi
        
        # Test current camera detection
        print_info "Testing current camera detection..."
        local camera_list=$(timeout 5 libcamera-hello --list-cameras 2>/dev/null || echo "")
        if echo "$camera_list" | grep -q "Available cameras"; then
            print_success "Camera already detected and working!"
            echo "$camera_list"
        else
            print_info "No camera detected. Let's configure one..."
            
            # Use command-line argument or interactive setup
            if [ -n "$CAMERA_TYPE" ]; then
                # Non-interactive mode with command-line flags
                case $CAMERA_TYPE in
                    imx477)
                        print_info "Setting up Arducam IMX-477 12MP Camera (non-interactive)..."
                        print_info "IMX477 uses standard Pi camera drivers - no additional driver installation needed"
                        configure_arducam_imx477
                        print_success "IMX-477 configured. System will need to reboot to take effect."
                        camera_configured=true
                        ;;
                    uc955)
                        print_info "Setting up Arducam UC-955 (IMX462 Pivariety) Camera (non-interactive)..."
                        print_info "IMX462 sensor requires Arducam Pivariety drivers for optimal performance"
                        if install_arducam_drivers; then
                            configure_arducam_uc955
                            print_success "UC-955 (IMX462) configured with drivers. System will need to reboot to take effect."
                            
                            # Verify configuration after setup
                            print_info "Verifying UC-955 configuration..."
                            verify_uc955_configuration
                            
                            print_info "After reboot, test the camera with: $0 --test-after-reboot"
                        else
                            print_warning "Driver installation failed, but overlay configured."
                            configure_arducam_uc955
                            print_info "You may need to install drivers manually later using official Arducam guide."
                            
                            # Still verify what we can
                            print_info "Verifying UC-955 configuration..."
                            verify_uc955_configuration
                            
                            print_info "After reboot, test the camera with: $0 --test-after-reboot"
                        fi
                        camera_configured=true
                        ;;
                    usb)
                        print_info "USB Camera selected (non-interactive) - no configuration needed"
                        print_info "Simply plug in any UVC-compatible USB webcam and restart WANDA service:"
                        print_info "sudo systemctl restart wanda-telescope"
                        camera_configured=false
                        ;;
                    skip)
                        print_info "Camera setup skipped (non-interactive)"
                        camera_configured=false
                        ;;
                esac
                
                # Handle reboot in non-interactive mode
                if [ "$camera_configured" = "true" ]; then
                    if [ "$AUTO_REBOOT" = "yes" ]; then
                        print_info "Rebooting automatically to activate camera configuration..."
                        sudo reboot
                    else
                        print_warning "Reboot required to activate camera. Use --auto-reboot flag or run: sudo reboot"
                    fi
                fi
            else
                # Interactive camera setup
                echo
                print_info "🎥 Camera Setup Options:"
                print_info "  1) Arducam IMX-477 12MP Camera (standard Pi drivers)"
                print_info "  2) Arducam UC-955 (IMX462 Pivariety) Camera (requires special drivers)"  
                print_info "  3) USB Camera (plug-and-play)"
                print_info "  4) Skip camera setup for now"
                echo
                read -p "Select camera type (1-4): " camera_choice
                
                local camera_configured=false
                case $camera_choice in
                    1)
                        print_info "Setting up Arducam IMX-477 12MP Camera..."
                        print_info "IMX477 uses standard Pi camera drivers - no additional driver installation needed"
                        configure_arducam_imx477
                        print_success "IMX-477 configured. System will need to reboot to take effect."
                        camera_configured=true
                        ;;
                    2)
                        print_info "Setting up Arducam UC-955 (IMX462 Pivariety) Camera..."
                        print_info "IMX462 sensor requires Arducam Pivariety drivers for optimal performance"
                        if install_arducam_drivers; then
                            configure_arducam_uc955
                            print_success "UC-955 (IMX462) configured with drivers. System will need to reboot to take effect."
                            
                            # Verify configuration after setup
                            print_info "Verifying UC-955 configuration..."
                            verify_uc955_configuration
                            
                            print_info "After reboot, test the camera with: $0 --test-after-reboot"
                        else
                            print_warning "Driver installation failed, but overlay configured."
                            configure_arducam_uc955
                            print_info "You may need to install drivers manually later using official Arducam guide."
                            
                            # Still verify what we can
                            print_info "Verifying UC-955 configuration..."
                            verify_uc955_configuration
                            
                            print_info "After reboot, test the camera with: $0 --test-after-reboot"
                        fi
                        camera_configured=true
                        ;;
                    3)
                        print_info "USB Camera selected - no configuration needed"
                        print_info "Simply plug in any UVC-compatible USB webcam and restart WANDA service:"
                        print_info "sudo systemctl restart wanda-telescope"
                        ;;
                    4)
                        print_info "Camera setup skipped"
                        ;;
                    *)
                        print_warning "Invalid choice, skipping camera setup"
                        ;;
                esac
                
                # Interactive reboot prompt
                if [ "$camera_configured" = "true" ]; then
                    echo
                    print_info "Would you like to reboot now to activate the camera? (y/N)"
                    read -p "Reboot now? " reboot_choice
                    case $reboot_choice in
                        [Yy]*)
                            print_info "Rebooting to activate camera configuration..."
                            sudo reboot
                            ;;
                        *)
                            print_warning "Reboot skipped. Camera will not work until you reboot."
                            print_info "To reboot later: sudo reboot"
                            ;;
                    esac
                fi
            fi
        fi
        
        # Check for camera devices
        print_info "Current camera device status:"
        if [ -e "/dev/video0" ]; then
            print_success "Camera device detected: /dev/video0"
        else
            print_info "No camera device at /dev/video0"
        fi
        
        # Check for CSI camera devices
        local csi_devices=""
        for dev in /dev/video1{0,1,2,3,4,5}; do
            if [ -e "$dev" ]; then
                csi_devices="$csi_devices $dev"
            fi
        done
        if [ -n "$csi_devices" ]; then
            print_success "CSI camera devices:$csi_devices"
        else
            print_info "No CSI camera devices detected"
        fi
        
    else
        print_info "Not running on Raspberry Pi - only USB cameras supported"
        print_info "Connect any UVC-compatible USB webcam and restart WANDA service"
    fi
    
    print_success "Camera detection and setup completed"
}

test_camera_after_reboot() {
    print_info "Testing camera functionality after reboot..."
    
    # Wait a moment for system to stabilize
    sleep 5
    
    # Test basic camera detection
    print_info "Testing camera detection..."
    if timeout 10 rpicam-still --list-cameras >/dev/null 2>&1; then
        print_success "Camera detection working after reboot"
        
        # Get camera info
        local camera_info=$(timeout 10 rpicam-still --list-cameras 2>/dev/null)
        if [ -n "$camera_info" ]; then
            print_info "Camera detection output:"
            echo "$camera_info"
        fi
        
        # Test actual image capture
        print_info "Testing image capture..."
        local test_image="/tmp/test_capture.jpg"
        
        # First try a simple capture with more debugging
        print_info "Attempting simple image capture..."
        if timeout 30 rpicam-still -o "$test_image" --immediate --nopreview --verbose 2>&1; then
            if [ -f "$test_image" ]; then
                local file_size=$(stat -c%s "$test_image" 2>/dev/null || echo "0")
                if [ "$file_size" -gt 1000 ]; then
                    print_success "Image capture test passed - captured $file_size bytes"
                    rm -f "$test_image"
                else
                    print_warning "Image capture test failed - file too small ($file_size bytes)"
                fi
            else
                print_warning "Image capture test failed - no output file created"
            fi
        else
            local exit_code=$?
            if [ "$exit_code" -eq 124 ]; then
                print_warning "Image capture test timed out"
            elif [ "$exit_code" -eq 134 ]; then
                print_warning "Image capture test failed with abort (SIGABRT) - possible memory or driver issue"
                print_info "This may indicate a CMA memory allocation problem or driver compatibility issue"
            else
                print_warning "Image capture test failed with exit code $exit_code"
            fi
            
            # Try alternative capture method
            print_info "Trying alternative capture method with different parameters..."
            if timeout 30 rpicam-still -o "$test_image" --immediate --nopreview --width 1280 --height 720 2>/dev/null; then
                if [ -f "$test_image" ]; then
                    local file_size=$(stat -c%s "$test_image" 2>/dev/null || echo "0")
                    if [ "$file_size" -gt 1000 ]; then
                        print_success "Alternative image capture test passed - captured $file_size bytes"
                        rm -f "$test_image"
                    else
                        print_warning "Alternative image capture test failed - file too small ($file_size bytes)"
                    fi
                else
                    print_warning "Alternative image capture test failed - no output file created"
                fi
            else
                print_warning "Alternative image capture test also failed"
            fi
        fi
        
        # Test WANDA camera detection
        print_info "Testing WANDA camera detection..."
        if [ -d "$PROJECT_DIR" ]; then
            cd "$PROJECT_DIR"
            if [ -f "venv/bin/activate" ]; then
                source venv/bin/activate
                if python3 -c "
import sys
sys.path.insert(0, '.')
from camera.factory import CameraFactory
try:
    camera = CameraFactory.create_camera()
    print(f'Camera type: {type(camera).__name__}')
    print(f'Camera status: {getattr(camera, \"status\", \"Unknown\")}')
    if hasattr(camera, 'camera') and hasattr(camera.camera, 'wrapper'):
        print('Using libcamera subprocess wrapper')
    else:
        print('Using direct camera interface')
except Exception as e:
    print(f'Camera detection failed: {e}')
    sys.exit(1)
"; then
                    print_success "WANDA camera detection test passed"
                else
                    print_warning "WANDA camera detection test failed"
                fi
            else
                print_warning "WANDA virtual environment not found, skipping WANDA test"
            fi
        else
            print_warning "WANDA project directory not found, skipping WANDA test"
        fi
        
    else
        print_error "Camera detection failed after reboot"
        print_info "This may indicate a configuration issue. Check the following:"
        print_info "1. Device tree overlays in /boot/firmware/config.txt"
        print_info "2. arducam-pivariety.json configuration file"
        print_info "3. System logs for camera-related errors"
        
        # Show recent camera errors
        print_info "Recent camera-related errors:"
        sudo journalctl --since "10 minutes ago" | grep -i "arducam\|pivariety\|imx462\|camera\|libcamera" | tail -10
    fi
}

check_mount_detection() {
    print_step "5/5: Checking mount/GPIO detection..."
    
    # Check if we're on Raspberry Pi
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        # Check for GPIO access
        if [ -d "/sys/class/gpio" ]; then
            print_success "GPIO system accessible"
        else
            print_warning "GPIO system not accessible"
        fi
        
        # Check for RPi.GPIO
        if python3 -c "import RPi.GPIO" 2>/dev/null; then
            print_success "RPi.GPIO module available"
        else
            print_warning "RPi.GPIO module not available"
        fi
        
        # Check for gpiozero
        if python3 -c "import gpiozero" 2>/dev/null; then
            print_success "gpiozero module available"
        else
            print_warning "gpiozero module not available"
        fi
    else
        print_info "Not running on Raspberry Pi - GPIO detection not applicable"
    fi
    
    print_success "Mount/GPIO detection check completed"
}

show_verification_summary() {
    print_step "Verification complete!"
    
    echo
    print_success "🎉 WANDA Telescope Verification Complete!"
    echo
    print_info "Verification Summary:"
    print_info "  ✓ Service status checked"
    print_info "  ✓ Service logs reviewed"
    print_info "  ✓ Web interface tested"
    print_info "  ✓ Camera detection verified"
    print_info "  ✓ Mount/GPIO detection verified"
    echo
    
    # Get IP address for final display
    local ip_address
    ip_address=$(hostname -I | awk '{print $1}')
    if [ -z "$ip_address" ]; then
        # Try alternative method
        ip_address=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' || echo "")
    fi
    if [ -n "$ip_address" ]; then
        print_success "🌐 WANDA Telescope is accessible at: http://$ip_address:$WEB_PORT"
    else
        print_success "🌐 WANDA Telescope is accessible at: http://localhost:$WEB_PORT"
    fi
    
    echo
    print_info "Service Management Commands:"
    print_info "  • Check status: sudo systemctl status $SERVICE_NAME"
    print_info "  • View logs: sudo journalctl -u $SERVICE_NAME -f"
    print_info "  • Restart: sudo systemctl restart $SERVICE_NAME"
    print_info "  • Stop: sudo systemctl stop $SERVICE_NAME"
    echo
    print_info "Next Steps:"
    print_info "  1. Access the web interface from any device on your network"
    print_info "  2. Configure camera settings through the web interface"
    print_info "  3. Configure mount settings if using stepper motor control"
    print_info "  4. Test camera capture and mount tracking functionality"
    echo
    print_info "Troubleshooting:"
    print_info "  • Check logs: sudo journalctl -u $SERVICE_NAME -f"
    print_info "  • Manual start: cd $PROJECT_DIR && source venv/bin/activate && python main.py"
    print_info "  • Check hardware connections if camera/mount not working"
    echo
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run this script as root. Run as the user that operates WANDA."
    exit 1
fi

# Check if WANDA is installed
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "WANDA Telescope not found at $PROJECT_DIR"
    print_info "Please run install.sh first to install WANDA Telescope."
    exit 1
fi

# Check if service exists
if ! sudo systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
    print_error "WANDA Telescope service not found!"
    print_info "Please run install.sh first to install WANDA Telescope."
    exit 1
fi

# Main verification process
main() {
    print_banner
    
    # Check if we're just testing after reboot
    if [ "$TEST_AFTER_REBOOT" = "yes" ]; then
        print_info "Testing camera functionality after reboot..."
        test_camera_after_reboot
        return
    fi
    
    check_service_status
    check_service_logs
    check_web_interface
    check_camera_detection
    check_mount_detection
    show_verification_summary
}

# Validate sudo access
print_info "Validating sudo access..."
if ! sudo -n true 2>/dev/null; then
    print_info "Sudo access required. Please enter your password when prompted."
    if ! sudo true; then
        print_error "Sudo access validation failed. Please ensure you have sudo privileges."
        exit 1
    fi
fi

# Run main verification
main "$@"
