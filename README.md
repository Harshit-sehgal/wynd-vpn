# WYND VPN (v2)

WYND is a custom VPN solution designed specifically to bypass highly restricted WiFi networks (hostels, corporate environments, cafes) by tunneling all traffic over a single TCP connection on Port 53.

## Current Status (May 2026)

| Component | Status | Location |
|-----------|--------|----------|
| Rust Server | **Deployed & Running** | Oracle VM (161.118.177.7:53) |
| Android Client | Code Ready | `clients/android/` (needs Android Studio build) |
| Desktop Client | Test Mode | `clients/desktop/` |
| Server Tests | **All Passing** | 6/6 tests passed |

## Features

- **Port 53 Penetration:** Uses TCP port 53 (DNS), which is almost universally left open on restricted captive portals.
- **Custom Protocol:** A lightweight, low-overhead framing protocol designed specifically for TCP streams.
- **Android First:** Includes a native Android client using `VpnService` for one-tap connection.
- **Desktop Client:** Python-based test client available.

## Architecture & Documentation

Please refer to the following documents in the `docs/` folder:
- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md): System design, components, and trade-offs.
- [`TCP53_PROTOCOL.md`](docs/TCP53_PROTOCOL.md): Custom stream framing protocol specification.
- [`DEPLOYMENT.md`](docs/DEPLOYMENT.md): Guide to deploying the server.
- [`PROJECT_INFO.md`](docs/PROJECT_INFO.md): Legacy (v1) project setup and server credentials.

## Repository Structure

```
├── clients/
│   ├── android/           # WYND v2 Android Client (VpnService)
│   └── desktop/           # Desktop test clients (Python)
├── docs/                  # Technical documentation
├── infra/                 # Legacy infrastructure config and certs
├── legacy/                # Old v1 web panel and SoftEther scripts
├── server/
│   └── wynd-tcp53d/       # Rust daemon (TCP-53 tunnel server)
└── tests/                 # Server test scripts
```

## Quick Start

### Test the Server

```bash
# Test connectivity to production server
python tests/test-protocol.py 161.118.177.7

# Run comprehensive tests
python tests/test-comprehensive.py 161.118.177.7
```

### Run Desktop Client

```bash
python clients/desktop/wynd-quick.py
```

### Build Android App

1. Open `clients/android/` in Android Studio
2. Build the APK
3. Install on Android device
4. Configure server IP in `WyndVpnService.kt` to `161.118.177.7`

## Legacy Services (v1)

SoftEther is still available on ports **443/992/5555** for full VPN functionality. The new WYND v2 server is now on port **53**.

## Development Phases Completed

- Phase 0: Repository reorganization and documentation
- Phase 1: Rust server on port 9000 (development)
- Phase 2: Android MVP with VpnService
- Phase 3: Deploy server to Oracle VM on port 53

## License

MIT