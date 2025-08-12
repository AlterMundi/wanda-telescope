#!/bin/bash

# WANDA Telescope One-Command Deployment Script
# This script completely sets up WANDA Telescope on a fresh Raspberry Pi OS Lite
# Usage: curl -sSL https://raw.githubusercontent.com/AlterMundi/wanda-telescope/main/scripts/deploy-to-pi.sh | bash

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
BRANCH="main"
REPO_URL="https://github.com/AlterMundi/wanda-telescope.git"
PROJECT_DIR="$HOME/wanda-telescope"
USER=$(whoami)

print_banner() {
    echo
    print_info "🔭 WANDA Telescope - One-Command Deployment"
    print_info "============================================="
    print_info "This script will completely set up WANDA Telescope on your Pi"
    print_info "Branch: $BRANCH"
    print_info "Target: $PROJECT_DIR"
    print_info "User: $USER"
    echo
}

check_system() {
    print_step "1/8: Checking system requirements..."
    
    # Check network connectivity
    print_info "Checking network connectivity..."
    if ! ping -c 1 github.com >/dev/null 2>&1; then
        print_error "No internet connection. Please check your network and try again."
        exit 1
    fi
    print_success "Network connectivity confirmed"
    
    # Check if we're on a Raspberry Pi
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        local pi_model=$(cat /proc/device-tree/model)
        print_success "Detected: $pi_model"
    else
        print_warning "Not running on Raspberry Pi - will use mock implementations"
    fi
    
    # Check OS version
    if [ -f /etc/os-release ]; then
        local os_name=$(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)
        print_info "OS: $os_name"
    fi
    
    print_success "System check completed"
}

configure_arducam_imx477() {
    print_step "2/8: Checking for Arducam IMX477 camera configuration..."
    
    # Check if we're on Raspberry Pi 5
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi 5" /proc/device-tree/model 2>/dev/null; then
        print_info "Raspberry Pi 5 detected"
        print_info "Note: For Arducam IMX477 cameras, manual configuration of /boot/firmware/config.txt may be required"
        print_info "See docs/ARDUCAM_UC955_SETUP.md for detailed setup instructions"
    else
        print_info "Not Raspberry Pi 5, skipping Arducam IMX477 configuration"
    fi
}

install_system_dependencies() {
    print_step "3/9: Installing system dependencies..."
    
    # Update package list
    print_info "Updating package list..."
    sudo apt update -qq
    
    # Install essential packages
    print_info "Installing essential packages..."
    sudo apt install -y -qq \
        git \
        curl \
        wget \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        cmake \
        pkg-config \
        libatlas-base-dev \
        libhdf5-dev \
        libhdf5-serial-dev \
        libhdf5-103 \
        python3-pyqt5 \
        libgtk-3-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        gfortran \
        libopenblas-dev \
        liblapack-dev \
        libgstreamer1.0-dev \
        libgstreamer-plugins-base1.0-dev \
        libgstreamer-plugins-bad1.0-dev \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-libav \
        gstreamer1.0-tools \
        gstreamer1.0-x \
        gstreamer1.0-alsa \
        gstreamer1.0-gl \
        gstreamer1.0-gtk3 \
        gstreamer1.0-qt5 \
        gstreamer1.0-pulseaudio \
        libcap-dev
    
    # Install Pi-specific packages if on Raspberry Pi
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        print_info "Installing Raspberry Pi specific packages..."
        sudo apt install -y -qq \
            python3-picamera2 \
            python3-libcamera \
            python3-rpi.gpio \
            python3-gpiozero \
            libraspberrypi-dev \
            libraspberrypi-bin
    fi
    
    print_success "System dependencies installed"
}

