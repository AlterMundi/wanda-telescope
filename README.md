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

## Quick Start

### One-Command Deployment (Recommended)

The easiest way to get WANDA running on a fresh Raspberry Pi OS Lite:

```bash
curl -sSL https://raw.githubusercontent.com/AlterMundi/wanda-telescope/main/scripts/deploy-to-pi.sh | bash
```

This single command will:
- ✅ Install all system dependencies (OpenCV, Pi camera libraries, GPIO)
- ✅ Clone the WANDA Telescope repository
- ✅ Set up Python virtual environment
- ✅ Install all Python dependencies
- ✅ Configure systemd service for auto-startup
- ✅ Start WANDA Telescope automatically
- ✅ Enable auto-startup on boot

### Manual Setup (Alternative)

If you prefer manual installation:

```bash
# Clone repository
git clone https://github.com/AlterMundi/wanda-telescope.git
cd wanda-telescope

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run WANDA
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
pytest --cov=camera,mount,web,utils

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/web/          # Web interface tests
```

### Development Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov

# Run WANDA in development mode
python main.py
```

## Configuration

Main configuration in `config.py`:
- **Camera settings**: Resolution, exposure limits, gain ranges
- **Mount settings**: GPIO pins, step sequences, tracking speeds
- **Storage paths**: Capture directories and USB drive preferences
- **Web server settings**: Host address, port number, debug mode

## Service Management

### Auto-Startup
WANDA automatically starts on boot via systemd service:
```bash
# Check service status
sudo systemctl status wanda-telescope

# View logs
sudo journalctl -u wanda-telescope -f

# Restart service
sudo systemctl restart wanda-telescope

# Disable auto-startup
sudo systemctl disable wanda-telescope
```

### Manual Control
```bash
# Start manually
cd ~/wanda-telescope
source venv/bin/activate
python main.py

# Stop service
sudo systemctl stop wanda-telescope
```

## File Structure

```
wanda-telescope/
├── main.py                    # Application entry point
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── camera/                    # Camera system modules
│   ├── base.py               # Abstract camera interface
│   ├── factory.py            # Camera factory and detection
│   ├── exceptions.py         # Camera-specific exceptions
│   └── implementations/      # Camera implementations
│       ├── pi_camera.py      # Raspberry Pi camera
│       ├── usb_camera.py     # USB camera support
│       └── mock_camera.py    # Mock camera for development
├── mount/                     # Mount control system
│   ├── base.py               # Abstract mount interface
│   ├── factory.py            # Mount factory
│   ├── controller.py         # Mount controller logic
│   └── implementations/      # Mount implementations
│       ├── pi_mount.py       # Raspberry Pi GPIO mount
│       └── mock_mount.py     # Mock mount for development
├── session/                   # Session management
│   ├── controller.py         # Session controller
│   └── exceptions.py         # Session exceptions
├── web/                       # Web interface
│   ├── app.py                # Flask application
│   ├── templates/            # HTML templates
│   └── static/               # CSS, JavaScript, images
├── utils/                     # Utility functions
│   └── storage.py            # Storage management
├── dev_tools/                 # Development tools
│   ├── mock_picamera2.py     # Mock picamera2
│   └── mock_rpi_gpio.py      # Mock RPi.GPIO
├── tests/                     # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── web/                  # Web interface tests
└── scripts/                   # Deployment and utility scripts
    ├── deploy-to-pi.sh       # One-command deployment
    ├── install-service.sh     # Service installation
    └── run-wanda.sh          # Development runner
```

## Troubleshooting

### Common Issues

#### Camera Detection Problems
```bash
# Check camera detection
python3 -c "from camera.factory import CameraFactory; print(CameraFactory.detect_camera())"

# Verify Pi camera connection
vcgencmd get_camera

# Check USB camera
lsusb | grep -i camera
```

#### Service Issues
```bash
# Check service logs
sudo journalctl -u wanda-telescope -f

# Verify service configuration
sudo systemctl cat wanda-telescope

# Test manual startup
cd ~/wanda-telescope && source venv/bin/activate && python main.py
```

#### Network Access
- Ensure Pi and device are on same network
- Check firewall settings
- Verify port 5000 is accessible
- Use `hostname -I` to find Pi's IP address

### Performance Optimization
- Use USB 3.0 for external storage
- Enable GPU memory split for Pi camera
- Optimize camera resolution for your use case
- Monitor CPU usage during capture sessions

## Contributing

We welcome contributions! Please follow our development guidelines:

1. **Fork the repository** and create a feature branch
2. **Write tests first** following TDD methodology
3. **Ensure test coverage** meets 85% minimum
4. **Follow code quality standards** (simplicity, no duplication)
5. **Submit a pull request** with clear description

### Development Setup
```bash
# Fork and clone
git clone https://github.com/yourusername/wanda-telescope.git
cd wanda-telescope

# Create feature branch
git checkout -b feat/your-feature

# Set up development environment
./scripts/run-wanda.sh --setup-only

# Run tests
pytest

# Make changes and test
# Submit pull request
```

## License

This project is open-source. Please ensure you provide appropriate attribution when using or modifying this code.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Join discussions in GitHub Discussions

---

**WANDA Telescope** - Making astrophotography accessible to everyone! 🔭✨