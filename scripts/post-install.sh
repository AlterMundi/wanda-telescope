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
    local ip_address=$(hostname -I | awk '{print $1}')
    if [ -z "$ip_address" ]; then
        print_error "Could not determine IP address"
        exit 1
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

check_camera_detection() {
    print_step "4/5: Checking camera detection..."
    
    # Check if we're on Raspberry Pi
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        local pi_model=$(cat /proc/device-tree/model)
        print_info "Running on: $pi_model"
        
        # Check for camera modules
        if lsmod | grep -q "bcm2835-v4l2\|v4l2_common"; then
            print_success "Camera modules loaded"
        else
            print_warning "Camera modules not loaded (may be normal if no camera connected)"
        fi
        
        # Check for camera devices
        if [ -e "/dev/video0" ]; then
            print_success "Camera device detected: /dev/video0"
        else
            print_warning "No camera device found at /dev/video0"
            print_info "This is normal if no camera is connected"
        fi
        
        # Check for CSI camera
        if [ -e "/dev/video10" ] || [ -e "/dev/video11" ] || [ -e "/dev/video12" ]; then
            print_success "CSI camera device detected"
        else
            print_info "No CSI camera detected (normal if not using Pi camera)"
        fi
    else
        print_info "Not running on Raspberry Pi - camera detection may be limited"
    fi
    
    print_success "Camera detection check completed"
}

check_mount_detection() {
    print_step "5/7: Checking mount/GPIO detection..."
    
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

configure_camera_modules() {
    print_step "6/7: Configuring camera modules..."
    
    # Check if we're on Raspberry Pi
    if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        print_info "Not running on Raspberry Pi - camera configuration not applicable"
        return 0
    fi
    
    local pi_model=$(cat /proc/device-tree/model)
    print_info "Detected: $pi_model"
    
    # Determine config file location based on hardware and OS
    local config_file=""
    local os_version=""
    
    if [ -f "/etc/os-release" ]; then
        os_version=$(grep VERSION_CODENAME /etc/os-release | cut -d'=' -f2)
        print_info "OS Version: $os_version"
    fi
    
    # Check for Raspberry Pi 5 first (which uses /boot/firmware/config.txt)
    if [ -f "/proc/device-tree/model" ] && grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
        config_file="/boot/firmware/config.txt"
        print_info "Detected Raspberry Pi 5 - using /boot/firmware/config.txt"
    # Check for Bookworm OS (which also uses /boot/firmware/config.txt)
    elif [ "$os_version" = "bookworm" ]; then
        config_file="/boot/firmware/config.txt"
        print_info "Detected Bookworm OS - using /boot/firmware/config.txt"
    # Fallback to traditional location
    else
        config_file="/boot/config.txt"
        print_info "Using traditional config location: /boot/config.txt"
    fi
    
    # Verify config file exists, try alternative location if needed
    if [ ! -f "$config_file" ]; then
        print_warning "Configuration file not found at: $config_file"
        
        # Try alternative location
        local alt_config=""
        if [ "$config_file" = "/boot/firmware/config.txt" ]; then
            alt_config="/boot/config.txt"
        else
            alt_config="/boot/firmware/config.txt"
        fi
        
        if [ -f "$alt_config" ]; then
            print_info "Found configuration file at alternative location: $alt_config"
            config_file="$alt_config"
        else
            print_error "Configuration file not found at either location:"
            print_error "  Primary: $config_file"
            print_error "  Alternative: $alt_config"
            print_info "Cannot proceed with camera configuration"
            return 1
        fi
    fi
    
    print_info "Configuration file: $config_file"
    
    # Ask user which camera module they have
    echo
    print_info "Camera Module Selection:"
    print_info "Please select your camera module:"
    echo
    print_info "1) ARDUCAM 12MP IMX477 (Native camera)"
    print_info "2) ARDUCAM UC-955 (Pivariety camera)"
    print_info "3) Skip camera configuration"
    echo
    
    read -p "Enter your choice (1, 2, or 3): " camera_choice
    
    case $camera_choice in
        1)
            configure_arducam_imx477 "$config_file"
            ;;
        2)
            configure_arducam_uc955 "$config_file"
            ;;
        3)
            print_info "Skipping camera configuration"
            return 0
            ;;
        *)
            print_error "Invalid choice. Skipping camera configuration."
            return 1
            ;;
    esac
}

