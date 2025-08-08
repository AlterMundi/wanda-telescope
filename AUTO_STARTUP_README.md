# WANDA Telescope Auto-Startup Configuration

This document describes the automatic startup system for the WANDA telescope on Raspberry Pi 5.

## Overview

The auto-startup system consists of:
- **Systemd service**: `wanda-telescope.service` - Manages the application lifecycle
- **Service script**: `scripts/wanda-service.sh` - Handles robust startup with error handling
- **Installation script**: `scripts/install-service.sh` - Installs and configures the service
- **Uninstall script**: `scripts/uninstall-service.sh` - Removes the service

## Features

- **Automatic startup** on boot
- **Robust error handling** with pre-flight checks
- **Network connectivity** waiting
- **Hardware detection** and validation
- **Graceful shutdown** handling
- **Restart on failure** with configurable limits
- **Comprehensive logging** via systemd journal
- **Security hardening** appropriate for Pi hardware access

## Installation

### 1. Initial Setup
First, ensure the WANDA environment is properly configured:
```bash
cd /home/astro2/repos/wanda-telescope
./run-wanda.sh  # This sets up the virtual environment and dependencies
```

### 2. Install the Service
```bash
sudo ./scripts/install-service.sh
```

The service will be:
- ✅ Installed to `/etc/systemd/system/wanda-telescope.service`
- ✅ Enabled for automatic startup on boot
- ✅ Configured with proper user permissions (`astro2`)
- ✅ Set up with logging to `/var/log/wanda-telescope.log`

## Service Management

### Start/Stop/Status Commands
```bash
# Start the service
sudo systemctl start wanda-telescope

# Stop the service
sudo systemctl stop wanda-telescope

# Restart the service
sudo systemctl restart wanda-telescope

# Check service status
sudo systemctl status wanda-telescope

# View live logs
sudo journalctl -u wanda-telescope -f

# View recent logs
sudo journalctl -u wanda-telescope -n 50
```

### Enable/Disable Auto-Start
```bash
# Enable auto-start on boot (default after installation)
sudo systemctl enable wanda-telescope

# Disable auto-start on boot
sudo systemctl disable wanda-telescope
```

## Service Configuration

The service is configured with:
- **User**: `astro2` (runs as the astro2 user, not root)
- **Working Directory**: `/home/astro2/repos/wanda-telescope`
- **Network Dependencies**: Waits for network connectivity before starting
- **Restart Policy**: Automatically restarts on failure (max 3 attempts in 30 seconds)
- **Resource Limits**: 1GB memory limit, 65536 file descriptor limit
- **Hardware Access**: Full access to GPIO, camera, and storage devices

## Startup Process

The service follows this startup sequence:

1. **System Boot** → systemd starts the service
2. **Pre-flight Checks** → Validates environment and locks
3. **Network Wait** → Waits up to 60 seconds for connectivity  
4. **Directory Setup** → Creates necessary directories
5. **Environment Setup** → Activates virtual environment and checks dependencies
6. **Hardware Checks** → Detects Pi model, camera, and GPIO access
7. **Application Start** → Launches the WANDA web server

## Logs and Monitoring

### Service Logs
```bash
# Real-time service logs
sudo journalctl -u wanda-telescope -f

# Service logs from last boot
sudo journalctl -u wanda-telescope -b

# Service logs with timestamp filtering
sudo journalctl -u wanda-telescope --since "1 hour ago"
```

### Application Logs
```bash
# Main application log
tail -f /var/log/wanda-telescope.log

# Development logs (if running manually)
tail -f wanda.log
```

## Troubleshooting

### Service Won't Start
1. Check service status:
   ```bash
   sudo systemctl status wanda-telescope
   ```

2. Check logs for errors:
   ```bash
   sudo journalctl -u wanda-telescope -n 20
   ```

3. Test the startup script manually:
   ```bash
   cd /home/astro2/repos/wanda-telescope
   bash scripts/wanda-service.sh --test
   ```

### Common Issues

**Virtual Environment Missing**
```bash
# Solution: Run the setup script
./run-wanda.sh
```

**Permission Errors**
```bash
# Solution: Ensure user is in proper groups
sudo usermod -a -G video,gpio astro2
# Then reboot
```

**Camera Not Detected**
```bash
# Check camera connection and enable camera interface
sudo raspi-config
# Interface Options → Camera → Enable
```

**Web Interface Not Accessible**
```bash
# Check if service is running
sudo systemctl status wanda-telescope

# Check if port 5000 is listening
sudo netstat -tlnp | grep :5000

# Test local access
curl http://localhost:5000
```

### Manual Testing
```bash
# Stop the service
sudo systemctl stop wanda-telescope

# Run manually for debugging
cd /home/astro2/repos/wanda-telescope
./run-wanda.sh
```

## Uninstallation

To remove the auto-startup service:
```bash
sudo ./scripts/uninstall-service.sh
```

This will:
- Stop the service
- Disable auto-start
- Remove the service file
- Clean up log files (optional)

The application can still be run manually using `./run-wanda.sh`.

## Network Access

After successful startup, the WANDA web interface is available at:
- **Local**: http://localhost:5000
- **Network**: http://[PI_IP_ADDRESS]:5000

To find the Pi's IP address:
```bash
hostname -I
```

## Security Notes

- The service runs as user `astro2`, not root
- Hardware access (GPIO, camera) is enabled for telescope functionality  
- Network access is unrestricted for web interface functionality
- Log files are owned by the `astro2` user

## Service Dependencies

The service automatically waits for:
- Network connectivity (`network-online.target`)
- Basic system initialization
- File system availability

## Performance

- **Startup Time**: ~10-15 seconds from boot to web interface ready
- **Memory Usage**: ~200-300MB typical, 1GB maximum
- **CPU Usage**: Low when idle, moderate during image capture
- **Auto-restart**: Failed services restart automatically after 10 seconds

## Integration with Development

The auto-startup service is designed to coexist with manual development:

- **Development**: Stop the service and run `./run-wanda.sh` manually
- **Production**: Service runs automatically, accessible via web interface
- **Testing**: Service can be easily started/stopped for testing changes

```bash
# Switch to development mode
sudo systemctl stop wanda-telescope
./run-wanda.sh

# Switch back to service mode  
sudo systemctl start wanda-telescope
```