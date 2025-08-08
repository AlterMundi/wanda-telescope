# 🔍 WANDA Telescope Network Discovery Guide

When your Raspberry Pi boots up and starts WANDA automatically, here's how to find its IP address and access it from other computers:

## 🚀 Quick Start Methods

### Method 1: Discovery Script (Recommended)
Download and run the discovery script on any computer:

```bash
# Download the script
curl -O https://raw.githubusercontent.com/AlterMundi/wanda-telescope/feat/auto-initialization/scripts/find-wanda.py

# Make it executable (Linux/Mac)
chmod +x find-wanda.py

# Run the discovery
python3 find-wanda.py
```

**Windows:**
```cmd
python find-wanda.py
```

This will automatically scan your network and show all WANDA telescopes with their URLs.

### Method 2: Check Router/Network Interface
1. Open your router's admin panel (usually `192.168.1.1` or `192.168.0.1`)
2. Look for "Connected Devices" or "DHCP Client List"
3. Find device named `astro2` or "Raspberry Pi"
4. Note the IP address and access: `http://[IP]:5000`

### Method 3: Network Scan
**Linux/Mac:**
```bash
# Scan local network for Raspberry Pi devices
nmap -sn 192.168.1.0/24 | grep -B2 "Raspberry Pi"

# Or check ARP table
arp -a | grep -i "raspberry\|b8:27:eb\|dc:a6:32\|e4:5f:01"
```

**Windows:**
```cmd
# Use Advanced IP Scanner or similar tool
# Or check ARP table
arp -a | findstr "b8-27-eb"
```

### Method 4: Hostname Resolution (if mDNS works)
Try accessing: `http://astro2.local:5000`

## 📱 Mobile Discovery

### Android/iOS Apps:
- **Network Analyzer** - Scan for devices on port 5000
- **Fing** - Network scanner, look for Raspberry Pi devices
- **Bonjour Browser** - Look for WANDA services

## 🔍 Detailed Discovery Methods

### Advanced Network Scanning

**Scan specific network range:**
```bash
python3 find-wanda.py --network 192.168.1.0/24
```

**Listen for broadcasts only:**
```bash
python3 find-wanda.py --broadcast-only --timeout 10
```

### Manual Port Scanning
If you know the approximate IP range:

```bash
# Check common IP ranges for port 5000
for ip in 192.168.1.{1..254}; do
    timeout 1 bash -c "echo >/dev/tcp/$ip/5000" 2>/dev/null && echo "WANDA found at $ip"
done
```

### Using nmap for port scanning:
```bash
nmap -p 5000 192.168.1.0/24 | grep -B4 "5000/tcp open"
```

## 🖥️ What You'll See

When WANDA starts up automatically, it:

1. **Announces its presence** via multiple methods
2. **Saves network info** to `/var/log/wanda-network-info.txt`
3. **Broadcasts UDP messages** that discovery tools can catch
4. **Registers with mDNS/Bonjour** (if available)

### Example Network Info File:
```
WANDA Telescope Network Information
Generated: Fri Aug  8 23:36:30 BST 2025
Hostname: astro2
IP Address: 10.42.0.10
Web Interface: http://10.42.0.10:5000
Local Access: http://localhost:5000
```

## 🛠️ Troubleshooting

### Can't Find WANDA?
1. **Check Pi is running**: Look for the device in your router's device list
2. **Verify network**: Ensure both devices are on the same WiFi/network
3. **Check firewall**: Disable firewall temporarily on searching computer
4. **Try different ranges**: Your network might use different IP ranges (10.0.0.x, 172.16.x.x)

### Service Not Running?
```bash
# On the Pi, check service status
sudo systemctl status wanda-telescope

# Restart if needed
sudo systemctl restart wanda-telescope
```

### Manual IP Check on Pi:
```bash
# SSH to the Pi and run:
hostname -I
ip route get 1.1.1.1 | awk '{print $7}'
```

## 📋 Common IP Ranges

Most home networks use one of these ranges:
- `192.168.1.x` (most common)
- `192.168.0.x` (also common)
- `10.0.0.x` (some routers)
- `172.16.x.x` (less common)

## 🔐 Security Notes

- WANDA runs on port 5000 (HTTP, not HTTPS)
- No authentication required by default
- Ensure you're on a trusted network
- Consider setting up a VPN for remote access

## 🎯 Success!

Once you find the IP, bookmark: `http://[PI_IP]:5000`

The WANDA telescope interface will be available for:
- 📷 Camera control and live preview
- 🎯 Capture sessions and astrophotography
- ⚙️ System monitoring and configuration
- 📊 Session history and image management

---

**Need Help?** The discovery script provides the most reliable method and includes troubleshooting guidance.