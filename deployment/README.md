# WANDA Deployment Files

This directory contains systemd service files and Nginx configuration for production deployment of WANDA Telescope.

## Files

- `wanda-backend.service` - Systemd service for Flask backend (port 5000)
- `wanda-frontend.service` - Systemd service for Next.js frontend (port 3000)
- `wanda-telescope.nginx` - Nginx reverse proxy configuration (port 80)

## Installation

### 1. Install Systemd Services

```bash
# Copy service files
sudo cp deployment/wanda-backend.service /etc/systemd/system/
sudo cp deployment/wanda-frontend.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable services (auto-start on boot)
sudo systemctl enable wanda-backend.service
sudo systemctl enable wanda-frontend.service

# Start services
sudo systemctl start wanda-backend.service
sudo systemctl start wanda-frontend.service

# Check status
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service
```

### 2. Install Nginx Configuration

```bash
# Copy Nginx configuration
sudo cp deployment/wanda-telescope.nginx /etc/nginx/sites-available/wanda-telescope

# Enable the site
sudo ln -s /etc/nginx/sites-available/wanda-telescope /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Customization

If your installation path differs from `/home/admin/wanda-telescope`, update:

1. `WorkingDirectory` in both service files
2. `ExecStart` paths in both service files  
3. `alias` path in the nginx configuration for `/captures` location
4. `User` and `Group` in service files if running as different user

## Service Management

```bash
# Start services
sudo systemctl start wanda-backend.service wanda-frontend.service

# Stop services
sudo systemctl stop wanda-backend.service wanda-frontend.service

# Restart services
sudo systemctl restart wanda-backend.service wanda-frontend.service

# Check status
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service

# View logs
sudo journalctl -u wanda-backend.service -f
sudo journalctl -u wanda-frontend.service -f
```

## Troubleshooting

### Services won't start

Check logs for errors:
```bash
sudo journalctl -u wanda-backend.service -n 50
sudo journalctl -u wanda-frontend.service -n 50
```

Verify Python environment:
```bash
cd /home/admin/wanda-telescope
source venv/bin/activate
python main.py  # Test manually
```

Verify Node.js build:
```bash
cd /home/admin/wanda-telescope/wanda-telescope
npm run build  # Rebuild if needed
```

### Nginx 502 Bad Gateway

Ensure backend services are running:
```bash
sudo systemctl status wanda-backend.service
sudo systemctl status wanda-frontend.service
```

Check Nginx error logs:
```bash
sudo tail -f /var/log/nginx/wanda-error.log
```

Verify services are listening on correct ports:
```bash
sudo netstat -tulpn | grep -E '3000|5000'
```

