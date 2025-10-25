# WANDA Telescope - Production Deployment Guide

Complete guide for deploying WANDA Telescope with Next.js frontend and Flask backend on Raspberry Pi.

## Overview

This deployment creates a production-ready astrophotography system with:
- **Backend**: Flask + Socket.IO (port 5000) - camera control and hardware interface
- **Frontend**: Next.js production build (port 3000) - modern web UI
- **Reverse Proxy**: Nginx (port 80) - unified access point
- **Auto-Start**: Systemd services start on boot
- **Monitoring**: Systemd journal logging for both services

## Prerequisites

### Hardware
- Raspberry Pi 4/5 (4GB RAM minimum, 8GB recommended)
- MicroSD card (32GB+)
- Raspberry Pi HQ Camera (IMX477) or compatible
- Stable power supply

### Software
- Raspberry Pi OS Lite or Desktop (64-bit recommended)
- Python 3.11+
- Node.js 20.x
- Nginx 1.18+

## Installation Steps

### 1. System Preparation

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install system dependencies
sudo apt install -y git python3-libcamera python3-picamera2 \
                    python3-pip python3-venv nginx
```

### 2. Camera Configuration

```bash
# Configure camera sensor
sudo nano /boot/firmware/config.txt

# Add these lines under [all]:
camera_auto_detect=0
dtoverlay=imx477

# For Pi 5 with CAM0 port:
# dtoverlay=imx477,cam0

# Save and reboot
sudo reboot

# Verify camera detection
rpicam-still --list-cameras
```

### 3. Install Node.js

```bash
# Install Node.js 20.x (required for Next.js)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version  # Should be v20.x.x
npm --version   # Should be 10.x.x
```

### 4. Clone and Setup Repository

```bash
# Clone repository
git clone https://github.com/AlterMundi/wanda-telescope.git
cd wanda-telescope

# Switch to production branch (if needed)
git checkout main  # or feat/v0-ui for latest features
```

### 5. Backend Setup

```bash
# Create virtual environment with system packages access
# (Required for picamera2)
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Test backend manually (optional)
python main.py
# Press Ctrl+C to stop after verifying it starts
```

### 6. Frontend Setup

```bash
# Navigate to Next.js directory
cd wanda-telescope

# Install Node.js dependencies (takes 10-15 minutes on Pi)
npm install

# Build production version
npm run build

# Test frontend manually (optional)
npm start
# Press Ctrl+C to stop after verifying it starts
```

### 7. Install Systemd Services

```bash
# Return to project root
cd /home/admin/wanda-telescope

# Copy service files (update paths if your installation differs)
sudo cp deployment/wanda-backend.service /etc/systemd/system/
sudo cp deployment/wanda-frontend.service /etc/systemd/system/

# If your username or path differs, edit the service files:
# sudo nano /etc/systemd/system/wanda-backend.service
# sudo nano /etc/systemd/system/wanda-frontend.service
# Update: User, Group, WorkingDirectory, ExecStart

# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable wanda-backend.service
sudo systemctl enable wanda-frontend.service

# Start services
sudo systemctl start wanda-backend.service
sudo systemctl start wanda-frontend.service

# Verify both services are running
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service
```

### 8. Configure Nginx Reverse Proxy

```bash
# Copy Nginx configuration
sudo cp deployment/wanda-telescope.nginx /etc/nginx/sites-available/wanda-telescope

# If your paths differ, edit the configuration:
# sudo nano /etc/nginx/sites-available/wanda-telescope
# Update: alias path in /captures location

# Enable the site
sudo ln -s /etc/nginx/sites-available/wanda-telescope /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# If test passes, restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 9. Verify Installation

```bash
# Check all services are running
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service
sudo systemctl status nginx.service

# Check services are listening on correct ports
sudo netstat -tulpn | grep -E '3000|5000|80'

# Test local access
curl http://localhost/api/status
```

### 10. Access WANDA

Open a web browser and navigate to:
- **Local**: `http://raspberrypi.local/`
- **Network**: `http://[PI_IP_ADDRESS]/`

To find your Pi's IP address:
```bash
hostname -I
```

