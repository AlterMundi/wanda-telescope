# WANDA Telescope

An open-source Raspberry Pi-based astrophotography system featuring an equatorial mount with automated star tracking capabilities and a comprehensive web interface.

## Overview

WANDA (World-wide Area Network for Distributed Astronomy) is a full-stack astrophotography system for Raspberry Pi featuring a modern **Next.js 14** frontend with **React 19** and a **Python Flask** backend with **Socket.IO**. It provides a comprehensive solution for controlling camera and equatorial mount systems for celestial object tracking, with real-time WebSocket updates, automated capture sessions, and production-ready deployment via Nginx reverse proxy.

## Features

### Hardware Control
- **Multi-Camera Support**: Automatic detection and support for Pi Camera, USB cameras, and mock cameras
- **Automated Star Tracking**: Equatorial mount control with configurable tracking speeds
- **Advanced Camera Control**: Exposure, ISO, gain adjustment, and night vision mode
- **Hardware Abstraction**: Mock implementations for development without physical hardware
- **State Preservation**: Non-intrusive camera operation with state restoration

### Software Architecture
- **Modern Web Interface**: Next.js 14 with App Router and React 19 + TypeScript
- **REST API Backend**: Flask-based API with comprehensive endpoint coverage
- **Real-Time Updates**: WebSocket (Socket.IO) communication via 3 namespaces (`/ws/camera`, `/ws/mount`, `/ws/session`)
- **Production Ready**: Nginx reverse proxy unifying frontend (port 3000) and backend (port 5000) on port 80
- **Auto-Startup**: Systemd services for both frontend and backend automatically start on boot
- **Concurrent Operations**: ThreadPoolExecutor and eventlet for non-blocking camera operations

### User Features
- **Session Management**: Automated capture sessions with progress tracking and metadata export
- **Live Preview**: MJPEG video streaming with histogram and focus assist overlays
- **Capture Gallery**: Browse and download captured images
- **Storage Management**: Automatic USB drive detection and fallback storage
- **Responsive UI**: Modern glassmorphism design with dark theme

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

## Architecture

WANDA uses a decoupled architecture with separate frontend and backend services unified through Nginx:

```
┌─────────────────────────────────────────────────────────┐
│              Raspberry Pi 5 (Production)                │
│                                                         │
│   ┌─────────────────────────────────────────────────┐  │
│   │  Nginx Reverse Proxy (Port 80)                  │  │
│   │  ├─ / → Next.js Frontend (Port 3000)            │  │
│   │  ├─ /api → Flask Backend (Port 5000)            │  │
│   │  ├─ /socket.io → WebSocket (Port 5000)          │  │
│   │  ├─ /video_feed → MJPEG Stream (Port 5000)      │  │
│   │  └─ /captures → Static Files (filesystem)       │  │
│   └─────────────────────────────────────────────────┘  │
│                                                         │
│   ┌──────────────────┐      ┌──────────────────────┐   │
│   │ wanda-frontend   │      │  wanda-backend       │   │
│   │  (systemd)       │      │   (systemd)          │   │
│   │                  │      │                      │   │
│   │  Next.js 14      │◄────►│  Flask + SocketIO   │   │
│   │  React 19        │ REST │  Python 3.11+        │   │
│   │  TypeScript      │ WS   │  Eventlet            │   │
│   │  shadcn/ui       │      │  ThreadPoolExecutor  │   │
│   └──────────────────┘      └──────────────────────┘   │
│                                      │                  │
│                                      ▼                  │
│                          ┌─────────────────────┐        │
│                          │  Hardware Layer     │        │
│                          │  ├─ picamera2       │        │
│                          │  ├─ libcamera       │        │
│                          │  └─ RPi.GPIO        │        │
│                          └─────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### Communication Flow
- **REST API**: Frontend calls `/api/*` endpoints for operations (capture, settings, etc.)
- **WebSocket**: Real-time bidirectional updates via Socket.IO namespaces (`/ws/camera`, `/ws/mount`, `/ws/session`)
- **MJPEG Stream**: Live camera feed streamed directly from Flask to browser
- **Static Files**: Captures served by Nginx from filesystem

### System Services
- **wanda-backend.service**: Flask API + WebSocket server (auto-start on boot)
- **wanda-frontend.service**: Next.js production build (auto-start on boot)
- **nginx.service**: Reverse proxy unifying both services on port 80

## Installation

### Prerequisites

- Raspberry Pi 4/5 (4GB RAM minimum, 8GB recommended)
- Raspberry Pi HQ Camera (IMX477) or compatible camera
- MicroSD card (32GB+)
- Raspberry Pi OS Lite or Desktop (64-bit recommended)

### Step 1: Camera Configuration

```bash
# Update system
sudo apt update
sudo apt upgrade

# Configure camera sensor (IMX477)
sudo nano /boot/firmware/config.txt

# Add these lines under the [all] section:
camera_auto_detect=0
dtoverlay=imx477

# For Pi 5 with CAM0 port, use:
# dtoverlay=imx477,cam0

# Save and reboot
sudo reboot

# Test camera detection
rpicam-still --list-cameras
```

### Step 2: Install System Dependencies

```bash
# Install Python and camera libraries
sudo apt install -y git python3-libcamera python3-picamera2 python3-pip python3-venv

# Install Node.js 20.x (required for Next.js)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
sudo apt install -y nginx

# Verify installations
python3 --version  # Should be 3.11+
node --version     # Should be v20.x
nginx -v          # Should be 1.18+
```

### Step 3: Clone and Setup Backend

```bash
# Clone repository
git clone https://github.com/AlterMundi/wanda-telescope.git
cd wanda-telescope

# Create virtual environment with system package access
# (Required for picamera2)
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Setup Frontend

```bash
# Navigate to Next.js directory
cd wanda-telescope

# Install Node.js dependencies (this may take 10-15 minutes on Pi)
npm install

# Build production version
npm run build
```

### Step 5: Configure Systemd Services

```bash
# Copy service files from deployment directory
sudo cp deployment/wanda-backend.service /etc/systemd/system/
sudo cp deployment/wanda-frontend.service /etc/systemd/system/

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable wanda-backend.service
sudo systemctl enable wanda-frontend.service

# Start services
sudo systemctl start wanda-backend.service
sudo systemctl start wanda-frontend.service

# Check status
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service
```

**Note:** If your installation path differs from `/home/admin/wanda-telescope`, edit the service files before copying to update `WorkingDirectory`, `ExecStart`, and `User`/`Group` fields.

### Step 6: Configure Nginx

```bash
# Copy Nginx configuration from deployment directory
sudo cp deployment/wanda-telescope.nginx /etc/nginx/sites-available/wanda-telescope

# Enable the site
sudo ln -s /etc/nginx/sites-available/wanda-telescope /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site (optional)

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

**Note:** If your installation path or username differs, edit `/etc/nginx/sites-available/wanda-telescope` and update the `alias` path in the `/captures` location block.

**For detailed deployment instructions, troubleshooting, and production tips, see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).**

### Step 7: Access WANDA

Open a web browser and navigate to:
- **Local access**: `http://raspberrypi.local/` (or use Pi's IP address)
- **Same network**: `http://[pi-ip-address]/`

You should see the modern WANDA telescope interface with:
- Live camera preview with MJPEG streaming
- Camera controls (exposure, ISO, gain)
- Mount tracking controls
- Session management for automated captures
- Real-time status updates via WebSocket

### Quick Development Setup (No Services)

For development without systemd services:

```bash
# Terminal 1: Start backend
cd wanda-telescope
source venv/bin/activate
python main.py  # Runs on port 5000

# Terminal 2: Start frontend (dev mode)
cd wanda-telescope/wanda-telescope
npm run dev  # Runs on port 3000

# Access at http://localhost:3000
```

## Core Design Patterns & Backend Architecture

### 1. Factory Pattern Implementation
- **Camera Factory**: `camera/factory.py` - Auto-detects hardware and creates appropriate implementations
- **Mount Factory**: `mount/factory.py` - Creates mount implementations based on available hardware

### 2. Abstract Base Classes
- **Camera Interface**: `camera/base.py` - AbstractCamera defines required interface
- **Mount Interface**: `mount/base.py` - Abstract mount interface for tracking control

### 3. Hardware Abstraction
- Mock implementations allow development without Raspberry Pi hardware
- Development mode automatically falls back to mocks when Pi hardware unavailable
- `dev_tools/` contains mock implementations of picamera2 and RPi.GPIO

### Backend Components

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

#### Web API (`web/app.py`)
- Flask-based REST API with comprehensive endpoint coverage
- WebSocket namespaces for real-time communication:
  - `/ws/camera` - Camera status and capture events
  - `/ws/mount` - Mount tracking status
  - `/ws/session` - Session progress updates
- MJPEG video streaming for live preview
- CORS-enabled for cross-origin requests
- ThreadPoolExecutor for non-blocking camera operations

### Frontend Application

The web interface is a standalone Next.js application located in `wanda-telescope/`:

#### Technology Stack
- **Next.js 14.2.25** with App Router
- **React 18.2** (compatible with React 19 features) with TypeScript 5.6
- **Tailwind CSS 3.4** + **shadcn/ui** components (Radix UI primitives)
- **Socket.IO Client 4.7** for WebSocket communication
- **Vitest 2.1** + Testing Library for component testing
- **Lucide React** for icons

#### Key Features
- **Real-time Updates**: WebSocket integration for live camera/mount status
- **Live Preview**: MJPEG stream with histogram and focus assist overlays
- **Camera Controls**: Exposure, ISO, gain, and capture settings
- **Mount Controls**: Tracking start/stop and speed adjustments
- **Session Management**: Automated capture with progress tracking
- **Capture Gallery**: Browse and download recent images
- **Responsive Design**: Modern glassmorphism UI with dark theme

#### Frontend Structure
```
wanda-telescope/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── camera-controls.tsx
│   ├── mount-controls.tsx
│   ├── session-controls.tsx
│   ├── image-preview.tsx
│   └── ui/               # shadcn/ui components
├── lib/                  # Utilities
│   ├── api-client.ts    # REST API wrapper
│   └── hooks/
│       └── useWebSocket.ts  # WebSocket hook
└── package.json
```

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

# Run Flask backend
python main.py

# (optional) start Next.js frontend in another terminal
# cd wanda-telescope && npm run dev
```

## Project Structure

```
wanda-telescope/
├── main.py                      # Application entry point (Flask + SocketIO)
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
├── CLAUDE.md                    # Rules for Claude Code users
├── README.md                    # This file
│
├── camera/                      # Camera system modules
│   ├── base.py                 # Abstract camera interface
│   ├── factory.py              # Camera factory and detection
│   └── implementations/        # Camera implementations
│       ├── pi_camera.py        # Raspberry Pi camera (IMX477)
│       ├── usb_camera.py       # USB camera support
│       └── mock_camera.py      # Mock camera for development
│
├── mount/                       # Mount control system
│   ├── base.py                 # Abstract mount interface
│   ├── factory.py              # Mount factory
│   ├── controller.py           # Mount controller logic
│   └── implementations/        # Mount implementations
│       ├── pi_mount.py         # Raspberry Pi GPIO mount
│       └── mock_mount.py       # Mock mount for development
│
├── session/                     # Session management
│   ├── controller.py           # Session controller
│   └── __init__.py
│
├── web/                         # Flask REST API (Backend)
│   ├── app.py                  # Main Flask application + WebSocket namespaces
│   ├── api_responses.py        # Response utilities
│   └── __init__.py
│
├── wanda-telescope/             # Next.js Frontend Application
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Main page
│   │   └── globals.css         # Global styles
│   ├── components/             # React components
│   │   ├── camera-controls.tsx # Camera control panel
│   │   ├── mount-controls.tsx  # Mount control panel
│   │   ├── session-controls.tsx # Session management
│   │   ├── image-preview.tsx   # Live feed display
│   │   ├── capture-panel.tsx   # Capture controls
│   │   ├── histogram.tsx       # Histogram overlay
│   │   ├── focus-assist.tsx    # Focus assist overlay
│   │   ├── status-bar.tsx      # Status display
│   │   ├── ui/                 # shadcn/ui components
│   │   └── __tests__/          # Component tests
│   ├── lib/                    # Frontend utilities
│   │   ├── api-client.ts       # REST API wrapper
│   │   ├── utils.ts            # Helper functions
│   │   └── hooks/
│   │       └── useWebSocket.ts # WebSocket hook
│   ├── package.json            # Frontend dependencies
│   ├── next.config.mjs         # Next.js configuration (API proxy)
│   ├── tailwind.config.ts      # Tailwind CSS config
│   ├── tsconfig.json           # TypeScript config
│   ├── vitest.config.ts        # Vitest test config
│   └── env.*.sample            # Environment variable templates
│
├── deployment/                  # Production deployment files
│   ├── wanda-backend.service   # Backend systemd service
│   ├── wanda-frontend.service  # Frontend systemd service
│   ├── wanda-telescope.nginx   # Nginx reverse proxy config
│   └── README.md               # Deployment instructions
│
├── utils/                       # Utility functions
│   └── storage.py              # Storage management
│
├── dev_tools/                   # Development tools
│   └── __init__.py             # Mock implementations
│
├── docs/                        # Documentation
│   ├── archive/                # Archived planning documents
│   │   ├── NEXTJS_INTEGRATION_PLAN.md  # Full Next.js integration plan
│   │   ├── v0-report.md                # v0.dev UI generation report
│   │   └── DEADLOCK_FIX_SUMMARY.md     # Backend concurrency fix
│   ├── DEPLOYMENT.md           # Production deployment guide ⭐
│   ├── ARDUCAM_UC955_SETUP.md  # Arducam camera configuration
│   ├── AUTO_STARTUP_README.md  # Legacy auto-startup (systemd v1)
│   ├── DEV_DEPLOYMENT.md       # Development deployment guide
│   ├── NETWORK_DISCOVERY.md    # Network discovery tools
│   ├── camera_state_restoration.md     # Camera state management
│   ├── picamera2_controls.md           # Camera control reference
│   ├── RASPBERRY_PI_ECOSYSTEM_LIMITATIONS.md  # Platform constraints
│   └── test_capture_isolation.md       # Testing methodology
│
├── tests/                       # Test suite (pytest)
│   ├── test_main.py            # Main application tests
│   ├── test_camera/            # Camera system tests
│   ├── test_session/           # Session management tests
│   └── test_web/               # Web API tests
│
├── scripts/                     # Utility scripts
│   ├── announce-ip.sh          # Network discovery
│   ├── find-wanda.py           # Network discovery finder
│   └── install-service.sh      # Service installation
│
├── captures/                    # Captured images directory
├── venv/                        # Python virtual environment
└── .gitignore                   # Git ignore rules
```

### Deployment Files (`deployment/`)

Service and configuration files for production deployment:

- **`wanda-backend.service`** - Systemd service for Flask backend (Python)
  - Runs `main.py` with venv Python interpreter
  - Auto-restart on failure
  - Logs to systemd journal
  
- **`wanda-frontend.service`** - Systemd service for Next.js frontend (Node.js)
  - Runs `npm start` in production mode
  - Depends on backend service
  - Auto-restart on failure
  
- **`wanda-telescope.nginx`** - Nginx reverse proxy configuration
  - Routes `/` to Next.js (port 3000)
  - Routes `/api`, `/socket.io`, `/video_feed` to Flask (port 5000)
  - Serves `/captures` as static files
  
- **`README.md`** - Detailed deployment instructions and troubleshooting

See `deployment/README.md` for installation and customization instructions.

## Managing Services

Once deployed, you can manage WANDA services using systemd:

```bash
# Check service status
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service
sudo systemctl status nginx.service

# View logs
sudo journalctl -u wanda-backend.service -f     # Follow backend logs
sudo journalctl -u wanda-frontend.service -f    # Follow frontend logs

# Restart services
sudo systemctl restart wanda-backend.service
sudo systemctl restart wanda-frontend.service
sudo systemctl restart nginx

# Stop services
sudo systemctl stop wanda-backend.service
sudo systemctl stop wanda-frontend.service

# Disable auto-start
sudo systemctl disable wanda-backend.service
sudo systemctl disable wanda-frontend.service
```

## Critical Implementation Notes

### Backend Concurrency Fix

The Flask backend uses **selective eventlet monkey patching** to prevent deadlocks:

```python
# main.py (lines 5-8)
import eventlet
eventlet.monkey_patch(socket=True, select=True, time=True, 
                     os=False, thread=False, subprocess=False)
```

**Why selective patching?**
- Makes I/O and `time.sleep()` non-blocking for concurrent request handling
- Preserves native threading for `picamera2` compatibility
- Prevents MJPEG video stream from blocking other requests
- Enables concurrent camera captures with `ThreadPoolExecutor`

**Without this fix:** The backend deadlocks within minutes under load. See `docs/archive/DEADLOCK_FIX_SUMMARY.md` for full technical analysis.

### Next.js Backend Connection

The frontend uses IPv4 (`127.0.0.1`) instead of `localhost` for backend connections:

```javascript
// next.config.mjs
destination: "http://127.0.0.1:5000/api/:path*"
```

This prevents IPv6 resolution issues on Raspberry Pi OS.

## Troubleshooting

### Services won't start
```bash
# Check for errors in logs
sudo journalctl -u wanda-backend.service -n 50
sudo journalctl -u wanda-frontend.service -n 50

# Verify Python environment
cd /home/admin/wanda-telescope
source venv/bin/activate
python main.py  # Test manually

# Verify Node.js build
cd /home/admin/wanda-telescope/wanda-telescope
npm run build  # Rebuild if needed
```

### Nginx 502 Bad Gateway
```bash
# Ensure backend services are running
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service

# Check Nginx configuration
sudo nginx -t

# View Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Camera not detected
```bash
# Check camera connection
rpicam-still --list-cameras

# Verify /boot/firmware/config.txt
cat /boot/firmware/config.txt | grep imx477

# Test with native tools
rpicam-still -o test.jpg
```

### WebSocket not connecting
```bash
# Check if backend is listening
sudo netstat -tulpn | grep 5000

# Test backend directly
curl http://localhost:5000/api/status

# Check browser console for CORS errors
# Ensure CORS origins are configured correctly in web/app.py
```

## API Documentation

### REST API Endpoints

All API endpoints are prefixed with `/api` and return JSON responses:

**Camera Endpoints:**
- `GET /api/camera/status` - Get current camera settings and status
- `POST /api/camera/settings` - Update camera settings (exposure, ISO, gain)
- `POST /api/camera/capture` - Capture a single image
- `GET /api/captures` - List all captured images

**Mount Endpoints:**
- `GET /api/mount/status` - Get mount tracking status
- `POST /api/mount/tracking` - Start/stop tracking (JSON body: `{"tracking": true/false}`)

**Session Endpoints:**
- `GET /api/session/status` - Get current session status and progress
- `POST /api/session/start` - Start automated capture session
- `POST /api/session/stop` - Stop current session

**Video Stream:**
- `GET /video_feed` - MJPEG live camera stream

### WebSocket Namespaces

Real-time bidirectional communication via Socket.IO:

**`/ws/camera` - Camera Events**
- `status` - Camera settings updates (exposure, ISO, mode)
- `capture_start` - Capture beginning
- `capture_complete` - Capture finished with filename
- `capture_error` - Capture failed with error message

**`/ws/mount` - Mount Events**
- `status` - Mount tracking status
- `tracking_start` - Tracking started
- `tracking_stop` - Tracking stopped

**`/ws/session` - Session Events**
- `status` - Session status and progress
- `session_start` - Session initiated
- `session_progress` - Image count updates
- `session_complete` - Session finished
- `session_error` - Session failed

For detailed event payloads and integration examples, see `docs/archive/NEXTJS_INTEGRATION_PLAN.md`.

### Example API Calls

```bash
# Get camera status
curl http://localhost/api/status

# Capture an image
curl -X POST http://localhost/api/capture

# Get recent captures
curl http://localhost/api/captures
```

## Development History

### feat/v0-ui Branch (October 2025)

Major architectural overhaul introducing modern Next.js frontend:

**Frontend Migration:**
- Generated initial UI with v0.dev (shadcn/ui + Tailwind CSS)
- Integrated Next.js 14 with React 18 and TypeScript
- Implemented real-time WebSocket communication via Socket.IO
- Created comprehensive component library with tests
- Added MJPEG video streaming with overlays (histogram, focus assist)

**Backend Enhancements:**
- Converted Flask from template-based to pure REST API
- Added Flask-SocketIO with 3 namespaces (`/ws/camera`, `/ws/mount`, `/ws/session`)
- Implemented ThreadPoolExecutor for non-blocking camera operations
- Added selective eventlet monkey patching to prevent deadlocks
- Fixed WebSocket namespace signatures for proper connection handling

**Production Infrastructure:**
- Created systemd services for auto-start (frontend + backend)
- Configured Nginx reverse proxy for unified access on port 80
- Added comprehensive deployment files and documentation
- IPv4-only backend connections to avoid Pi OS networking issues

**Key Commits:**
- `759db69` - UI color scheme refinements
- `70e0649` - WebSocket fixes and real-time updates
- `a60878d` - Critical deadlock fix + Nginx production setup
- `fe12239` - Next.js frontend runs correctly
- `65be4e6` - Initial v0.dev UI generation

See `docs/archive/NEXTJS_INTEGRATION_PLAN.md` and `docs/archive/DEADLOCK_FIX_SUMMARY.md` for technical details.

## License

This project is open-source. Please ensure you provide appropriate attribution when using or modifying this code.

## Support

- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Join discussions in GitHub Discussions
- **Documentation**: See `docs/` directory for guides and technical details

## Quick Links

- 📚 [Production Deployment Guide](docs/DEPLOYMENT.md)
- 🏗️ [Next.js Integration Plan](docs/archive/NEXTJS_INTEGRATION_PLAN.md)
- 🐛 [Deadlock Fix Technical Analysis](docs/archive/DEADLOCK_FIX_SUMMARY.md)
- 🎨 [v0.dev UI Generation Report](docs/archive/v0-report.md)

---

**WANDA Telescope** - Making astrophotography accessible to everyone! 🔭✨