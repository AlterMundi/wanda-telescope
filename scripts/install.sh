#!/bin/bash

# WANDA Telescope Installation Script
# This script installs WANDA Telescope on a fresh Raspberry Pi OS Lite
# Usage: curl -sSL https://raw.githubusercontent.com/AlterMundi/wanda-telescope/main/scripts/install.sh | bash

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
    print_info "🔭 WANDA Telescope - Installation Script"
    print_info "========================================="
    print_info "This script will install WANDA Telescope on your Pi"
    print_info "Branch: $BRANCH"
    print_info "Target: $PROJECT_DIR"
    print_info "User: $USER"
    echo
}

check_system() {
    print_step "1/6: Checking system requirements..."
    
    # Check system clock first - this is critical for package operations
    print_info "Checking system clock..."
    local current_year=$(date '+%Y' 2>/dev/null || echo "0")
    if [ "$current_year" -lt "2020" ] || [ "$current_year" -gt "2030" ]; then
        print_warning "System clock appears to be severely incorrect: year $current_year"
        print_info "This will prevent package installation. Attempting immediate correction..."
        
        # Try to set a reasonable date immediately
        local current_month=$(date '+%m' 2>/dev/null || echo "01")
        local current_day=$(date '+%d' 2>/dev/null || echo "01")
        
        if sudo date -s "2024-$current_month-$current_day" >/dev/null 2>&1; then
            print_success "Corrected system date to: 2024-$current_month-$current_day"
        elif sudo date -s "2025-$current_month-$current_day" >/dev/null 2>&1; then
            print_success "Corrected system date to: 2025-$current_month-$current_day"
        else
            print_error "Cannot correct system date. Installation will fail."
            print_info "Please manually set the system date before continuing."
            print_info "You can use: sudo date -s '$(date -u)' to set UTC time"
            exit 1
        fi
    else
        print_success "System clock appears to be correct: year $current_year"
    fi
    
    # Check network connectivity
    print_info "Checking network connectivity..."
    if ! ping -c 1 github.com >/dev/null 2>&1; then
        print_error "No internet connection. Please check your network and try again."
        exit 1
    fi
    
    # Check for broken packages and fix them
    print_info "Checking for broken packages..."
    if dpkg -l | grep -q "^iU\|^rc"; then
        print_warning "Found broken packages, attempting to fix..."
        sudo apt --fix-broken install -y || true
        sudo dpkg --configure -a || true
    fi
    
    print_success "Network connectivity confirmed"
    
    # Check available disk space (need at least 2GB free)
    print_info "Checking available disk space..."
    local available_space=$(df / | awk 'NR==2 {print $4}')
    local required_space=2097152  # 2GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        print_error "Insufficient disk space. Need at least 2GB free, but only $(($available_space / 1024))MB available."
        print_info "Please free up some space and try again."
        exit 1
    fi
    print_success "Disk space check passed ($(($available_space / 1024))MB available)"
    
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

sync_system_clock() {
    print_step "1.5/6: Synchronizing system clock..."
    
    # Check if system clock is significantly off
    print_info "Checking system clock..."
    local current_date=$(date '+%Y-%m-%d')
    
    # Try multiple time sources for redundancy
    local expected_date=""
    local time_sources=(
        "https://worldtimeapi.org/api/timezone/UTC"
        "https://www.google.com"
        "https://httpbin.org/headers"
    )
    
    for source in "${time_sources[@]}"; do
        if [ "$source" = "https://www.google.com" ]; then
            # Extract date from HTTP headers
            local http_date=$(curl -s --connect-timeout 5 -I "$source" | grep "^Date:" | cut -d' ' -f2-)
            if [ -n "$http_date" ]; then
                expected_date=$(date -d "$http_date" '+%Y-%m-%d' 2>/dev/null || echo "")
                if [ -n "$expected_date" ]; then
                    print_info "Got date from HTTP headers: $expected_date"
                    break
                fi
            fi
        else
            # Try JSON API
            local api_date=$(curl -s --connect-timeout 5 "$source" | grep -o '"datetime":"[^"]*"' | cut -d'"' -f4 | cut -d'T' -f1 2>/dev/null || echo "")
            if [ -n "$api_date" ]; then
                expected_date="$api_date"
                print_info "Got date from API: $expected_date"
                break
            fi
        fi
    done
    
    if [ -n "$expected_date" ] && [ "$current_date" != "$expected_date" ]; then
        print_warning "System clock appears to be off. Current: $current_date, Expected: $expected_date"
        print_info "Attempting to synchronize clock..."
        
        # Try to install ntpdate if available, otherwise use rdate
        if command -v ntpdate >/dev/null 2>&1; then
            print_info "Using ntpdate to sync clock..."
            if sudo ntpdate -s time.nist.gov; then
                print_success "Clock synchronized using ntpdate"
            else
                print_warning "ntpdate failed, trying alternative method..."
            fi
        fi
        
        # Alternative: try to set date from HTTP headers
        if ! command -v ntpdate >/dev/null 2>&1 || [ $? -ne 0 ]; then
            print_info "Attempting to sync clock using HTTP headers..."
            local http_date=$(curl -s --connect-timeout 10 -I https://www.google.com | grep "^Date:" | cut -d' ' -f2-)
            if [ -n "$http_date" ]; then
                print_info "Setting date from HTTP headers: $http_date"
                if sudo date -s "$http_date" >/dev/null 2>&1; then
                    print_success "Clock synchronized using HTTP headers"
                else
                    print_warning "Failed to set date from HTTP headers"
                fi
            fi
        fi
        
        # Final check - if still off, try to install and use ntpdate
        if ! command -v ntpdate >/dev/null 2>&1; then
            print_info "Installing ntpdate for clock synchronization..."
            if sudo apt update -qq >/dev/null 2>&1; then
                if sudo apt install -y ntpdate >/dev/null 2>&1; then
                    print_info "ntpdate installed, syncing clock..."
                    if sudo ntpdate -s time.nist.gov; then
                        print_success "Clock synchronized using newly installed ntpdate"
                    else
                        print_warning "ntpdate sync failed"
                    fi
                else
                    print_warning "Failed to install ntpdate"
                fi
            else
                print_warning "Package update failed, trying manual date correction..."
                
                # Last resort: try to estimate and set a reasonable date
                # This is a fallback for when the system clock is completely wrong
                local estimated_year=$(date '+%Y' 2>/dev/null || echo "2024")
                if [ "$estimated_year" -lt "2020" ] || [ "$estimated_year" -gt "2030" ]; then
                    print_warning "System year appears to be wrong: $estimated_year"
                    print_info "Attempting to set a reasonable date..."
                    
                    # Try to set to current year (we know it's 2024-2025)
                    local current_month=$(date '+%m' 2>/dev/null || echo "01")
                    local current_day=$(date '+%d' 2>/dev/null || echo "01")
                    
                    if sudo date -s "2024-$current_month-$current_day" >/dev/null 2>&1; then
                        print_success "Set reasonable date: 2024-$current_month-$current_day"
                    elif sudo date -s "2025-$current_month-$current_day" >/dev/null 2>&1; then
                        print_success "Set reasonable date: 2025-$current_month-$current_day"
                    else
                        print_warning "Failed to set reasonable date, continuing with current clock"
                    fi
                fi
            fi
        fi
        
        # Additional fallback: if we still can't get the right date, try to force a reasonable one
        # This is specifically for cases where the system clock is completely broken
        local final_year=$(date '+%Y' 2>/dev/null || echo "0")
        if [ "$final_year" -lt "2020" ] || [ "$final_year" -gt "2030" ]; then
            print_warning "System clock is still incorrect after all attempts"
            print_info "Forcing a reasonable date to allow package installation..."
            
            # Get current month and day, but force a reasonable year
            local current_month=$(date '+%m' 2>/dev/null || echo "01")
            local current_day=$(date '+%d' 2>/dev/null || echo "01")
            local current_hour=$(date '+%H' 2>/dev/null || echo "12")
            local current_minute=$(date '+%M' 2>/dev/null || echo "00")
            local current_second=$(date '+%S' 2>/dev/null || echo "00")
            
            # Try to set a reasonable date and time
            if sudo date -s "2024-$current_month-$current_day $current_hour:$current_minute:$current_second" >/dev/null 2>&1; then
                print_success "Forced reasonable date: 2024-$current_month-$current_day $current_hour:$current_minute:$current_second"
            elif sudo date -s "2025-$current_month-$current_day $current_hour:$current_minute:$current_second" >/dev/null 2>&1; then
                print_success "Forced reasonable date: 2025-$current_month-$current_day $current_hour:$current_minute:$current_second"
            else
                print_error "Cannot set any reasonable date. Installation may fail."
                print_info "You may need to manually set the system date before continuing."
            fi
        fi
    else
        print_success "System clock appears to be correct: $current_date"
    fi
    
    # Show current time for verification
    print_info "Current system time: $(date)"
    
    # Final verification that we have a reasonable date
    local current_year=$(date '+%Y' 2>/dev/null || echo "0")
    if [ "$current_year" -lt "2020" ] || [ "$current_year" -gt "2030" ]; then
        print_warning "System date still appears to be incorrect: $(date)"
        print_info "This may cause package installation issues."
        echo
        print_info "Options:"
        print_info "  1. Continue with installation (may fail)"
        print_info "  2. Exit and fix date manually"
        echo
        read -p "Choose option (1 or 2): " date_choice
        
        case $date_choice in
            1)
                print_warning "Continuing with potentially incorrect date..."
                ;;
            2)
                print_info "Exiting. Please fix the system date manually and run the script again."
                print_info "You can use: sudo date -s '$(date -u)' to set UTC time"
                exit 1
                ;;
            *)
                print_error "Invalid choice. Exiting."
                exit 1
                ;;
        esac
    else
        print_success "System date appears to be correct"
    fi
    
    print_success "Clock synchronization completed"
}

