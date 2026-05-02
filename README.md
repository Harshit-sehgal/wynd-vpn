# WYND VPN

A multi-protocol VPN system for connecting through restricted networks like hostels and corporate WiFi.

## Features

- SoftEther VPN on TCP 53 (works where other VPNs don't)
- Multiple fallback ports (443, 992, 5555)
- WireGuard UDP 443 support
- Web control panel at http://harshitsehgal.online
- Automatic protocol detection

## Quick Start

### SoftEther (Recommended)

Host: `161.118.177.7:53`
Hub: `WYND`
User: `wynduser`
Pass: `wyndpass123`

Download: SoftEther VPN Client (Android/Windows) or OpenVPN compatible clients

### WireGuard

Port: UDP 443
Network: 10.66.66.0/24

### Web Panel

View active connections and get setup instructions:
http://harshitsehgal.online

## Why TCP 53?

Most restrictive networks block everything except DNS (port 53):
- DNS is essential for network operation
- Rarely blocked by network admins
- TCP provides reliable delivery
- Works on hostels, airports, corporate networks

## Architecture

```
Oracle Cloud VM (161.118.177.7)
├── SoftEther (TCP 53, 443, 992, 5555)
├── WireGuard (UDP 443)
├── Web Panel (FastAPI)
└── Nginx Reverse Proxy
```

## Project Structure

```
wynd-server/           Rust TCP tunnel server
wynd-client/python/    Python client implementation
index.html            Web UI
main.py               FastAPI backend
```

## Services

| Service | Port | Protocol | Status |
|---------|------|----------|--------|
| SoftEther | 53 | TCP | ✓ |
| SoftEther | 443 | TCP | ✓ |
| SoftEther | 992 | TCP | ✓ |
| SoftEther | 5555 | TCP | ✓ |
| WireGuard | 443 | UDP | ✓ |
| Web Panel | 8080 | HTTP | ✓ |

## Development

Build the Rust server:

```bash
cd wynd-server
cargo run
```

Run the Python client:

```bash
cd wynd-client/python
python3 client.py
```

Test connectivity:

```bash
python3 test-server.py
```

## Server Info

SSH: `ubuntu@161.118.177.7`
Domain: `harshitsehgal.online`
OS: Ubuntu 22.04 LTS

## Troubleshooting

**Can't connect to port 53?**
Try ports 443, 992, or 5555

**Web panel not loading?**
Check: `curl http://161.118.177.7`

**WireGuard connection issues?**
Verify firewall allows UDP 443

## Documentation

See `PROJECT_INFO.md` for detailed setup and architecture documentation.

## License

MIT