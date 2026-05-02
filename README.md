# WYND VPN (v2)

WYND is a custom VPN solution designed specifically to bypass highly restricted WiFi networks (hostels, corporate environments, cafes) by tunneling all traffic over a single TCP connection on Port 53.

**Note:** This repository is currently transitioning from a legacy SoftEther/WireGuard setup (v1) to a custom-built Rust/Android architecture (v2).

## Features

- **Port 53 Penetration:** Uses TCP port 53 (DNS), which is almost universally left open on restricted captive portals.
- **Custom Protocol:** A lightweight, low-overhead framing protocol designed specifically for TCP streams.
- **Android First:** Includes a native Android client using `VpnService` for one-tap connection without complex configurations.

## Architecture & Documentation

Please refer to the following documents in the `docs/` folder for detailed technical information:
- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md): System design, components, and trade-offs.
- [`TCP53_PROTOCOL.md`](docs/TCP53_PROTOCOL.md): Custom stream framing protocol specification.
- [`PROJECT_INFO.md`](docs/PROJECT_INFO.md): Legacy (v1) project setup, infrastructure, and server credentials.

## Repository Structure

```
├── clients/          # Native clients (Android, etc.)
│   └── android/      # WYND v2 Android Client
├── docs/             # Technical documentation
├── infra/            # Legacy infrastructure config and certs
├── legacy/           # Old v1 web panel and SoftEther scripts
├── server/           # Backend server implementations
│   └── wynd-tcp53d/  # Rust daemon handling the custom TCP-53 protocol
└── tests/            # Connectivity test scripts
```

## Legacy Services (v1)

The legacy infrastructure (SoftEther on TCP 53/443/5555 and WireGuard on UDP 443) remains operational during the v2 transition. See `docs/PROJECT_INFO.md` for connection details to the legacy server.

## Current Development Phase

We are currently building **Phase 1 & Phase 2** of the new architecture:
1. Building the `wynd-tcp53d` server in Rust (currently testing on port 9000).
2. Developing the Android MVP to interface with the new server protocol.

## License

MIT
