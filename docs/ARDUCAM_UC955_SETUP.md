# Arducam UC-955 Camera Setup Guide

This guide provides setup instructions for the **Arducam UC-955** (Pivariety) camera module with WANDA telescope system on Raspberry Pi 5.

## Camera Module Information

- **Model**: Arducam UC-955 
- **Sensor**: IMX477-based with Pivariety adapter
- **Resolution**: 1920x1080 @ 60fps (10-bit RGGB)
- **Connection**: CSI-2 interface via ribbon cable

## Official Documentation

For complete documentation and latest drivers, visit:
**[Arducam Pivariety Camera Quick Start Guide](https://docs.arducam.com/Raspberry-Pi-Camera/Pivariety-Camera/Quick-Start-Guide/)**

## Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS Bookworm
- Arducam UC-955 camera module
- CSI camera ribbon cable (included with camera)
- Internet connection for downloading drivers

## Installation Steps

### 1. Physical Connection

1. Power down the Raspberry Pi completely
2. Connect the camera ribbon cable to the **Camera 1** port on Pi 5
3. Ensure silver contacts face the HDMI ports
4. Connect the other end to the Arducam UC-955 module
5. Verify connections are secure and cables are not damaged

### 2. Install Arducam Drivers

Run the automated installation script:

```bash
# Download installation script
wget -O install_pivariety_pkgs.sh https://github.com/ArduCAM/Arducam-Pivariety-V4L2-Driver/releases/download/install_script/install_pivariety_pkgs.sh
chmod +x install_pivariety_pkgs.sh

# Install libcamera development packages
./install_pivariety_pkgs.sh -p libcamera_dev

# Install libcamera applications (rpicam-* commands)
./install_pivariety_pkgs.sh -p libcamera_apps
```

### 3. Configure Device Tree Overlay

Edit the boot configuration:

```bash
sudo nano /boot/firmware/config.txt
```

Add or modify the camera overlay line:
```
dtoverlay=arducam-pivariety
```

**Important**: Replace any existing `dtoverlay=imx477` with `dtoverlay=arducam-pivariety`

### 4. Install Missing Tuning File

The Arducam UC-955 requires a specific tuning file for libcamera operation:

```bash
sudo cp /usr/share/libcamera/ipa/rpi/pisp/arducam_64mp.json /usr/share/libcamera/ipa/rpi/pisp/arducam-pivariety.json
```

This step is **critical** - without this file, the camera will be detected by the kernel but not accessible via libcamera applications.

### 5. Reboot System

```bash
sudo reboot
```

## Verification

After reboot, verify camera detection:

```bash
# List available cameras
rpicam-hello --list-cameras

# Expected output:
# Available cameras
# -----------------
# 0 : arducam-pivariety [1920x1080 10-bit RGGB] (/base/axi/pcie@1000120000/rp1/i2c@80000/arducam_pivariety@c)
#     Modes: 'SRGGB10_CSI2P' : 1920x1080 [60.00 fps - (0, 0)/1920x1080 crop]
```

Test camera operation:
```bash
# 5-second preview
rpicam-hello -t 5000

# Capture test image
rpicam-still -o test_image.jpg
```

## Troubleshooting

### Camera Not Detected

1. **Check physical connections**:
   - Ensure ribbon cable is properly seated at both ends
   - Verify cable is not damaged (try a spare if available)
   - Confirm camera is connected to "Camera 1" port on Pi 5

2. **Verify kernel detection**:
   ```bash
   dmesg | grep -i "arducam\|pivariety"
   ```
   Look for: `arducam-pivariety 11-000c: firmware version: 0x10003`

3. **Check I2C communication**:
   ```bash
   # Should show video devices created
   ls -la /dev/video0 /dev/video1 /dev/video2 /dev/video3
   ```

### libcamera Errors

If you see "Configuration file not found" errors:
```bash
# Verify tuning file exists
ls -la /usr/share/libcamera/ipa/rpi/pisp/arducam-pivariety.json

# If missing, reinstall:
sudo cp /usr/share/libcamera/ipa/rpi/pisp/arducam_64mp.json /usr/share/libcamera/ipa/rpi/pisp/arducam-pivariety.json
```

### WANDA Application Issues

If WANDA still reports "No cameras detected":
1. Restart the WANDA application
2. Check that the camera factory correctly detects the new camera
3. Verify permissions (user should be in `video` group)

## Technical Details

### Device Tree Configuration
- **Overlay**: `arducam-pivariety`
- **I2C Address**: `11-000c` (0x0c on bus 11)
- **CSI Interface**: `/dev/media3` with multiple video nodes

### Video Devices Created
- `/dev/video0`: Main camera stream (CSI2 CH0)
- `/dev/video1`: Embedded data
- `/dev/video2-3`: Additional CSI2 channels
- `/dev/video4-7`: PiSP frontend processing

### libcamera Configuration
- **Tuning file**: `/usr/share/libcamera/ipa/rpi/pisp/arducam-pivariety.json`
- **IPA module**: `rpi/pisp`
- **Supported format**: SRGGB10_CSI2P (10-bit Bayer RGGB)

## Integration with WANDA

The WANDA telescope system will automatically detect the Arducam UC-955 as a Pi camera through the existing camera factory system. No additional code changes are required - the camera will be instantiated as a `PiCamera` implementation and provide full functionality including:

- Live preview streaming
- Adjustable exposure and gain controls
- Night vision mode
- Automated capture sessions
- Image storage with metadata

---

**Last Updated**: August 2025
**Tested On**: Raspberry Pi 5 with Raspberry Pi OS Bookworm
**Camera Model**: Arducam UC-955 (Pivariety)