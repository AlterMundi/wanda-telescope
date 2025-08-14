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
