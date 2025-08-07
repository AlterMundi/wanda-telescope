#!/bin/bash

# WANDA Telescope Quick Start Script
# Fast startup for repeated runs - skips setup when environment is ready

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "WANDA Telescope Quick Start"
print_status "Working directory: $SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Running full setup..."
    exec ./run-wanda.sh
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Verify activation
if [ "$VIRTUAL_ENV" = "" ]; then
    print_warning "Failed to activate virtual environment. Running full setup..."
    exec ./run-wanda.sh
fi

print_success "Virtual environment activated: $VIRTUAL_ENV"

# Quick check for critical packages
print_status "Checking critical packages..."
if ! python3 -c "import flask, cv2" 2>/dev/null; then
    print_warning "Critical packages missing. Running full setup..."
    exec ./run-wanda.sh
fi

print_success "All critical packages available"

# Create captures directory if it doesn't exist
mkdir -p captures

# Display startup information
echo
print_success "=== WANDA Telescope Quick Start ==="
echo
print_status "System Information:"
print_status "  • Python: $(python3 --version)"
print_status "  • Virtual Environment: $VIRTUAL_ENV"
print_status "  • Working Directory: $SCRIPT_DIR"
print_status "  • Captures Directory: $SCRIPT_DIR/captures"
echo

# Start the application
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