install_system_dependencies() {
    print_step "2/6: Installing system dependencies..."
    
    # Update package list
    print_info "Updating package list..."
    
    # Try to update package list with retry logic
    local max_retries=3
    local retry_count=0
    local update_success=false
    
    while [ $retry_count -lt $max_retries ] && [ "$update_success" = false ]; do
        if sudo apt update -qq; then
            update_success=true
            print_success "Package list updated successfully"
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                print_warning "Package update failed (attempt $retry_count/$max_retries)"
                print_info "This might be due to clock synchronization issues. Retrying..."
                
                # Try to sync clock again
                if command -v ntpdate >/dev/null 2>&1; then
                    print_info "Re-syncing clock..."
                    sudo ntpdate -s time.nist.gov >/dev/null 2>&1 || true
                fi
                
                sleep 2
            else
                print_error "Failed to update package list after $max_retries attempts"
                print_info "This might be due to network issues or repository problems."
                print_info "Trying to continue with existing package list..."
                
                # Try to continue with existing package list
                if sudo apt list --upgradable >/dev/null 2>&1; then
                    print_warning "Continuing with existing package list"
                    update_success=true
                else
                    print_error "Cannot continue without package list update"
                    
                    # Last resort: try to force a package list update by ignoring date issues
                    print_info "Attempting to force package list update..."
                    if sudo apt update -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false -qq >/dev/null 2>&1; then
                        print_success "Forced package list update successful"
                        update_success=true
                    else
                        print_error "All package update methods failed"
                        print_info "This installation cannot proceed without package updates."
                        print_info "Please check your system clock and network connectivity."
                        exit 1
                    fi
                fi
            fi
        fi
    done
    
    # Upgrade existing packages
    print_info "Upgrading existing packages..."
    if sudo apt upgrade -y -qq; then
        print_success "System packages upgraded successfully"
    else
        print_warning "Some packages could not be upgraded - continuing with installation"
        # Try to fix any broken packages
        sudo apt --fix-broken install -y >/dev/null 2>&1 || true
    fi
    
    # Install only essential packages for WANDA Telescope
    print_info "Installing essential packages..."
    if ! sudo apt install -y -qq \
        git \
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
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libgstreamer1.0-dev \
        libgstreamer-plugins-base1.0-dev \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-tools; then
        
        print_error "Failed to install system packages"
        print_info "Attempting to fix broken packages..."
        sudo apt --fix-broken install -y || true
        sudo dpkg --configure -a || true
        exit 1
    fi
    
    # Install Pi-specific packages if on Raspberry Pi
    if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        print_info "Installing Raspberry Pi specific packages..."
        if ! sudo apt install -y -qq \
            python3-picamera2 \
            python3-libcamera \
            python3-rpi.gpio \
            python3-gpiozero \
            libraspberrypi-dev \
            libraspberrypi-bin; then
            
            print_warning "Failed to install some Pi-specific packages - will use mock implementations"
        fi
    fi
    
    print_success "System dependencies installed"
}

