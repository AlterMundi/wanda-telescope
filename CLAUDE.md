# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Platform Usage

- Use this file when working with Claude Code (claude.ai/code). It contains the authoritative rules and guidance for Claude.
- Cursor users should not rely on this file. Instead, use the modular rules under `.cursor/rules/` where `base.mdc` is always applied and context-specific `.mdc` files (e.g., `hardware.mdc`, `web-api.mdc`) can be enabled as needed.

## Project Overview

WANDA (Wide-Angle Nightsky Digital Astrophotographer) is a Python-based astrophotography web application for Raspberry Pi. It provides a comprehensive web interface for controlling camera and equatorial mount for celestial object tracking.

## Common Development Commands

### Running the Application
```bash
# Create virtual environment if not exists
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=camera,mount,web,utils,session --cov-report=term-missing

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/web/          # Web interface tests only

# Run a single test file
pytest tests/unit/test_camera/test_camera_factory.py

# Run a specific test
pytest tests/unit/test_camera/test_camera_factory.py::test_factory_creates_mock_camera

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
```

### Development Environment
```bash
# Install development dependencies
pip install pytest pytest-cov pytest-mock pytest-flask responses

# Force mock camera (useful for development without hardware)
export MOCK_CAMERA=1
python main.py

# Check code coverage
pytest --cov=camera,mount,web,utils,session --cov-report=html
# Open htmlcov/index.html in browser
```

## Architecture

### Core Design Patterns

1. **Factory Pattern**: Camera and Mount factories auto-detect hardware and create appropriate implementations
   - `camera/factory.py`: CameraFactory.create_camera() → PiCamera | USBCamera | MockCamera
   - `mount/factory.py`: MountFactory.create_mount() → PiMount | MockMount
   - Detection priority: Pi hardware → USB hardware → Mock fallback

2. **Abstract Base Classes**: Define interfaces for hardware components
   - `camera/base.py`: AbstractCamera - all cameras must implement capture_image, capture_video, etc.
   - `mount/base.py`: AbstractMount - defines tracking control interface
   - Ensures consistent API across different hardware implementations

3. **Hardware Abstraction**: Mock implementations allow development without Raspberry Pi hardware
   - Development mode automatically falls back to mocks when Pi hardware unavailable
   - `dev_tools/` contains mock implementations of picamera2 and RPi.GPIO
   - Full feature parity with real hardware for testing

### Key Components

**Camera System** (`camera/`):
- Factory pattern with automatic hardware detection
- Supports Raspberry Pi HQ Camera (IMX-477), Arducam UC-955 (Pivariety), USB webcams, and mock cameras
- Advanced exposure control (1/10000s to 200s), ISO adjustment (20-1600), night vision mode
- State preservation for non-intrusive operation
- Thread-safe capture operations with retry logic

**Mount Control** (`mount/`):
- Stepper motor control for equatorial tracking via GPIO pins
- Configurable tracking speed for sidereal rate (3.523 default)
- Thread-safe operation with graceful shutdown
- Step sequences defined in `config.py`

**Session Management** (`session/`):
- Automated capture sessions with progress tracking
- Thread-based implementation for non-blocking operation
- JSON metadata export for each session
- Handles both photo and video capture sessions

**Web Interface** (`web/`):
- Flask-based REST API serving HTML/JS frontend
- Real-time camera feed via MJPEG streaming at `/video_feed`
- AJAX-based control for responsive UI
- Collapsible control panels for camera, mount, and session management