setup_directories() {
    print_step "4/8: Setting up project directories..."
    
    # Create project directory
    if ! mkdir -p "$PROJECT_DIR"; then
        print_error "Failed to create project directory: $PROJECT_DIR"
        exit 1
    fi
    
    if ! cd "$PROJECT_DIR"; then
        print_error "Failed to change to project directory: $PROJECT_DIR"
        exit 1
    fi
    
    print_success "Directories created"
}

clone_repository() {
    print_step "5/8: Cloning WANDA Telescope repository..."
    
    if [ -d "$PROJECT_DIR/.git" ]; then
        print_info "Repository exists, updating..."
        if ! git fetch origin; then
            print_error "Failed to fetch from origin"
            exit 1
        fi
        if ! git checkout "$BRANCH"; then
            print_error "Failed to checkout branch: $BRANCH"
            exit 1
        fi
        if ! git pull origin "$BRANCH"; then
            print_error "Failed to pull from origin"
            exit 1
        fi
        print_success "Repository updated"
    else
        print_info "Cloning repository..."
        if ! git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"; then
            print_error "Failed to clone repository"
            exit 1
        fi
        if ! cd "$PROJECT_DIR"; then
            print_error "Failed to change to project directory after clone"
            exit 1
        fi
        print_success "Repository cloned"
    fi
}

setup_python_environment() {
    print_step "6/8: Setting up Python environment..."
    
    if ! cd "$PROJECT_DIR"; then
        print_error "Failed to change to project directory"
        exit 1
    fi
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    if ! python3 -m venv venv; then
        print_error "Failed to create virtual environment"
        exit 1
    fi
    
    # Use full path to pip instead of activating environment
    local pip_path="$PROJECT_DIR/venv/bin/pip"
    local python_path="$PROJECT_DIR/venv/bin/python"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    if ! "$pip_path" install --upgrade pip setuptools wheel; then
        print_error "Failed to upgrade pip"
        exit 1
    fi
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        if ! "$pip_path" install -r requirements.txt; then
            print_error "Failed to install requirements.txt dependencies"
            exit 1
        fi
    else
        print_warning "requirements.txt not found, installing basic dependencies..."
        if ! "$pip_path" install flask opencv-python numpy pillow requests; then
            print_error "Failed to install basic dependencies"
            exit 1
        fi
    fi
    
    # Install additional dependencies for Pi camera
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        print_info "Installing Pi camera dependencies..."
        if ! "$pip_path" install picamera2; then
            print_warning "Failed to install picamera2 - will use mock camera"
        fi
    fi
    
    print_success "Python environment setup completed"
}

install_systemd_service() {
    print_step "7/8: Installing systemd service..."
    
    if ! cd "$PROJECT_DIR"; then
        print_error "Failed to change to project directory"
        exit 1
    fi
    
    # Check if main.py exists
    if [ ! -f "main.py" ]; then
        print_error "main.py not found in project directory"
        exit 1
    fi
    
    # Create systemd service file
    print_info "Creating systemd service file..."
    if ! sudo tee /etc/systemd/system/wanda-telescope.service > /dev/null <<EOF
[Unit]
Description=WANDA Telescope Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    then
        print_error "Failed to create systemd service file"
        exit 1
    fi
    
    # Reload systemd and enable service
    print_info "Enabling service..."
    if ! sudo systemctl daemon-reload; then
        print_error "Failed to reload systemd daemon"
        exit 1
    fi
    
    if ! sudo systemctl enable wanda-telescope; then
        print_error "Failed to enable wanda-telescope service"
        exit 1
    fi
    
    print_success "Systemd service installed and enabled"
}

