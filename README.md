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

## Hardware Requirements

- Raspberry Pi (4 recommended for best performance)
- Raspberry Pi HQ Camera module (IMX-477)
- Compatible lens or telescope adapter
- 3D printed equatorial mount (STL files not included in this repository)
- Stepper motor (compatible with pins defined in config.py)
- Power supply

## Software Requirements

Python packages (see requirements.txt for full list):
- Flask
- picamera2
- OpenCV (opencv-python)
- RPi.GPIO
- NumPy

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/wanda-telescope.git
   cd wanda-telescope
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create capture directory:
   ```
   mkdir -p ~/wanda_captures
   ```

4. Run the application:
   ```
   python main.py
   ```

## Usage

1. Access the web interface by navigating to `http://[raspberry-pi-ip]:5000` in your browser.

2. The interface provides two main control panels:
   - **Camera Controls**: Adjust exposure time, ISO, digital gain, and capture settings
   - **Mount Controls**: Configure tracking speed and direction

3. Before capturing:
   - Adjust camera settings for the specific celestial object
   - Start mount tracking to follow the object's movement

4. Capture options:
   - Take still photos (with optional RAW format)
   - Record videos

## Configuration

The system can be configured by editing `config.py`:

- Camera settings (resolution, default exposure, etc.)
- Mount settings (GPIO pins, tracking speed)
- Storage settings (capture locations)
- Web server settings (host, port)

## Project Structure

- `camera/`: Camera controller and related modules
- `mount/`: Mount controller for the equatorial tracking system
- `utils/`: Utility functions for storage management
- `web/`: Flask web application with UI templates and static assets
- `config.py`: Configuration settings
- `main.py`: Main application entry point

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open-source. Please ensure you provide appropriate attribution when using or modifying this code.

## Acknowledgements

Special thanks to contributors and the open-source community for making this project possible.