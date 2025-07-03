# WANDA Telescope

An open-source Raspberry Pi-based astrophotography system featuring an equatorial mount with automated star tracking capabilities.

## Overview

WANDA (Wide-Angle Nightsky Digital Astrophotographer) is a DIY telescope system combining a Raspberry Pi with the HQ Camera module (IMX-477), a 3D printed equatorial mount, and a stepper motor for automated tracking. It offers a comprehensive web interface for controlling the camera and mount, making astrophotography more accessible.

## Features

- **High-Quality Imaging**: Uses the Raspberry Pi HQ Camera (IMX-477 sensor) for detailed astrophotography
- **Automated Star Tracking**: Equatorial mount with stepper motor control for smooth tracking of celestial objects
- **Web Interface**: Control the system from any device on the same network
- **Configurable Settings**: Adjust exposure, ISO, and tracking speed
- **Digital Gain**: Optional digital boost for capturing faint night sky details
- **RAW Capture**: Option to save RAW files for post-processing
- **Video Recording**: Capture videos of celestial events
- **Responsive Design**: Mobile-friendly UI
- **Development Mode**: Works on any Linux system with mock hardware interfaces for testing

## Hardware Requirements

### For Astrophotography (Raspberry Pi Setup)
- Raspberry Pi (4 recommended for best performance)
- Raspberry Pi HQ Camera module (IMX-477)
- Compatible lens or telescope adapter
- 3D printed equatorial mount (STL files not included in this repository)
- Stepper motor (compatible with pins defined in config.py)
- Power supply

### For Development/Testing (Any Linux System)
- Any Linux computer with Python 3
- Optional: USB webcam (will be used for preview if available)

## Quick Start

The easiest way to run WANDA is using the automated setup script:

### 1. Clone and Run

```bash
git clone https://github.com/yourusername/wanda-telescope.git
cd wanda-telescope
chmod +x run-wanda.sh
./run-wanda.sh
```

That's it! The script will:
- ✅ Create a Python virtual environment
- ✅ Install all required dependencies
- ✅ Create necessary directories
- ✅ Start the web server automatically

### 2. Access the Interface

Once running, open your web browser and navigate to:
- **Local access**: `http://localhost:5000`
- **Network access**: `http://[your-ip-address]:5000`

The script will display the exact URL when it starts.

### 3. Running Again

You can run the script multiple times safely:
```bash
./run-wanda.sh
```
It will skip setup steps that are already complete and start the application quickly.

## Manual Installation (Alternative)

If you prefer manual setup or need to customize the installation:

### Prerequisites
- Python 3.7+ 
- pip (Python package manager)

### Step-by-step Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/wanda-telescope.git
   cd wanda-telescope
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install core dependencies:**
   ```bash
   pip install Flask opencv-python numpy Jinja2 Werkzeug Pillow
   ```

4. **Install Raspberry Pi packages (if on Raspberry Pi):**
   ```bash
   pip install picamera2 RPi.GPIO gpiozero
   ```

5. **Create capture directory:**
   ```bash
   mkdir -p ~/wanda_captures
   ```

6. **Run the application:**
   ```bash
   python main.py
   ```

## Usage

### Web Interface

The modern web interface provides an immersive full-screen experience:

- **Camera Feed**: Full-screen live preview with optimal viewing
- **Collapsible Panels**: Side panels for camera and mount controls that slide out when needed
- **Camera Controls**: 
  - Exposure settings (1/10000s to 200s)
  - ISO adjustment (20-1600)
  - Digital gain for night sky enhancement
  - RAW file saving option
  - Performance tuning for CPU usage
- **Mount Controls**:
  - Tracking speed configuration
  - Direction control (clockwise/counterclockwise)
  - Start/stop tracking

### Taking Photos

1. **Adjust camera settings** using the Camera panel
2. **Start mount tracking** if following celestial objects  
3. **Click "Capture Photo"** - the interface will show progress
4. **Files are saved** to `~/wanda_captures` (or USB drive if available)

### Recording Videos

1. Configure your settings
2. Click "Start Video" to begin recording
3. Click "Stop Video" when finished
4. Videos are saved as H.264 files

## System Compatibility

- **Raspberry Pi**: Full functionality with real camera and GPIO control
- **Development Systems**: Mock interfaces simulate hardware for testing
- **All Linux Distributions**: The automated script works on any modern Linux system

## Configuration

The system can be configured by editing `config.py`:

- **Camera settings**: Resolution, default exposure, gain settings
- **Mount settings**: GPIO pins, tracking speed, step sequences
- **Storage settings**: Capture locations, USB drive preferences  
- **Web server settings**: Host address, port number

## File Structure

```
wanda-telescope/
├── run-wanda.sh          # Automated setup and run script
├── main.py               # Application entry point
├── config.py             # Configuration settings
├── camera/               # Camera controller modules
├── mount/                # Mount controller for tracking
├── utils/                # Utility functions
├── web/                  # Flask web application
│   ├── templates/        # HTML templates
│   └── static/          # CSS, JavaScript, images
├── dev_tools/           # Mock interfaces for development
└── venv/                # Virtual environment (created by script)
```

## Troubleshooting

### Script Won't Run
```bash
# Make sure the script is executable
chmod +x run-wanda.sh

# Check if Python 3 is installed
python3 --version
```

### Camera Issues on Raspberry Pi
```bash
# Check if camera is detected
vcgencmd get_camera

# Enable camera in raspi-config if needed
sudo raspi-config
```

### Network Access Issues
- Check firewall settings if accessing from other devices
- Ensure the Raspberry Pi and your device are on the same network
- Try the IP address shown in the script output

### Port Already in Use
If port 5000 is busy, edit `config.py` and change the `PORT` setting.

## Development

The project includes mock interfaces that simulate Raspberry Pi hardware, making it easy to develop and test on any Linux system. The automated script detects your environment and configures accordingly.

## Contributing

Contributions are welcome! The automated script makes it easy for contributors to get started quickly.

## License

This project is open-source. Please ensure you provide appropriate attribution when using or modifying this code.

## Acknowledgements

Special thanks to contributors and the open-source community for making this project possible.