configure_arducam_imx477() {
    local config_file="$1"
    print_info "Configuring ARDUCAM 12MP IMX477 camera..."
    
    # Check if required camera packages are installed
    if ! dpkg -l | grep -q "python3-picamera2\|python3-libcamera"; then
        print_warning "Required camera packages not detected"
        print_info "The IMX477 camera requires picamera2 and libcamera packages"
        print_info "These should have been installed by install.sh, but if not:"
        print_info "  sudo apt update && sudo apt install -y python3-picamera2 python3-libcamera"
        echo
        print_info "After installing the packages, run this script again to configure the camera."
        return 1
    fi
    
    # Check if configuration is already applied
    if grep -q "dtoverlay=imx477" "$config_file"; then
        print_info "IMX477 overlay already configured"
    else
        print_info "Applying IMX477 configuration to $config_file..."
        
        # Create backup
        sudo cp "$config_file" "${config_file}.backup.$(date +%Y%m%d_%H%M%S)"
        print_info "Backup created: ${config_file}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Check if sensor config file exists
        local sensor_config="$PROJECT_DIR/sensor-configs/config-for-IMX477.txt"
        if [ ! -f "$sensor_config" ]; then
            print_error "Sensor configuration file not found: $sensor_config"
            print_info "Cannot proceed with camera configuration"
            return 1
        fi
        
        # Apply the complete sensor configuration
        print_info "Applying complete IMX477 configuration..."
        if sudo cp "$sensor_config" "$config_file"; then
            print_success "IMX477 configuration applied successfully"
        else
            print_error "Failed to apply IMX477 configuration"
            return 1
        fi
        
        print_warning "Configuration updated. A reboot is required for changes to take effect."
        print_info "After reboot, the camera should be detected automatically."
    fi
    
    # Fix camera permissions for Pi 5 DMA heap access
    print_info "Fixing camera permissions for Pi 5 DMA heap access..."
    
    # Add user to video and gpio groups
    local current_user=$(whoami)
    if ! groups "$current_user" | grep -q "video"; then
        print_info "Adding user $current_user to video group..."
        sudo usermod -a -G video "$current_user"
        print_success "User added to video group"
    else
        print_info "User already in video group"
    fi
    
    if ! groups "$current_user" | grep -q "gpio"; then
        print_info "Adding user $current_user to gpio group..."
        sudo usermod -a -G gpio "$current_user"
        print_success "User added to gpio group"
    else
        print_info "User already in gpio group"
    fi
    
    # Create udev rules for persistent camera permissions
    print_info "Creating udev rules for camera permissions..."
    sudo tee /etc/udev/rules.d/99-camera-permissions.rules > /dev/null <<EOF
# Camera device permissions for WANDA Telescope
KERNEL=="media*", MODE="0666", GROUP="video"
KERNEL=="video*", MODE="0666", GROUP="video"
KERNEL=="v4l2-subdev*", MODE="0666", GROUP="video"

# GPIO permissions
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"
SUBSYSTEM=="bcm2835-gpiomem", GROUP="gpio", MODE="0660"
EOF
    
    print_success "Udev rules created for camera permissions"
    
    # Show current configuration
    print_info "Current camera configuration:"
    if [ -f "$config_file" ]; then
        echo "----------------------------------------"
        cat "$config_file"
        echo "----------------------------------------"
    else
        print_info "No camera configuration found"
    fi
    
    # Check if camera is currently detected (may not work until reboot)
    print_info "Checking current camera detection..."
    if command -v rpicam-still >/dev/null 2>&1; then
        local camera_list=$(rpicam-still --list-cameras 2>/dev/null || echo "No cameras detected")
        print_info "Current camera list: $camera_list"
    else
        print_info "rpicam-still not available for testing"
    fi
    
    print_info "Camera permissions configured. A reboot is required for all changes to take effect."
}