## Post-Installation Configuration

### Environment Variables

The frontend uses environment variables for API endpoints:

```bash
cd wanda-telescope

# For development
cp env.local.sample .env.local

# For production (already configured by default)
# No changes needed - Next.js uses relative URLs through Nginx
```

### Storage Configuration

By default, captures are saved to `~/wanda-telescope/captures`. To use USB storage:

1. Mount USB drive to `/media/usb` (or similar)
2. WANDA automatically detects mounted storage
3. Priority: USB → Home directory → Current directory

## Service Management

### Start/Stop/Restart

```bash
# Start services
sudo systemctl start wanda-backend.service wanda-frontend.service

# Stop services
sudo systemctl stop wanda-backend.service wanda-frontend.service

# Restart services (after code updates)
sudo systemctl restart wanda-backend.service wanda-frontend.service

# Restart Nginx (after config changes)
sudo systemctl restart nginx
```

### View Logs

```bash
# Follow backend logs in real-time
sudo journalctl -u wanda-backend.service -f

# Follow frontend logs in real-time
sudo journalctl -u wanda-frontend.service -f

# View recent logs
sudo journalctl -u wanda-backend.service -n 100
sudo journalctl -u wanda-frontend.service -n 100

# View logs since last boot
sudo journalctl -u wanda-backend.service -b
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot
sudo systemctl enable wanda-backend.service wanda-frontend.service

# Disable auto-start
sudo systemctl disable wanda-backend.service wanda-frontend.service
```

## Updating WANDA

### Pull Latest Changes

```bash
# Stop services
sudo systemctl stop wanda-backend.service wanda-frontend.service

# Pull updates
cd /home/admin/wanda-telescope
git pull

# Update backend dependencies (if requirements.txt changed)
source venv/bin/activate
pip install -r requirements.txt

# Rebuild frontend (if frontend code changed)
cd wanda-telescope
npm install  # Only if package.json changed
npm run build

# Restart services
sudo systemctl restart wanda-backend.service wanda-frontend.service
```

## Troubleshooting

### Backend Service Won't Start

**Check logs:**
```bash
sudo journalctl -u wanda-backend.service -n 50
```

**Common issues:**
- Python virtual environment missing → Recreate venv
- Camera not detected → Check `/boot/firmware/config.txt` and cable
- Port 5000 already in use → `sudo netstat -tulpn | grep 5000`
- Permission issues → Check user/group in service file

**Test manually:**
```bash
cd /home/admin/wanda-telescope
source venv/bin/activate
python main.py
```

### Frontend Service Won't Start

**Check logs:**
```bash
sudo journalctl -u wanda-frontend.service -n 50
```

**Common issues:**
- Node.js version < 20 → Reinstall Node.js 20.x
- Build artifacts missing → Run `npm run build`
- Port 3000 already in use → `sudo netstat -tulpn | grep 3000`
- npm not found → Install Node.js or fix PATH

**Test manually:**
```bash
cd /home/admin/wanda-telescope/wanda-telescope
npm start
```

### Nginx 502 Bad Gateway

**Diagnosis:**
```bash
# Check backend services are running
sudo systemctl status wanda-backend.service wanda-frontend.service

# Check Nginx error logs
sudo tail -f /var/log/nginx/wanda-error.log

# Verify services listening on correct ports
sudo netstat -tulpn | grep -E '3000|5000'
```

**Solutions:**
- Backend not running → Start backend service
- Frontend not running → Start frontend service
- Wrong ports in Nginx config → Edit `/etc/nginx/sites-available/wanda-telescope`
- Firewall blocking → Check `sudo iptables -L`

### WebSocket Connection Issues

**Symptoms:** UI loads but doesn't update in real-time

**Check:**
```bash
# Verify backend is running with SocketIO
sudo journalctl -u wanda-backend.service | grep -i socket

# Check browser console for WebSocket errors
# Open browser DevTools → Console → Look for connection errors

# Test WebSocket directly
curl http://localhost/socket.io/?transport=polling
```

**Solutions:**
- Backend not configured for WebSocket → Check `web/app.py` for SocketIO setup
- Nginx not proxying WebSocket → Verify `/socket.io` location in Nginx config
- CORS issues → Check `cors_allowed_origins` in `web/app.py`

