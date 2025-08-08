#!/bin/bash

# WANDA Telescope Service Startup Script
# This script is designed to be run by systemd for automatic startup
# It handles environment setup, dependency checking, and graceful startup

set -e  # Exit on any error

# Service configuration
SERVICE_NAME="wanda-telescope"
LOG_FILE="/var/log/wanda-telescope.log"
LOCK_FILE="/tmp/wanda-telescope.lock"
PROJECT_DIR="/home/astro2/repos/wanda-telescope"
VENV_DIR="$PROJECT_DIR/venv"
USER="astro2"

# Colors for output (disabled for systemd journal)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Logging functions
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" | tee -a "$LOG_FILE" >&2
}

# Cleanup function
cleanup() {
    log_info "Service shutdown initiated"
    rm -f "$LOCK_FILE"
    log_info "Cleanup completed"
}

# Signal handlers
handle_sigterm() {
    log_info "Received SIGTERM, shutting down gracefully..."
    cleanup
    exit 0
}

handle_sighup() {
    log_info "Received SIGHUP, reloading configuration..."
    # Add any reload logic here if needed
}

# Set up signal handlers
trap handle_sigterm SIGTERM
trap handle_sighup SIGHUP
trap cleanup EXIT

# Pre-flight checks
preflight_checks() {
    log_info "Starting pre-flight checks..."
    
    # Check if another instance is running
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            log_error "Another instance is already running (PID: $pid)"
            exit 1
        else
            log_warning "Stale lock file found, removing..."
            rm -f "$LOCK_FILE"
        fi
    fi
    
    # Create lock file
    echo $$ > "$LOCK_FILE"
    
    # Check if we're running as the correct user
    if [ "$(whoami)" != "$USER" ]; then
        log_error "Service must run as user '$USER', currently running as '$(whoami)'"
        exit 1
    fi
    
    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi
    
    # Change to project directory
    cd "$PROJECT_DIR"
    log_success "Pre-flight checks completed"
}

# Wait for network connectivity
wait_for_network() {
    log_info "Waiting for network connectivity..."
    local timeout=60
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
            log_success "Network connectivity confirmed"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        log_info "Waiting for network... ($elapsed/$timeout seconds)"
    done
    
    log_warning "Network connectivity timeout, proceeding anyway"
    return 0
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Ensure we're in the project directory
    cd "$PROJECT_DIR"
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        log_error "Virtual environment not found: $VENV_DIR"
        log_error "Please run './run-wanda.sh' once to initialize the environment"
        exit 1
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    if [ "$VIRTUAL_ENV" != "$VENV_DIR" ]; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi
    
    log_success "Virtual environment activated: $VIRTUAL_ENV"
    
    # Set environment variables
    export PYTHONPATH="$PROJECT_DIR"
    export HOME="/home/$USER"
    
    # Quick dependency check
    if ! python3 -c "import flask, cv2, numpy" 2>/dev/null; then
        log_error "Critical dependencies missing. Please reinstall requirements."
        exit 1
    fi
    
    log_success "Environment setup completed"
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."
    
    # Create captures directory
    mkdir -p "$PROJECT_DIR/captures"
    
    # Create log directory if it doesn't exist
    sudo mkdir -p "$(dirname "$LOG_FILE")"
    sudo touch "$LOG_FILE"
    sudo chown "$USER:$USER" "$LOG_FILE"
    
    # Create wanda_captures in home directory
    mkdir -p "/home/$USER/wanda_captures"
    
    log_success "Directories setup completed"
}

# Hardware checks (Raspberry Pi specific)
hardware_checks() {
    log_info "Performing hardware checks..."
    
    # Check if we're on a Raspberry Pi
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        local pi_model=$(cat /proc/device-tree/model)
        log_success "Detected: $pi_model"
        
        # Check camera availability (non-blocking)
        if command -v libcamera-hello >/dev/null 2>&1; then
            if timeout 5 libcamera-hello --list-cameras 2>/dev/null | grep -q "Available cameras"; then
                log_success "Camera hardware detected"
            else
                log_warning "No camera detected - will use mock camera"
            fi
        else
            log_warning "libcamera tools not found - camera detection skipped"
        fi
        
        # Check GPIO access
        if [ -e /dev/gpiomem ]; then
            log_success "GPIO access available"
        else
            log_warning "GPIO access not available - mount control may not work"
        fi
    else
        log_info "Not running on Raspberry Pi - using mock implementations"
    fi
    
    log_success "Hardware checks completed"
}

# Main startup function
start_wanda() {
    log_info "Starting WANDA Telescope System..."
    
    # Run pre-startup script if it exists
    if [ -f "$PROJECT_DIR/scripts/pre-startup.sh" ]; then
        log_info "Running pre-startup script..."
        bash "$PROJECT_DIR/scripts/pre-startup.sh" || log_warning "Pre-startup script failed"
    fi
    
    # Start the main application
    log_success "🔭 Starting WANDA Telescope Web Server..."
    log_info "Web interface will be available at:"
    log_info "  • Local: http://localhost:5000"
    
    # Get the IP address for network access
    local ip_address=$(hostname -I | awk '{print $1}')
    if [ -n "$ip_address" ]; then
        log_info "  • Network: http://$ip_address:5000"
    fi
    
    # Execute the main application
    exec python3 main.py
}

# Main execution
main() {
    log_info "=== WANDA Telescope Service Starting ==="
    log_info "Service: $SERVICE_NAME"
    log_info "User: $(whoami)"
    log_info "PID: $$"
    log_info "Working Directory: $(pwd)"
    
    # Wait a bit for system to settle after boot
    log_info "Waiting for system initialization..."
    sleep 5
    
    # Execute startup sequence
    preflight_checks
    wait_for_network
    setup_directories
    setup_environment
    hardware_checks
    start_wanda
}

# Create log file if it doesn't exist
sudo mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || true
sudo touch "$LOG_FILE" 2>/dev/null || true
sudo chown "$USER:$USER" "$LOG_FILE" 2>/dev/null || true

# Start main execution
main "$@"