configure_arducam_uc955() {
    local config_file="$1"
    print_info "Configuring ARDUCAM UC-955 (Pivariety) camera..."
    
    # Check if Arducam Pivariety driver is installed
    if ! dpkg -l | grep -q "arducam-pivariety"; then
        print_warning "Arducam Pivariety driver not detected"
        print_info "The UC-955 camera requires the official Arducam Pivariety driver"
        print_info "Please install it first:"
        print_info "  curl -sSL https://raw.githubusercontent.com/ArduCAM/Arducam-Pivariety/master/install.sh | bash"
        echo
        print_info "After installing the driver, run this script again to configure the camera."
        return 1
    fi
    
    # Check if configuration is already applied
    if grep -q "dtoverlay=arducam-pivariety" "$config_file"; then
        print_info "Arducam Pivariety overlay already configured"
    else
        print_info "Applying UC-955 configuration to $config_file..."
        
        # Create backup
        sudo cp "$config_file" "${config_file}.backup.$(date +%Y%m%d_%H%M%S)"
        print_info "Backup created: ${config_file}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Check if sensor config file exists
        local sensor_config="$PROJECT_DIR/sensor-configs/config-for-UC955.txt"
        if [ ! -f "$sensor_config" ]; then
            print_error "Sensor configuration file not found: $sensor_config"
            print_info "Cannot proceed with camera configuration"
            return 1
        fi
        
        # Apply the complete sensor configuration
        print_info "Applying complete UC-955 configuration..."
        if sudo cp "$sensor_config" "$config_file"; then
            print_success "UC-955 configuration applied successfully"
        else
            print_error "Failed to apply UC-955 configuration"
            return 1
        fi
        
        print_warning "Configuration updated. A reboot is required for changes to take effect."
        print_info "After reboot, the camera should be detected automatically."
    fi
    
    # Fix camera permissions for Pi 5 DMA heap access
    print_info "Fixing camera permissions for Pi 5 DMA heap access..."
    
    # Add user to video and gpio groups
    local current_user=$(whoami)
    if ! groups "$current_user" | grep -q "video"; then
        print_info "Adding user $current_user to video group..."
        sudo usermod -a -G video "$current_user"
        print_success "User added to video group"
    else
        print_info "User already in video group"
    fi
    
    if ! groups "$current_user" | grep -q "gpio"; then
        print_info "Adding user $current_user to gpio group..."
        sudo usermod -a -G gpio "$current_user"
        print_success "User added to gpio group"
    else
        print_info "User already in gpio group"
    fi
    
    # Create udev rules for persistent camera permissions
    print_info "Creating udev rules for camera permissions..."
    sudo tee /etc/udev/rules.d/99-camera-permissions.rules > /dev/null <<EOF
# Camera device permissions for WANDA Telescope
KERNEL=="media*", MODE="0666", GROUP="video"
KERNEL=="video*", MODE="0666", GROUP="video"
KERNEL=="v4l2-subdev*", MODE="0666", GROUP="video"

# GPIO permissions
SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"
SUBSYSTEM=="bcm2835-gpiomem", GROUP="gpio", MODE="0660"
EOF
    
    print_success "Udev rules created for camera permissions"
    
    # Show current configuration
    print_info "Current camera configuration:"
    if [ -f "$config_file" ]; then
        echo "----------------------------------------"
        cat "$config_file"
        echo "----------------------------------------"
    else
        print_info "No camera configuration found"
    fi
    
    # Check if camera is currently detected (may not work until reboot)
    print_info "Checking current camera detection..."
    if command -v rpicam-still >/dev/null 2>&1; then
        local camera_list=$(rpicam-still --list-cameras 2>/dev/null || echo "No cameras detected")
        print_info "Current camera list: $camera_list"
    else
        print_info "rpicam-still not available for testing"
    fi
    
    print_info "Camera permissions configured. A reboot is required for all changes to take effect."
}

