# WYND VPN (v2)

WYND is a custom VPN solution designed to bypass highly restricted WiFi networks (hostels, corporate, cafes) by tunneling all traffic over TCP port 53.

## Current Status (May 2026) - ✅ WORKING

| Component | Status | Location |
|-----------|--------|----------|
| **Server** | Running & Forwarding | Oracle VM (161.118.177.7:53) |
| **Linux Client** | Ready to Use | `clients/linux/wynd-linux-vpn.py` |
| **Android Client** | Code Ready | `clients/android/` (build in Android Studio) |
| **Windows** | SOCKS Proxy | `clients/desktop/WyndVPNFull.exe` |

## Features

- **Port 53 Penetration:** Works on networks that only allow DNS port
- **Full VPN:** Routes all traffic through server to internet
- **Platform Support:** Linux, Android, Windows (SOCKS)
- **Custom Protocol:** Lightweight TCP framing

## Quick Start

### Linux (Recommended)
```bash
git clone https://github.com/Harshit-sehgal/wynd-vpn.git
cd wynd-vpn/clients/linux
sudo python3 wynd-linux-vpn.py
```

### Android
1. Open `clients/android/` in Android Studio
2. Build APK → Install → Connect

### Windows
1. Download `WyndVPNFull.exe` from `clients/desktop/dist/`
2. Run → Configure app to use SOCKS5 proxy `127.0.0.1:1080`
3. Or use proxychains: `proxychains your_app.exe`

## Server Details

- **IP:** 161.118.177.7
- **Port:** 53 (TCP)
- **Protocol:** Custom WYND framing

## Architecture

```
User Device → TCP:53 → Oracle VM → Internet
                 ↓
            TUN Interface (Linux/Android)
```

## Documentation

See `docs/` folder:
- `ARCHITECTURE.md` - System design
- `TCP53_PROTOCOL.md` - Protocol spec
- `DEPLOYMENT.md` - Server deployment

## License

MIT