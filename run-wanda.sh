#!/bin/bash

# WANDA Telescope Launcher Script
# This script sets up the environment and runs the WANDA telescope system
# Can be run multiple times safely

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Function to check if we're on a Raspberry Pi
is_raspberry_pi() {
    if [ -f /proc/device-tree/model ]; then
        if grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to check if a Python package is installed
is_package_installed() {
    python3 -c "import $1" 2>/dev/null
}

# Function to check if virtual environment needs system packages
needs_system_packages() {
    if is_raspberry_pi; then
        return 0  # True - Pi needs system packages for libcamera
    fi
    return 1  # False - Regular systems don't need system packages
}

# Main script starts here
print_status "Starting WANDA Telescope System Setup..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "Working directory: $SCRIPT_DIR"

# Check if we're on a Raspberry Pi
if is_raspberry_pi; then
    print_success "Detected Raspberry Pi system"
    PI_MODE=true
else
    print_status "Detected regular system (not Raspberry Pi)"
    PI_MODE=false
fi

# Step 1: Create virtual environment if it doesn't exist
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating virtual environment..."
    
    if [ "$PI_MODE" = true ]; then
        # Create venv with system site packages for Pi (needed for libcamera)
        python3 -m venv --system-site-packages "$VENV_DIR"
        print_success "Created virtual environment with system site packages"
    else
        # Create regular venv for other systems
        python3 -m venv "$VENV_DIR"
        print_success "Created virtual environment"
    fi
else
    print_status "Virtual environment already exists"
fi

# Step 2: Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Verify activation
if [ "$VIRTUAL_ENV" != "" ]; then
    print_success "Virtual environment activated: $VIRTUAL_ENV"
else
    print_error "Failed to activate virtual environment"
    exit 1
fi

# Step 3: Upgrade pip to latest version
print_status "Upgrading pip..."
python3 -m pip install --upgrade pip > /dev/null 2>&1

# Step 4: Install/update requirements
if [ -f "requirements.txt" ]; then
    print_status "Installing/updating requirements from requirements.txt..."
    pip install -r requirements.txt
    print_success "Requirements installed/updated"
else
    print_warning "requirements.txt not found, installing basic requirements..."
    pip install Flask Werkzeug Jinja2 opencv-python numpy Pillow
fi

# Step 5: Install picamera2 if on Raspberry Pi
if [ "$PI_MODE" = true ]; then
    print_status "Checking for picamera2 (Raspberry Pi camera library)..."
    
    # Check if picamera2 is already installed and working
    if python3 -c "import picamera2; print('picamera2 is available')" 2>/dev/null; then
        print_success "picamera2 is already installed and working"
    else
        print_status "Installing picamera2..."
        
        # Try different installation methods
        if sudo apt update && sudo apt install -y python3-picamera2 2>/dev/null; then
            print_success "Installed picamera2 via apt"
        elif pip install picamera2 2>/dev/null; then
            print_success "Installed picamera2 via pip"
        else
            print_warning "Could not install picamera2 automatically"
            print_warning "You may need to install it manually:"
            print_warning "  sudo apt update && sudo apt install python3-picamera2"
        fi
    fi
    
    # Also check for libcamera Python bindings
    if python3 -c "import libcamera" 2>/dev/null; then
        print_success "libcamera Python bindings are available"
    else
        print_warning "libcamera Python bindings not found"
        print_warning "Installing libcamera Python bindings..."
        sudo apt install -y python3-libcamera 2>/dev/null || print_warning "Could not install libcamera bindings"
    fi
fi

# Step 6: Create captures directory
print_status "Creating captures directory..."
mkdir -p captures
print_success "Captures directory ready"

# Step 7: Check camera permissions (Pi only)
if [ "$PI_MODE" = true ]; then
    print_status "Checking camera permissions..."
    
    # Add user to video group if not already there
    if ! groups | grep -q video; then
        print_status "Adding user to video group..."
        sudo usermod -a -G video "$USER"
        print_warning "User added to video group. You may need to log out and back in for camera access."
    fi
    
    # Check if camera interface is enabled
    if ! libcamera-hello --list-cameras 2>/dev/null | grep -q "Available cameras"; then
        print_warning "Camera not detected. Make sure:"
        print_warning "  1. Camera is properly connected"
        print_warning "  2. Camera interface is enabled (sudo raspi-config -> Interface Options -> Camera)"
        print_warning "  3. System has been rebooted after enabling camera"
    else
        print_success "Camera detected and accessible"
    fi
fi

# Step 8: Final system check
print_status "Performing system check..."

# Check Python version
PYTHON_VERSION=$(python3 --version)
print_status "Python version: $PYTHON_VERSION"

# Check critical imports
print_status "Testing critical imports..."
IMPORTS_OK=true

if ! python3 -c "import flask" 2>/dev/null; then
    print_error "Flask import failed"
    IMPORTS_OK=false
fi

if ! python3 -c "import cv2" 2>/dev/null; then
    print_error "OpenCV import failed"
    IMPORTS_OK=false
fi

if [ "$PI_MODE" = true ]; then
    if ! python3 -c "import picamera2" 2>/dev/null; then
        print_error "picamera2 import failed"
        IMPORTS_OK=false
    fi
fi

if [ "$IMPORTS_OK" = true ]; then
    print_success "All critical imports successful"
else
    print_error "Some imports failed. Check the error messages above."
    exit 1
fi

# Step 9: Display startup information
echo
print_success "=== WANDA Telescope System Ready ==="
echo
print_status "System Information:"
print_status "  • Platform: $(if [ "$PI_MODE" = true ]; then echo "Raspberry Pi"; else echo "Generic Linux"; fi)"
print_status "  • Python: $PYTHON_VERSION"
print_status "  • Virtual Environment: $VIRTUAL_ENV"
print_status "  • Working Directory: $SCRIPT_DIR"
print_status "  • Captures Directory: $SCRIPT_DIR/captures"
echo

# Step 10: Run the application
print_status "Starting WANDA Telescope Web Server..."
echo
print_success "🔭 WANDA Telescope is starting up..."
print_success "📱 Web interface will be available at:"
print_success "   • Local: http://localhost:5000"
print_success "   • Network: http://$(hostname -I | awk '{print $1}'):5000"
echo
print_status "Press Ctrl+C to stop the server"
echo

# Run the main application
exec python3 main.py