verify_camera_permissions() {
    print_info "Verifying camera permissions..."
    
    # Check if user is in required groups
    local current_user=$(whoami)
    local in_video_group=false
    local in_gpio_group=false
    
    if groups "$current_user" | grep -q "video"; then
        in_video_group=true
        print_success "User $current_user is in video group"
    else
        print_warning "User $current_user is not in video group"
    fi
    
    if groups "$current_user" | grep -q "gpio"; then
        in_gpio_group=true
        print_success "User $current_user is in gpio group"
    else
        print_warning "User $current_user is not in gpio group"
    fi
    
    # Check if udev rules exist
    if [ -f "/etc/udev/rules.d/99-camera-permissions.rules" ]; then
        print_success "Camera permission udev rules exist"
    else
        print_warning "Camera permission udev rules not found"
    fi
    
    # Test camera access without sudo (if possible)
    if command -v rpicam-still >/dev/null 2>&1; then
        print_info "Testing camera access without sudo..."
        
        # Try to list cameras without sudo
        local camera_test=$(rpicam-still --list-cameras 2>&1)
        
        if echo "$camera_test" | grep -q "imx477\|arducam"; then
            print_success "Camera accessible without sudo!"
            print_info "Camera test result: $camera_test"
        elif echo "$camera_test" | grep -q "Could not open any dmaHeap device"; then
            print_warning "DMA heap access issue detected - permissions may need reboot to take effect"
            print_info "This is normal after permission changes"
        else
            print_warning "Camera access test inconclusive: $camera_test"
        fi
    else
        print_info "rpicam-still not available for permission testing"
    fi
    
    print_info "Permission verification completed"
}

show_camera_configuration_help() {
    echo
    print_info "Camera Configuration Help:"
    print_info "=========================="
    
    if [ "$camera_choice" = "1" ]; then
        print_info "ARDUCAM 12MP IMX477 Configuration:"
        print_info "  • Applied complete IMX477 configuration from sensor-configs/config-for-IMX477.txt"
        print_info "  • Includes optimized settings for Raspberry Pi 5, 4, 3, Zero, and Compute Modules"
        print_info "  • Supports both Bookworm and Bullseye OS"
        echo
        print_info "Next Steps:"
        print_info "  1. Reboot your Raspberry Pi: sudo reboot"
        print_info "  2. After reboot, test camera with: rpicam-still --list-cameras"
        print_info "  3. Take a test photo: rpicam-still -t 5000 -o test.jpg"
        echo
        print_info "Documentation: https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/12MP-IMX477/"
        
    elif [ "$camera_choice" = "2" ]; then
        print_info "ARDUCAM UC-955 (Pivariety) Configuration:"
        print_info "  • Applied complete UC-955 configuration from sensor-configs/config-for-UC955.txt"
        print_info "  • Includes optimized settings for high-performance IMX477-based camera"
        print_info "  • Requires official Arducam Pivariety driver"
        echo
        print_info "Next Steps:"
        print_info "  1. Reboot your Raspberry Pi: sudo reboot"
        print_info "  2. After reboot, test camera with: rpicam-still --list-cameras"
        print_info "  3. Take a test photo: rpicam-still -t 5000 -o test.jpg"
        echo
        print_info "Documentation: https://docs.arducam.com/Raspberry-Pi-Camera/Pivariety-Camera/Quick-Start-Guide/"
    fi
    
    echo
    print_info "Troubleshooting:"
    print_info "  • If camera not detected after reboot, check CSI cable connection"
    print_info "  • Verify camera is properly seated in CSI connector"
    print_info "  • Check logs: dmesg | grep -i camera"
    print_info "  • Ensure camera is powered (Pi camera modules are powered via CSI)"
    echo
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
    print_info "  ✓ Camera module configuration completed"
    print_info "  ✓ Camera permissions verified"
    echo
    
    # Get IP address for final display
    local ip_address=$(hostname -I | awk '{print $1}')
    if [ -n "$ip_address" ]; then
        print_success "🌐 WANDA Telescope is accessible at: http://$ip_address:$WEB_PORT"
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
    
    # Show camera configuration help if camera was configured
    if [ -n "$camera_choice" ] && [ "$camera_choice" != "3" ]; then
        show_camera_configuration_help
        
        # Check if reboot is needed for camera configuration
        if [ "$camera_choice" = "1" ] || [ "$camera_choice" = "2" ]; then
            echo
            print_warning "⚠️  IMPORTANT: Camera configuration requires a reboot to take effect!"
            print_info "After completing this verification, please reboot your Raspberry Pi:"
            print_info "  sudo reboot"
            echo
            print_info "After reboot, your camera should be automatically detected by WANDA Telescope."
        fi
    fi
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
    check_service_status
    check_service_logs
    check_web_interface
    check_camera_detection
    check_mount_detection
    configure_camera_modules
    verify_camera_permissions
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
