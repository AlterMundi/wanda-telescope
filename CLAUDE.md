# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WANDA (Wide-Angle Nightsky Digital Astrophotographer) is a Python-based astrophotography web application for Raspberry Pi. It provides a comprehensive web interface for controlling camera and equatorial mount for celestial object tracking.

## Common Development Commands

### Running the Application
```bash
# Automated setup and run (recommended)
./run-wanda.sh

# Manual run (if virtual environment already exists)
source venv/bin/activate
python main.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/web/          # Web interface tests only

# Run with coverage
pytest --cov=camera,mount,web,utils

# Run a single test file
pytest tests/unit/test_camera_base.py

# Run a specific test
pytest tests/unit/test_camera_base.py::test_abstract_camera_interface
```

### Development Environment
```bash
# Create virtual environment manually
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install pytest pytest-cov
```

## Architecture

### Core Design Patterns

1. **Factory Pattern**: Camera and Mount factories auto-detect hardware and create appropriate implementations
   - `camera/factory.py`: CameraFactory.create_camera() → PiCamera | USBCamera | MockCamera
   - `mount/factory.py`: MountFactory.create_mount() → PiMount | MockMount

2. **Abstract Base Classes**: Define interfaces for hardware components
   - `camera/base.py`: AbstractCamera - all cameras must implement this interface
   - `mount/base.py`: Abstract mount interface for tracking control

3. **Hardware Abstraction**: Mock implementations allow development without Raspberry Pi hardware
   - Development mode automatically falls back to mocks when Pi hardware unavailable
   - `dev_tools/` contains mock implementations of picamera2 and RPi.GPIO

### Key Components

**Camera System** (`camera/`):
- Supports Raspberry Pi HQ Camera (IMX-477), Arducam UC-955 (Pivariety), USB webcams, and mock cameras
- Automatic camera detection and fallback (Pi → USB → Mock)
- Advanced exposure control, ISO adjustment, night vision mode
- State preservation for non-intrusive operation

**Mount Control** (`mount/`):
- Stepper motor control for equatorial tracking
- Configurable tracking speed for sidereal rate
- Thread-safe operation with graceful shutdown

**Session Management** (`session/`):
- Automated capture sessions with progress tracking
- Thread-based implementation for non-blocking operation
- JSON metadata export for each session

**Web Interface** (`web/`):
- Flask-based REST API with AJAX frontend
- Real-time camera feed via MJPEG streaming
- Responsive design with collapsible control panels

## Important Implementation Details

### Camera State Management
The camera system preserves state to avoid disrupting other applications:
- Camera controls are restored to original values after use
- Proper cleanup on application shutdown via signal handlers
- Thread-safe operations for concurrent access

### Storage Hierarchy
Storage locations are checked in order:
1. USB drive (if mounted at /media/*)
2. User home directory (~/wanda_captures)
3. Current directory fallback

### Error Handling
- Camera exceptions in `camera/exceptions.py`
- Mount exceptions follow similar pattern
- Web routes return appropriate HTTP status codes with error messages

### Testing Strategy
- Comprehensive fixtures in `tests/conftest.py`
- Mock hardware for CI/CD compatibility
- Integration tests verify component interactions
- Web tests use Flask test client

## Configuration

Main configuration in `config.py`:
- Camera settings (resolution, exposure limits, gain ranges)
- Mount settings (GPIO pins, step sequences, tracking speeds)
- Storage paths and web server settings
- All settings have sensible defaults

## Development Tips

1. **Running without hardware**: The application automatically uses mock implementations when Pi hardware is unavailable
2. **Camera testing**: Use MOCK_CAMERA environment variable to force mock camera even on Pi
3. **Mount testing**: Mock mount allows testing tracking logic without stepper motor
4. **Web development**: Frontend uses vanilla JavaScript with AJAX for simplicity
5. **Session testing**: Mock implementations support full session workflows

## Camera Hardware Support

### Arducam UC-955 (Pivariety) Setup
For Arducam UC-955 camera modules, special driver installation is required. See `docs/ARDUCAM_UC955_SETUP.md` for complete setup instructions including:
- Official Arducam Pivariety driver installation
- Device tree overlay configuration (`dtoverlay=arducam-pivariety`)
- Required tuning file setup for libcamera compatibility
- Verification and troubleshooting steps

The UC-955 provides 1920x1080 @ 60fps with 10-bit RGGB color depth and integrates seamlessly with WANDA's camera factory system.