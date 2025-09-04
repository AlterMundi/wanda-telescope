# WANDA Telescope

An open-source Raspberry Pi-based astrophotography system featuring an equatorial mount with automated star tracking capabilities and a comprehensive web interface.

## Overview

WANDA (Wide-Angle Nightsky Digital Astrophotographer) is a Python-based astrophotography web application designed for Raspberry Pi. It provides a complete solution for controlling camera and equatorial mount systems for celestial object tracking, with support for multiple camera types and automated startup.

## Features

- **Multi-Camera Support**: Automatic detection and support for Pi Camera, USB cameras, and mock cameras
- **Automated Star Tracking**: Equatorial mount control with configurable tracking speeds
- **Modern Web Interface**: Responsive Flask-based REST API with AJAX frontend
- **Advanced Camera Control**: Exposure, ISO, gain adjustment, and night vision mode
- **Session Management**: Automated capture sessions with progress tracking and metadata export
- **Auto-Startup**: Systemd service for automatic startup on boot
- **Hardware Abstraction**: Mock implementations for development without physical hardware
- **State Preservation**: Non-intrusive camera operation with state restoration
- **Storage Management**: Automatic USB drive detection and fallback storage

## Hardware Support

### Camera Systems
- **Raspberry Pi HQ Camera (IMX-477)**: Native libcamera/picamera2 integration
- **Arducam UC-955 (Pivariety)**: High-performance IMX477-based camera
- **USB Cameras**: Any UVC-compatible webcam with OpenCV support
- **Mock Camera**: Development and testing without hardware

### Mount Control
- **Stepper Motor Control**: Configurable GPIO pins and step sequences
- **Tracking Speed**: Adjustable for sidereal rate and custom speeds
- **Mock Mount**: Testing mount logic without physical hardware


### Manual Setup

Manual installation for Raspberry Pi with IMX477 camera:

```bash

## Update system
sudo apt update
sudo apt upgrade

## Configure camera sensor (IMX477)
sudo nano /boot/firmware/config.txt

# Add these lines under the [all] section:
# Disable camera autodetection:
camera_auto_detect=0

# Enable IMX477 camera under the [all] section:
dtoverlay=imx477

#For Pi 5 with cameras connected to CAM0 port, use: 
dtoverlay=imx477,cam0

# Save and exit, then reboot
sudo reboot

## Test camera detection after reboot
rpicam-still --list-cameras

## Install system dependencies
# Note: python3-picamera2 must be installed as system package before creating venv
sudo apt install git python3-libcamera python3-picamera2

## Clone repository
git clone https://github.com/AlterMundi/wanda-telescope.git
cd wanda-telescope

## Create virtual environment with system package access
# (Required for picamera2 which is installed as system package)
# Note: Without --system-site-packages, venv cannot access picamera2
python3 -m venv --system-site-packages venv
source venv/bin/activate

## Install Python dependencies
pip install -r requirements.txt

## Run WANDA
python main.py
```

## Architecture

### Core Design Patterns

#### 1. Factory Pattern Implementation
- **Camera Factory**: `camera/factory.py` - Auto-detects hardware and creates appropriate implementations
- **Mount Factory**: `mount/factory.py` - Creates mount implementations based on available hardware

#### 2. Abstract Base Classes
- **Camera Interface**: `camera/base.py` - AbstractCamera defines required interface
- **Mount Interface**: `mount/base.py` - Abstract mount interface for tracking control

#### 3. Hardware Abstraction
- Mock implementations allow development without Raspberry Pi hardware
- Development mode automatically falls back to mocks when Pi hardware unavailable
- `dev_tools/` contains mock implementations of picamera2 and RPi.GPIO

### Key Components

#### Camera System (`camera/`)
- Supports multiple camera types with automatic fallback
- Advanced exposure control, ISO adjustment, night vision mode
- State preservation for non-intrusive operation
- Retry logic with detailed error diagnostics

#### Mount Control (`mount/`)
- Stepper motor control for equatorial tracking
- Configurable tracking speed for sidereal rate
- Thread-safe operation with graceful shutdown

#### Session Management (`session/`)
- Automated capture sessions with progress tracking
- Thread-based implementation for non-blocking operation
- JSON metadata export for each session

#### Web Interface (`web/`)
- Flask-based REST API with AJAX frontend
- Real-time camera feed via MJPEG streaming
- Responsive design with collapsible control panels
- Modern UI with intuitive controls

## Usage

### Web Interface

Access WANDA through any web browser on your network:
- **Local access**: `http://localhost:5000`
- **Network access**: `http://[PI_IP]:5000`

#### Camera Controls
- **Live Preview**: Real-time camera feed with MJPEG streaming
- **Exposure Settings**: 1/10000s to 200s with fine control
- **ISO Adjustment**: 20-1600 range for optimal light sensitivity
- **Night Vision Mode**: Enhanced sensitivity for low-light conditions
- **RAW Capture**: Option to save RAW files for post-processing
- **Performance Tuning**: CPU usage optimization

#### Mount Controls
- **Tracking Speed**: Configurable for different celestial objects
- **Direction Control**: Clockwise/counterclockwise movement
- **Start/Stop Tracking**: Manual control of mount operation

#### Session Management
- **Automated Captures**: Set up timed capture sessions
- **Progress Tracking**: Real-time session status and completion
- **Metadata Export**: JSON files with capture information

### Taking Photos

