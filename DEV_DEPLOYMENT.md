# 🚀 WANDA Development Deployment Guide

Quick setup guide for deploying WANDA with auto-initialization to multiple Raspberry Pi devices during development.

## 📦 One-Command Deployment

### For Fresh Raspberry Pi Setup:
```bash
curl -sSL https://raw.githubusercontent.com/AlterMundi/wanda-telescope/feat/auto-initialization/scripts/deploy-to-pi.sh | bash
```

This single command will:
- ✅ Clone the `feat/auto-initialization` branch
- ✅ Set up Python environment and dependencies  
- ✅ Install auto-startup service
- ✅ Test the installation
- ✅ Configure for boot-time startup

## 🔧 Manual Deployment Steps

If you prefer step-by-step control:

### 1. Clone the Development Branch
```bash
git clone -b feat/auto-initialization https://github.com/AlterMundi/wanda-telescope.git
cd wanda-telescope
```

### 2. Setup Environment
```bash
./run-wanda.sh  # Sets up venv and dependencies
```

### 3. Install Auto-Startup
```bash
sudo ./scripts/install-service.sh
```

### 4. Test Installation
```bash
sudo systemctl start wanda-telescope
sudo systemctl status wanda-telescope
```

## 🔍 Finding Your Pi's IP

### From Another Computer:
```bash
# Download discovery script
curl -O https://raw.githubusercontent.com/AlterMundi/wanda-telescope/feat/auto-initialization/scripts/find-wanda.py

# Run discovery
python3 find-wanda.py
```

### From the Pi (via SSH):
```bash
hostname -I
```

## 🧪 Development Workflow

### Update to Latest Changes:
```bash
cd ~/repos/wanda-telescope
git pull origin feat/auto-initialization
sudo systemctl restart wanda-telescope
```

### Test Manual Mode:
```bash
sudo systemctl stop wanda-telescope
./run-wanda.sh
```

### Check Logs:
```bash
sudo journalctl -u wanda-telescope -f
```

### Remove Auto-Startup (for testing):
```bash
sudo ./scripts/uninstall-service.sh
```

## 🏠 Multiple Pi Management

### Pi Naming Convention:
```bash
# Rename each Pi for easy identification
sudo hostnamectl set-hostname wanda-pi-01
# Access via: http://wanda-pi-01.local:5000
```

### Quick Status Check:
```bash
# Check if WANDA is running
curl -s http://localhost:5000 | grep -q "Wanda" && echo "✅ WANDA Running" || echo "❌ WANDA Not Running"
```

## 📋 Development Checklist

### New Pi Setup:
- [ ] Flash Raspberry Pi OS
- [ ] Enable SSH and camera interface
- [ ] Connect to WiFi
- [ ] Run deployment script
- [ ] Test auto-startup (reboot)
- [ ] Verify IP discovery works

### Code Changes Testing:
- [ ] Pull latest changes
- [ ] Restart service
- [ ] Test web interface
- [ ] Check logs for errors
- [ ] Verify auto-startup still works

## 🚨 Troubleshooting

### Service Won't Start:
```bash
sudo systemctl status wanda-telescope --no-pager
sudo journalctl -u wanda-telescope -n 20
```

### Environment Issues:
```bash
cd ~/repos/wanda-telescope
./run-wanda.sh  # Re-run setup
```

### Discovery Issues:
```bash
# Check network info
cat /var/log/wanda-network-info.txt

# Manual IP check
hostname -I
```

### Reset Everything:
```bash
sudo ./scripts/uninstall-service.sh
rm -rf ~/repos/wanda-telescope
# Then re-run deployment script
```

## 🌐 Network Setup Tips

### For Multiple Pis:
1. **Use DHCP reservations** in router (by MAC address)
2. **Set unique hostnames** for each Pi
3. **Document IP assignments** for team reference

### For Remote Access:
1. **Port forwarding** on router (Pi_IP:5000 → external:5000)
2. **VPN setup** for secure remote access
3. **Dynamic DNS** for permanent URLs

## 🔄 Branch Management

### Current Branch: `feat/auto-initialization`
- This is our development branch for auto-startup features
- Safe to deploy to test Pis
- Not yet merged to main (intentionally)

### When Ready for Production:
- Thorough testing on multiple Pis
- Documentation review
- Merge to main branch
- Tag release version

---

**🎯 Goal**: Easy, reliable deployment to multiple Raspberry Pis during development phase while maintaining isolated feature branch.