setup_directories() {
    print_step "3/6: Setting up project directories..."
    
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
    print_step "4/6: Cloning WANDA Telescope repository..."
    
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
    print_step "5/6: Setting up Python environment..."
    
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
    
    # Note: Pi camera dependencies (picamera2, libcamera) are installed as system packages above
    # The virtual environment will access them via sys.path modification in the code
    
    print_success "Python environment setup completed"
}

install_systemd_service() {
    print_step "6/6: Installing systemd service..."
    
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

show_completion_info() {
    print_step "Installation complete!"
    
    echo
    print_success "🎉 WANDA Telescope Installation Complete!"
    echo
    print_info "Installation Summary:"
    print_info "  ✓ System dependencies installed"
    print_info "  ✓ Python virtual environment created"
    print_info "  ✓ WANDA Telescope repository cloned"
    print_info "  ✓ Python dependencies installed"
    print_info "  ✓ Systemd service configured and enabled"
    echo
    print_info "Next Steps:"
    print_info "  1. The system will reboot in 10 seconds to start WANDA Telescope"
    print_info "  2. After reboot, WANDA will start automatically"
    print_info "  3. Run post-install.sh to verify everything is working correctly"
    echo
    print_info "Service Information:"
    print_info "  • Service: wanda-telescope (enabled for auto-start)"
    print_info "  • Working Directory: $PROJECT_DIR"
    print_info "  • User: $USER"
    echo
    print_info "Post-Installation:"
    print_info "  • Run: ./scripts/post-install.sh"
    print_info "  • This will verify the service is running and accessible"
    echo
}

# Cleanup function for error handling
cleanup_on_error() {
    print_error "Installation failed! Cleaning up..."
    
    # Remove service file if it exists
    if [ -f /etc/systemd/system/wanda-telescope.service ]; then
        print_info "Removing systemd service file..."
        sudo rm -f /etc/systemd/system/wanda-telescope.service
        sudo systemctl daemon-reload 2>/dev/null || true
    fi
    
    print_error "Cleanup completed. Please check the error messages above and try again."
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run this script as root. Run as the user that will operate WANDA."
    exit 1
fi

# Check if this is a reinstallation
if [ -d "$HOME/wanda-telescope" ] || sudo systemctl list-unit-files | grep -q "wanda-telescope"; then
    print_warning "WANDA Telescope appears to be already installed!"
    echo
    print_info "Options:"
    print_info "  1. Clean reinstall (remove existing installation and start fresh)"
    print_info "  2. Exit and keep existing installation"
    echo
    read -p "Choose option (1 or 2): " choice
    
    case $choice in
        1)
            print_info "Performing clean reinstall..."
            cleanup_existing_installation
            ;;
        2)
            print_info "Exiting. No changes made."
            exit 0
            ;;
        *)
            print_error "Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