**Storage Management** (`utils/storage.py`):
- Intelligent storage hierarchy with automatic fallback
- Priority: USB drive (/media/*) → Home directory (~/wanda_captures) → Current directory
- Automatic directory creation and permission handling

## Important Implementation Details

### Camera State Management
The camera system preserves state to avoid disrupting other applications:
- Original camera controls saved before modification
- Camera controls restored to original values after use
- Proper cleanup on application shutdown via signal handlers
- Thread-safe operations for concurrent access

### Error Handling Architecture
- Custom exceptions in `camera/exceptions.py` and `session/exceptions.py`
- Mount exceptions follow similar pattern (though not in separate file)
- Web routes return appropriate HTTP status codes (200, 400, 500) with JSON error messages
- Comprehensive error logging throughout the application

### Threading Model
- Mount tracking runs in separate thread for continuous operation
- Session controller uses threads for non-blocking captures
- Web server uses threaded=True for concurrent request handling
- Proper thread cleanup on application shutdown

### Testing Strategy
- Comprehensive fixtures in `tests/conftest.py` for reusable test components
- Mock hardware implementations for CI/CD compatibility
- Unit tests for individual components
- Integration tests verify component interactions
- Web tests use Flask test client for endpoint testing

## Configuration

Main configuration in `config.py`:
- **Camera settings**: 
  - PREVIEW_SIZE = (1440, 810) - 16:9 aspect ratio
  - STILL_SIZE = (4056, 2282) - Maximum resolution 16:9
  - VIDEO_SIZE = (1920, 1080) - Full HD
  - DEFAULT_EXPOSURE_US = 10000 (10ms)
- **Mount settings**: 
  - MOTOR_PINS = [23, 24, 25, 8] - GPIO pins
  - 8-step sequence for smooth motor control
  - DEFAULT_SIDEREAL_DELAY = 3.523
- **Storage paths**: 
  - USB_BASE = "/media/astro1"
  - HOME_BASE = "/home/astro1/wanda_captures"
- **Web server**: 
  - HOST = '0.0.0.0' (all interfaces)
  - PORT = 5000

## Development Guidelines (aligned with `.cursor/rules` modular structure)

### Test-Driven Development (TDD) - MANDATORY
1. **Write failing test first** - Define expected behavior
2. **Write minimal code** - Make the test pass
3. **Refactor** - Improve code while keeping tests green
4. **Test coverage requirement**: Minimum 85% for new code

### Code Quality Standards
- **Simplicity**: Clear, maintainable code over complex abstractions
- **No duplication**: Reuse existing utilities and constants
- **File size**: Keep under 300 lines where possible
- **Only implement requested changes** - No unsolicited improvements

## Development Tips

1. **Running without hardware**: The application automatically uses mock implementations when Pi hardware is unavailable
2. **Camera testing**: Use `MOCK_CAMERA=1` environment variable to force mock camera even on Pi
3. **Mount testing**: Mock mount allows testing tracking logic without stepper motor
4. **Web development**: Frontend uses vanilla JavaScript with AJAX for simplicity
5. **Session testing**: Mock implementations support full session workflows
6. **Debugging camera detection**: Check `camera/factory.py` logs for detection process
7. **Testing specific components**: Use pytest markers or specific test paths

## Raspberry Pi Ecosystem Limitations

⚠️ **Important**: WANDA development has revealed significant limitations in the Raspberry Pi software ecosystem that affect automated deployment and cross-environment compatibility. See `docs/RASPBERRY_PI_ECOSYSTEM_LIMITATIONS.md` for detailed analysis.

**Key Challenges:**
- **Package Management Fragmentation**: System packages (apt) vs virtual environment packages (pip) compatibility issues
- **Binary Compatibility**: System picamera2 compiled against different numpy versions than venv
- **Hardware Integration Complexity**: Multiple layers (hardware, kernel, system, application) must align
- **Rapid Ecosystem Evolution**: Camera stack changes, OS updates, and hardware variations

**Critical Dependencies:**
- numpy version MUST match system picamera2 compilation (constrained to <2.0.0)
- OpenCV installed via pip due to Raspberry Pi camera integration requirements
- System packages required: python3-picamera2, python3-libcamera, libcamera-apps-lite
- Hardware permissions: DMA heap devices, video group membership, udev rules

**Testing Requirements:**
- Always test on actual Raspberry Pi hardware, not development machines
- Test automated installation from scratch, not incremental updates
- Verify camera functionality includes both live feed AND still captures
- Check logs for "Mock PiCamera" vs "picamera2.picamera2" to confirm real hardware usage

## API Endpoints

### Camera Control
- `POST /capture_still` - Capture a photo
- `POST /start_video` - Start video recording  
- `POST /stop_video` - Stop video recording
- `GET /capture_status` - Get current capture status
- `GET /video_feed` - MJPEG stream for live preview

### Mount Control
- `POST /start_tracking` - Start mount tracking with specified parameters
- `POST /stop_tracking` - Stop mount tracking

### Session Management
- `POST /start_session` - Start automated capture session
- `POST /stop_session` - Stop current session
- `GET /session_status` - Get session progress and status

## Hardware Support Details

### Camera Detection Priority
1. **Raspberry Pi Camera** (via CSI interface)
   - Detected using picamera2 library availability
   - Supports IMX477 and Pivariety cameras
   - Requires libcamera and picamera2 packages

2. **USB Camera** (via OpenCV)
   - Detected using cv2.VideoCapture
   - Supports any UVC-compatible webcam
   - Uses MJPG format for better performance

3. **Mock Camera** (development fallback)
   - Automatically used when no hardware detected
   - Generates synthetic images or uses local webcam
   - Full API compatibility for testing

### Mount Hardware
- Stepper motor control via RPi.GPIO
- 4-wire bipolar stepper motor support
- GPIO pins configurable in config.py
- Mock mount for development without hardware