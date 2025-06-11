#!/bin/bash

# Wanda Telescope - Automated Setup and Run Script
# This script handles dependency installation and starts the astrophotography system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Check if running as root (not recommended for this application)
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root is not recommended. Consider running as a regular user."
fi

# Get script directory and change to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "Starting Wanda Telescope setup from: $SCRIPT_DIR"

# Quick status check for subsequent runs
if [ -d "venv" ] && [ -d "$HOME/wanda_captures" ]; then
    print_status "Previous setup detected - performing quick startup check..."
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip in virtual environment
print_status "Ensuring pip is up to date..."
python -m pip install --upgrade pip --verbose

# Install requirements
print_status "Installing/updating Python dependencies..."

# Create minimal requirements for core functionality
cat > temp_requirements.txt << EOF
Flask>=2.2.2
opencv-python>=4.5.0
numpy>=1.21.0
Jinja2>=3.1.0
Werkzeug>=2.2.0
Pillow>=9.0.0
EOF

# Install core dependencies (pip will skip if already satisfied)
print_status "Ensuring core dependencies are installed..."
pip install -r temp_requirements.txt --timeout 5 --verbose

# Try Raspberry Pi specific packages
if [ -f "/proc/device-tree/model" ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    print_status "Ensuring Raspberry Pi specific packages are installed..."
    pip install picamera2 RPi.GPIO gpiozero --timeout 5 --quiet || print_warning "Some Raspberry Pi packages failed to install, using mock interfaces"
else
    print_status "Non-Raspberry Pi system detected, skipping hardware-specific packages"
fi

# Clean up temporary file
rm -f temp_requirements.txt
print_success "Dependencies ready"

# Create necessary directories (safe to run multiple times)
print_status "Ensuring necessary directories exist..."
mkdir -p ~/wanda_captures
mkdir -p logs
print_success "Directories ready"

# Check if we're likely on a Raspberry Pi
if [ -f "/proc/device-tree/model" ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    print_status "Detected Raspberry Pi environment"
    # Check if camera is enabled
    if ! vcgencmd get_camera 2>/dev/null | grep -q "detected=1"; then
        print_warning "Camera may not be enabled. Enable with 'sudo raspi-config' if needed."
    fi
else
    print_status "Non-Raspberry Pi environment detected - using mock hardware interfaces"
fi

# Function to handle cleanup on script exit
cleanup() {
    print_status "Shutting down Wanda Telescope..."
    # Kill any background processes if needed
    jobs -p | xargs -r kill 2>/dev/null || true
    # Deactivate virtual environment if active
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        deactivate 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the application
print_success "Starting Wanda Telescope..."
print_status "Web interface will be available at: http://localhost:5000"
print_status "Press Ctrl+C to stop the application"

# Run the main application
python main.py