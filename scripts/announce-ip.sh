#!/bin/bash

# WANDA Telescope IP Address Announcement Script
# This script announces the Pi's IP address in multiple ways

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Get the primary IP address
get_primary_ip() {
    # Try multiple methods to get IP
    local ip=""
    
    # Method 1: Using hostname -I (gets all IPs)
    ip=$(hostname -I | awk '{print $1}')
    
    # Method 2: Using ip route (more reliable for primary interface)
    if [ -z "$ip" ] || [ "$ip" = "127.0.0.1" ]; then
        ip=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7}' | head -1)
    fi
    
    # Method 3: Using ifconfig as fallback
    if [ -z "$ip" ] || [ "$ip" = "127.0.0.1" ]; then
        ip=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1' | head -1)
    fi
    
    echo "$ip"
}

# Get hostname
get_hostname() {
    hostname
}

# Announce IP via multiple methods
announce_ip() {
    local ip=$(get_primary_ip)
    local hostname=$(get_hostname)
    local port="5000"
    
    if [ -z "$ip" ]; then
        print_warning "Could not determine IP address"
        return 1
    fi
    
    print_success "=== WANDA Telescope Network Information ==="
    echo
    print_info "Hostname: $hostname"
    print_info "IP Address: $ip"
    print_info "Web Interface: http://$ip:$port"
    echo
    
    # Method 1: Write to log file
    local info_file="/var/log/wanda-network-info.txt"
    {
        echo "WANDA Telescope Network Information"
        echo "Generated: $(date)"
        echo "Hostname: $hostname"
        echo "IP Address: $ip"
        echo "Web Interface: http://$ip:$port"
        echo "Local Access: http://localhost:$port"
    } | sudo tee "$info_file" > /dev/null
    
    print_success "Network info saved to: $info_file"
    
    # Method 2: Broadcast via UDP (if netcat is available)
    if command -v nc >/dev/null 2>&1; then
        print_info "Broadcasting IP via UDP..."
        echo "WANDA_TELESCOPE:$hostname:$ip:$port" | nc -b -u 255.255.255.255 8888 2>/dev/null || true
    fi
    
    # Method 3: Try to register with Bonjour/Avahi (if available)
    if command -v avahi-publish >/dev/null 2>&1; then
        print_info "Registering with Avahi/Bonjour..."
        avahi-publish -s "WANDA Telescope" _http._tcp 5000 "path=/wanda" &
        echo $! > /tmp/wanda-avahi.pid
    fi
    
    # Method 4: Create QR code if qrencode is available
    if command -v qrencode >/dev/null 2>&1; then
        print_info "Generating QR code..."
        qrencode -t ansiutf8 "http://$ip:$port" 2>/dev/null || print_warning "QR code generation failed"
    fi
    
    # Method 5: Write to shared network location if possible
    local network_share="/media/usb"
    if [ -d "$network_share" ] && [ -w "$network_share" ]; then
        echo "http://$ip:$port" > "$network_share/wanda-telescope-url.txt"
        print_success "URL saved to USB drive: $network_share/wanda-telescope-url.txt"
    fi
    
    return 0
}

# Show discovery methods for other computers
show_discovery_methods() {
    echo
    print_success "=== Discovery Methods for Other Computers ==="
    echo
    print_info "Method 1: Network Scan"
    print_info "  Run: nmap -sn 192.168.1.0/24 | grep -B2 'Raspberry Pi'"
    print_info "  Or: arp -a | grep -i 'raspberry\\|b8:27:eb\\|dc:a6:32\\|e4:5f:01'"
    echo
    print_info "Method 2: Hostname Resolution"
    print_info "  Try: http://$(get_hostname).local:5000"
    print_info "  Or: ping $(get_hostname).local"
    echo
    print_info "Method 3: Router/DHCP Client List"
    print_info "  Check your router's admin panel for connected devices"
    print_info "  Look for 'Raspberry Pi' or hostname '$(get_hostname)'"
    echo
    print_info "Method 4: UDP Listener (if implemented)"
    print_info "  Run: nc -l -u 8888"
    print_info "  Wait for broadcast message with WANDA info"
    echo
    print_info "Method 5: Bonjour/mDNS Discovery"
    print_info "  Run: avahi-browse -rt _http._tcp"
    print_info "  Or use Bonjour Browser app on mobile devices"
    echo
}

# Main function
main() {
    print_info "WANDA Telescope IP Address Announcement"
    echo
    
    if announce_ip; then
        show_discovery_methods
        
        echo
        print_success "IP announcement completed successfully!"
        print_info "Other computers can now discover this WANDA telescope."
    else
        print_warning "IP announcement failed. Check network connectivity."
        exit 1
    fi
}

# Run main function
main "$@"