### Camera Not Detected

```bash
# Check camera hardware
rpicam-still --list-cameras

# Check camera module is loaded
lsmod | grep -i camera

# Verify config.txt
cat /boot/firmware/config.txt | grep imx477

# Test with native tools
rpicam-still -o test.jpg

# Check backend logs
sudo journalctl -u wanda-backend.service | grep -i camera
```

### High Memory Usage

**Check resource usage:**
```bash
htop

# Or
free -h
ps aux | grep -E 'python|node'
```

**Typical usage:**
- Backend: 200-400MB
- Frontend: 300-600MB
- Nginx: 10-20MB
- Total: ~600-1000MB

**If memory is too high:**
- Restart services: `sudo systemctl restart wanda-backend wanda-frontend`
- Check for memory leaks in logs
- Reduce session capture frequency
- Close unused browser tabs

## Performance Optimization

### Frontend Build Optimization

```bash
cd wanda-telescope

# Production build with optimizations
npm run build

# Check bundle size
ls -lh .next/static/chunks/
```

### Backend Performance

The backend uses:
- **Eventlet** for concurrent connections
- **ThreadPoolExecutor** for camera operations
- **Selective monkey patching** to avoid blocking

No additional tuning needed for typical use.

### Nginx Caching (Optional)

Add to `/etc/nginx/sites-available/wanda-telescope`:

```nginx
# Cache static assets
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 7d;
    add_header Cache-Control "public, immutable";
}
```

## Security Considerations

### Network Access

By default, WANDA is accessible on local network only:
- Port 80 (HTTP) open to LAN
- No external access without port forwarding

### User Permissions

Services run as user `admin` (or your specified user):
- **Not root** for security
- Has access to camera and GPIO (required)
- Limited file system access

### Future Enhancements

For production deployment on internet:
1. Add HTTPS with Let's Encrypt
2. Implement authentication (JWT)
3. Use Cloudflare Tunnel or VPN
4. Rate limiting on API endpoints

## Backup and Recovery

### Backup Configuration

```bash
# Backup service files
sudo cp /etc/systemd/system/wanda-*.service ~/wanda-backup/

# Backup Nginx config
sudo cp /etc/nginx/sites-available/wanda-telescope ~/wanda-backup/

# Backup captures
rsync -av ~/wanda-telescope/captures/ ~/wanda-backup/captures/
```

### Recovery

```bash
# Restore service files
sudo cp ~/wanda-backup/wanda-*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Restore Nginx config
sudo cp ~/wanda-backup/wanda-telescope /etc/nginx/sites-available/
sudo nginx -t && sudo systemctl restart nginx
```

## Monitoring

### Health Checks

```bash
# Check if WANDA is responding
curl -s http://localhost/api/status | jq .

# Check uptime
systemctl status wanda-backend.service | grep Active
systemctl status wanda-frontend.service | grep Active

# Check disk space
df -h ~/wanda-telescope/captures/
```

### Automated Monitoring (Optional)

Create a monitoring script:

```bash
#!/bin/bash
# /home/admin/wanda-check.sh

# Check services are running
systemctl is-active --quiet wanda-backend.service || {
    echo "Backend down! Restarting..."
    sudo systemctl restart wanda-backend.service
}

systemctl is-active --quiet wanda-frontend.service || {
    echo "Frontend down! Restarting..."
    sudo systemctl restart wanda-frontend.service
}
```

Add to crontab:
```bash
crontab -e

# Check every 5 minutes
*/5 * * * * /home/admin/wanda-check.sh >> /var/log/wanda-monitor.log 2>&1
```

## Support

For issues and questions:
- **GitHub Issues**: https://github.com/AlterMundi/wanda-telescope/issues
- **Documentation**: `docs/` directory
- **Integration Plan**: `docs/archive/NEXTJS_INTEGRATION_PLAN.md`
- **Deadlock Fix**: `docs/archive/DEADLOCK_FIX_SUMMARY.md`

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**Compatible with:** WANDA feat/v0-ui branch

