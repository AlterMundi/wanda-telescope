#!/bin/bash

# WANDA Telescope One-Command Deployment Script
# This script completely sets up WANDA Telescope on a fresh Raspberry Pi OS Lite
# Usage: curl -sSL https://raw.githubusercontent.com/AlterMundi/wanda-telescope/feat/auto-deploy-rpi/scripts/deploy-to-pi.sh | bash

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
BRANCH="feat/auto-deploy-rpi"
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

install_system_dependencies() {
    print_step "2/8: Installing system dependencies..."
    
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
        gstreamer1.0-pulseaudio
    
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
    print_step "3/8: Setting up project directories..."
    
    # Create project directory
    mkdir -p "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    print_success "Directories created"
}

clone_repository() {
    print_step "4/8: Cloning WANDA Telescope repository..."
    
    if [ -d "$PROJECT_DIR/.git" ]; then
        print_info "Repository exists, updating..."
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
        print_success "Repository updated"
    else
        print_info "Cloning repository..."
        git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
        print_success "Repository cloned"
    fi
}

setup_python_environment() {
    print_step "5/8: Setting up Python environment..."
    
    cd "$PROJECT_DIR"
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        print_warning "requirements.txt not found, installing basic dependencies..."
        pip install flask opencv-python numpy pillow requests
    fi
    
    # Install additional dependencies for Pi camera
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        print_info "Installing Pi camera dependencies..."
        pip install picamera2
    fi
    
    print_success "Python environment setup completed"
}

install_systemd_service() {
    print_step "6/8: Installing systemd service..."
    
    cd "$PROJECT_DIR"
    
    # Create systemd service file
    print_info "Creating systemd service file..."
    sudo tee /etc/systemd/system/wanda-telescope.service > /dev/null <<EOF
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
    
    # Reload systemd and enable service
    print_info "Enabling service..."
    sudo systemctl daemon-reload
    sudo systemctl enable wanda-telescope
    
    print_success "Systemd service installed and enabled"
}

test_installation() {
    print_step "7/8: Testing installation..."
    
    # Start service
    print_info "Starting WANDA service..."
    sudo systemctl start wanda-telescope
    
    # Wait for startup
    print_info "Waiting for service to start..."
    sleep 15
    
    # Check service status
    if sudo systemctl is-active wanda-telescope >/dev/null 2>&1; then
        print_success "Service is running successfully"
        
        # Get IP address
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
    print_step "8/8: Deployment complete!"
    
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

# Main deployment process
main() {
    print_banner
    check_system
    install_system_dependencies
    setup_directories
    clone_repository
    setup_python_environment
    install_systemd_service
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