1. **Configure camera settings** using the Camera panel
2. **Start mount tracking** if following celestial objects
3. **Click "Capture Photo"** - interface shows progress
4. **Files are saved** with automatic storage management

### Recording Videos

1. **Set up recording parameters** in camera controls
2. **Click "Start Video"** to begin recording
3. **Click "Stop Video"** when finished
4. **Videos are saved** as H.264 files

## Storage Management

WANDA automatically manages storage with intelligent fallback:
1. **USB Drive**: If mounted at `/media/*`, captures are saved there
2. **Home Directory**: Falls back to `~/wanda_captures`
3. **Current Directory**: Final fallback for development

## Development

### Test-Driven Development (TDD)
- **Always work using TDD methodology**: Write tests first, then implement code
- **No implementation without tests**: Every new feature must have corresponding tests
- **Test coverage requirement**: Aim for at least 85% code coverage
- **Comprehensive testing**: Include positive, negative, and edge case tests

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest tests/ --cov=camera.implementations --cov=camera.factory --cov=main --cov=web.app --cov=session.controller --cov-report=term-missing --cov-report=term --tb=short


```

### Development Environment
```bash
# Create virtual environment with system package access
# (Required for picamera2 on Raspberry Pi)
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov

# Run WANDA in development mode
python main.py
```

## File Structure

```
wanda-telescope/
├── main.py                    # Application entry point
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── pytest.ini               # Pytest configuration
├── run_tests_with_coverage.sh # Test runner script
├── camera/                    # Camera system modules
│   ├── __init__.py           # Camera package initialization
│   ├── base.py               # Abstract camera interface
│   ├── factory.py            # Camera factory and detection
│   └── implementations/      # Camera implementations
│       ├── __init__.py       # Implementations package init
│       ├── pi_camera.py      # Raspberry Pi camera
│       ├── usb_camera.py     # USB camera support
│       └── mock_camera.py    # Mock camera for development
├── mount/                     # Mount control system
│   ├── __init__.py           # Mount package initialization
│   ├── base.py               # Abstract mount interface
│   ├── factory.py            # Mount factory
│   ├── controller.py         # Mount controller logic
│   └── implementations/      # Mount implementations
│       ├── pi_mount.py       # Raspberry Pi GPIO mount
│       └── mock_mount.py     # Mock mount for development
├── session/                   # Session management
│   ├── __init__.py           # Session package initialization
│   └── controller.py         # Session controller
├── web/                       # Web interface
│   ├── __init__.py           # Web package initialization
│   ├── app.py                # Flask application
│   ├── templates/            # HTML templates
│   │   ├── base.html         # Base template
│   │   ├── index.html        # Main page
│   │   └── components/       # Reusable components
│   │       ├── camera-controls.html
│   │       ├── mount-controls.html
│   │       └── session-controls.html
│   └── static/               # Static assets
│       ├── css/              # Stylesheets
│       │   ├── main.css
│       │   ├── components.css
│       │   └── modern-ui.css
│       ├── js/               # JavaScript files
│       │   ├── ajax-utils.js
│       │   ├── camera-controls.js
│       │   ├── modern-ui.js
│       │   ├── mount-controls.js
│       │   ├── session-controls.js
│       │   └── utils.js
│       └── img/              # Images
│           └── favicon.ico
├── utils/                     # Utility functions
│   ├── __init__.py           # Utils package initialization
│   └── storage.py            # Storage management
├── dev_tools/                 # Development tools
│   └── __init__.py           # Dev tools package initialization
├── docs/                      # Documentation
│   ├── ARDUCAM_UC955_SETUP.md
│   ├── AUTO_STARTUP_README.md
│   ├── camera_state_restoration.md
│   ├── DEV_DEPLOYMENT.md
│   ├── NETWORK_DISCOVERY.md
│   ├── RASPBERRY_PI_ECOSYSTEM_LIMITATIONS.md
│   └── test_capture_isolation.md
├── tests/                     # Test suite
│   ├── __init__.py           # Tests package initialization
│   ├── test_main.py          # Main application tests
│   ├── test_camera/          # Camera system tests
│   │   ├── __init__.py
│   │   ├── test_camera_factory.py
│   │   └── test_implementations/
│   │       ├── __init__.py
│   │       ├── test_pi_camera.py
│   │       ├── test_usb_camera.py
│   │       └── captures/     # Test capture files
│   ├── test_session/         # Session management tests
│   │   ├── __init__.py
│   │   └── test_controller.py
│   └── test_web/             # Web interface tests
│       ├── __init__.py
│       └── test_app.py
├── scripts/                   # Deployment and utility scripts
│   ├── announce-ip.sh        # Network discovery announcement
│   ├── deploy-to-pi.sh       # Legacy one-command deployment
│   ├── find-wanda.py         # Network discovery finder
│   ├── install-service.sh    # Service installation
│   ├── install.sh            # One-command installation
│   ├── post-install.sh       # Post-installation verification
│   ├── quick-start.sh        # Quick start script
│   ├── run-wanda.sh          # Development runner
│   ├── uninstall-service.sh  # Service uninstallation
│   └── wanda-service.sh      # Service definition
├── captures/                  # Captured images directory
├── htmlcov/                   # Coverage report output
├── venv/                      # Virtual environment
└── session_metadata.json     # Session metadata storage
```

## License

This project is open-source. Please ensure you provide appropriate attribution when using or modifying this code.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Join discussions in GitHub Discussions

---

**WANDA Telescope** - Making astrophotography accessible to everyone! 🔭✨