# Cleanup function for existing installations
cleanup_existing_installation() {
    print_info "Cleaning up existing WANDA installation..."
    
    # Stop and disable service
    if sudo systemctl is-active wanda-telescope >/dev/null 2>&1; then
        print_info "Stopping wanda-telescope service..."
        sudo systemctl stop wanda-telescope
    fi
    
    if sudo systemctl is-enabled wanda-telescope >/dev/null 2>&1; then
        print_info "Disabling wanda-telescope service..."
        sudo systemctl disable wanda-telescope
    fi
    
    # Remove service file
    if [ -f /etc/systemd/system/wanda-telescope.service ]; then
        print_info "Removing systemd service file..."
        sudo rm -f /etc/systemd/system/wanda-telescope.service
        sudo systemctl daemon-reload
    fi
    
    # Remove project directory
    if [ -d "$HOME/wanda-telescope" ]; then
        print_info "Removing project directory..."
        rm -rf "$HOME/wanda-telescope"
    fi
    
    # Clean up any broken packages
    print_info "Cleaning up package system..."
    sudo apt autoremove -y
    sudo apt autoclean
    
    print_success "Cleanup completed. Ready for fresh installation."
    echo
}

# Main installation process
main() {
    # Set trap for error handling
    trap cleanup_on_error ERR
    
    print_banner
    check_system
    sync_system_clock
    install_system_dependencies
    setup_directories
    clone_repository
    setup_python_environment
    install_systemd_service
    show_completion_info
    
    # Clear trap on successful completion
    trap - ERR
    
    # Prompt for reboot
    echo
    print_info "System will reboot in 10 seconds to start WANDA Telescope..."
    print_info "Press Ctrl+C to cancel reboot and reboot manually later"
    echo
    
    # Countdown and reboot
    for i in {10..1}; do
        echo -n "Rebooting in $i seconds... "
        sleep 1
        echo "✓"
    done
    
    print_info "Rebooting now..."
    sudo reboot
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

# Check for required commands
for cmd in git python3 pip3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        print_warning "Command '$cmd' not found - will be installed during setup"
    fi
done

# Run main installation
main "$@"