test_installation() {
    print_step "8/8: Testing installation..."
    
    # Start service
    print_info "Starting WANDA service..."
    if ! sudo systemctl start wanda-telescope; then
        print_error "Failed to start wanda-telescope service"
        sudo systemctl status wanda-telescope --no-pager
        exit 1
    fi
    
    # Wait for startup with better error checking
    print_info "Waiting for service to start..."
    local max_wait=30
    local wait_count=0
    
    while [ $wait_count -lt $max_wait ]; do
        if sudo systemctl is-active wanda-telescope >/dev/null 2>&1; then
            break
        fi
        sleep 1
        wait_count=$((wait_count + 1))
    done
    
    # Check service status
    if sudo systemctl is-active wanda-telescope >/dev/null 2>&1; then
        print_success "Service is running successfully"
        
        # Get IP address
        local ip_address=$(hostname -I | awk '{print $1}')
        if [ -n "$ip_address" ]; then
            print_success "WANDA is accessible at: http://$ip_address:5000"
        fi
    else
        print_error "Service failed to start within $max_wait seconds"
        sudo systemctl status wanda-telescope --no-pager
        exit 1
    fi
}

show_completion_info() {
    print_step "9/9: Deployment complete!"
    
    echo
    print_success "🎉 WANDA Telescope Deployment Complete!"
    echo
    print_info "Your WANDA Telescope is now running and will start automatically on boot!"
    echo
    print_info "Access Information:"
    local ip_address=$(hostname -I | awk '{print $1}')
    if [ -n "$ip_address" ]; then
        print_success "🌐 Web Interface: http://$ip_address:5000"
    fi
    echo
    print_info "Service Management:"
    print_info "  • Check status: sudo systemctl status wanda-telescope"
    print_info "  • View logs: sudo journalctl -u wanda-telescope -f"
    print_info "  • Restart: sudo systemctl restart wanda-telescope"
    print_info "  • Stop: sudo systemctl stop wanda-telescope"
    echo
    print_info "Next Steps:"
    print_info "  1. Reboot to test auto-startup: sudo reboot"
    print_info "  2. Access the web interface from any device on your network"
    print_info "  3. Configure camera and mount settings through the web interface"
    echo
    print_info "Troubleshooting:"
    print_info "  • Check logs: sudo journalctl -u wanda-telescope -f"
    print_info "  • Manual start: cd $PROJECT_DIR && source venv/bin/activate && python main.py"
    echo
}

# Cleanup function for error handling
cleanup_on_error() {
    print_error "Deployment failed! Cleaning up..."
    
    # Stop service if it was started
    if sudo systemctl is-active wanda-telescope >/dev/null 2>&1; then
        print_info "Stopping wanda-telescope service..."
        sudo systemctl stop wanda-telescope 2>/dev/null || true
    fi
    
    # Disable service if it was enabled
    if sudo systemctl is-enabled wanda-telescope >/dev/null 2>&1; then
        print_info "Disabling wanda-telescope service..."
        sudo systemctl disable wanda-telescope 2>/dev/null || true
    fi
    
    # Remove service file if it exists
    if [ -f /etc/systemd/system/wanda-telescope.service ]; then
        print_info "Removing systemd service file..."
        sudo rm -f /etc/systemd/system/wanda-telescope.service
        sudo systemctl daemon-reload 2>/dev/null || true
    fi
    
    print_error "Cleanup completed. Please check the error messages above and try again."
}

# Main deployment process
main() {
    # Set trap for error handling
    trap cleanup_on_error ERR
    
    print_banner
    check_system
    configure_arducam_imx477
    install_system_dependencies
    setup_directories
    clone_repository
    setup_python_environment
    install_systemd_service
    test_installation
    show_completion_info
    
    # Clear trap on successful completion
    trap - ERR
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run this script as root. Run as the user that will operate WANDA."
    exit 1
fi

# Validate sudo access
print_info "Validating sudo access..."
if ! sudo -n true 2>/dev/null; then
    print_info "Sudo access required. Please enter your password when prompted."
    if ! sudo true; then
        print_error "Sudo access validation failed. Please ensure you have sudo privileges."
        exit 1
    fi
fi

# Check for required commands
for cmd in git python3 pip3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        print_warning "Command '$cmd' not found - will be installed during setup"
    fi
done

# Run main deployment
main "$@"