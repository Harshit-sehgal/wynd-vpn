# WYND VPN - Linux Quick Start

## Requirements
- Linux machine (Ubuntu, Debian, etc.)
- Root access (sudo)
- Python 3

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/Harshit-sehgal/wynd-vpn.git
cd wynd-vpn

# 2. Go to Linux client directory
cd clients/linux

# 3. Run the VPN (requires root for TUN device)
sudo python3 wynd-linux-vpn.py
```

## How It Works

1. Creates a TUN network interface (tun0) with IP 10.0.0.2
2. Routes all system traffic through the TUN interface
3. Sends all traffic through port 53 to WYND server
4. Server forwards to the real internet

## Output

```
==================================================
WYND VPN - Linux Client
==================================================
Creating TUN device...
TUN device tun0 created: 10.0.0.2/24
Connecting to 161.118.177.7:53...
Server connected: b'VPN1'
VPN is running!
TUN: tun0 (10.0.0.2/24)
Server: 161.118.177.7:53

All system traffic is now routed through the VPN
Press Ctrl+C to stop
```

## Troubleshooting

- **Permission denied?** Run with `sudo`
- **TUN device error?** Your kernel may not support TUN. Check: `cat /dev/net/tun`

## Stopping

Press `Ctrl+C` - the script will clean up routing automatically.