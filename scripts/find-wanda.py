#!/usr/bin/env python3
"""
WANDA Telescope Discovery Script
Run this on any computer to find WANDA telescopes on the network
"""

import socket
import subprocess
import platform
import re
import time
import sys
from concurrent.futures import ThreadPoolExecutor
import argparse

def print_banner():
    print("🔭 WANDA Telescope Discovery Tool")
    print("=" * 40)

def get_local_network():
    """Get the local network range"""
    try:
        # Get default gateway
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            # Parse Windows ipconfig output
            lines = result.stdout.split('\n')
            for line in lines:
                if 'IPv4 Address' in line:
                    ip = line.split(':')[1].strip()
                    if ip.startswith('192.168.') or ip.startswith('10.'):
                        network = '.'.join(ip.split('.')[:-1]) + '.0/24'
                        return network
        else:
            # Linux/Mac
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'default' in line:
                    # Extract gateway IP
                    gateway = line.split()[2]
                    network = '.'.join(gateway.split('.')[:-1]) + '.0/24'
                    return network
    except:
        pass
    
    # Fallback common networks
    return ['192.168.1.0/24', '192.168.0.0/24', '10.0.0.0/24']

def check_wanda_service(ip, port=5000, timeout=1):
    """Check if WANDA service is running on given IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            # Try to get the page title to confirm it's WANDA
            try:
                import urllib.request
                req = urllib.request.Request(f'http://{ip}:{port}', 
                                           headers={'User-Agent': 'WANDA-Discovery'})
                with urllib.request.urlopen(req, timeout=2) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    if 'Wanda' in content or 'WANDA' in content:
                        return True
            except:
                pass
            return True  # Port is open, likely WANDA
        return False
    except:
        return False

def ping_host(ip, timeout=1):
    """Ping a host to check if it's alive"""
    try:
        if platform.system() == "Windows":
            cmd = ['ping', '-n', '1', '-w', str(timeout * 1000), ip]
        else:
            cmd = ['ping', '-c', '1', '-W', str(timeout), ip]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def scan_network_range(network_range, max_workers=50):
    """Scan network range for WANDA telescopes"""
    print(f"🔍 Scanning network: {network_range}")
    
    # Generate IP list
    if isinstance(network_range, str):
        if '/' in network_range:
            base_ip = network_range.split('/')[0]
            base = '.'.join(base_ip.split('.')[:-1])
            ips = [f"{base}.{i}" for i in range(1, 255)]
        else:
            ips = [network_range]
    else:
        # Multiple networks
        ips = []
        for net in network_range:
            base_ip = net.split('/')[0]
            base = '.'.join(base_ip.split('.')[:-1])
            ips.extend([f"{base}.{i}" for i in range(1, 255)])
    
    wanda_devices = []
    
    def check_ip(ip):
        if ping_host(ip, timeout=0.5):
            if check_wanda_service(ip):
                return ip
        return None
    
    print(f"⏳ Checking {len(ips)} IP addresses...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(check_ip, ips)
        wanda_devices = [ip for ip in results if ip is not None]
    
    return wanda_devices

def get_device_info(ip, port=5000):
    """Get additional info about the WANDA device"""
    try:
        # Try to get hostname
        hostname = socket.gethostbyaddr(ip)[0]
    except:
        hostname = "Unknown"
    
    return {
        'ip': ip,
        'port': port,
        'hostname': hostname,
        'url': f'http://{ip}:{port}'
    }

def listen_for_broadcasts(timeout=5):
    """Listen for UDP broadcasts from WANDA devices"""
    print(f"📡 Listening for WANDA broadcasts ({timeout}s)...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 8888))
        sock.settimeout(timeout)
        
        broadcasts = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode('utf-8')
                if message.startswith('WANDA_TELESCOPE:'):
                    parts = message.split(':')
                    if len(parts) >= 4:
                        broadcasts.append({
                            'ip': parts[2],
                            'hostname': parts[1],
                            'port': parts[3],
                            'url': f'http://{parts[2]}:{parts[3]}'
                        })
                        print(f"📢 Received broadcast from {parts[1]} ({parts[2]})")
            except socket.timeout:
                continue
            except:
                break
        
        sock.close()
        return broadcasts
    except:
        return []

def discover_mdns():
    """Try to discover via mDNS/Bonjour"""
    print("🌐 Checking mDNS/Bonjour...")
    
    try:
        if platform.system() == "Windows":
            # Windows: try dns-sd
            result = subprocess.run(['dns-sd', '-B', '_http._tcp'], 
                                  capture_output=True, text=True, timeout=3)
        else:
            # Linux: try avahi-browse
            result = subprocess.run(['avahi-browse', '-rt', '_http._tcp'], 
                                  capture_output=True, text=True, timeout=3)
        
        if 'WANDA' in result.stdout or 'wanda' in result.stdout:
            print("✅ Found WANDA via mDNS")
            return True
    except:
        pass
    
    return False

def main():
    parser = argparse.ArgumentParser(description='Discover WANDA Telescopes on the network')
    parser.add_argument('--network', help='Network range to scan (e.g., 192.168.1.0/24)')
    parser.add_argument('--broadcast-only', action='store_true', 
                       help='Only listen for broadcasts, skip network scan')
    parser.add_argument('--timeout', type=int, default=5, 
                       help='Timeout for broadcast listening (default: 5s)')
    
    args = parser.parse_args()
    
    print_banner()
    
    all_devices = []
    
    # Method 1: Listen for broadcasts
    broadcasts = listen_for_broadcasts(args.timeout)
    all_devices.extend(broadcasts)
    
    if not args.broadcast_only:
        # Method 2: Network scan
        network = args.network if args.network else get_local_network()
        wanda_ips = scan_network_range(network)
        
        for ip in wanda_ips:
            # Avoid duplicates from broadcasts
            if not any(d['ip'] == ip for d in all_devices):
                device_info = get_device_info(ip)
                all_devices.append(device_info)
        
        # Method 3: mDNS discovery
        discover_mdns()
    
    # Display results
    print("\n" + "=" * 40)
    if all_devices:
        print(f"🎯 Found {len(all_devices)} WANDA Telescope(s):")
        print()
        
        for i, device in enumerate(all_devices, 1):
            print(f"  {i}. {device['hostname']} ({device['ip']})")
            print(f"     URL: {device['url']}")
            print()
        
        print("🌐 Access any of the URLs above in your web browser!")
    else:
        print("❌ No WANDA Telescopes found on the network")
        print()
        print("💡 Troubleshooting tips:")
        print("   1. Make sure WANDA is running on the Raspberry Pi")
        print("   2. Check that both devices are on the same network")
        print("   3. Try running with specific network: --network 192.168.1.0/24")
        print("   4. Check firewall settings")

if __name__ == "__main__":
    main()