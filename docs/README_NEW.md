WYND VPN

A multi-protocol VPN system for bypassing network restrictions on restricted networks like hostels and corporate WiFi.

Overview

WYND runs on an Oracle Cloud server (161.118.177.7) and provides multiple VPN protocols to ensure connectivity even on heavily restricted networks. The primary advantage is using TCP port 53 (DNS), which is rarely blocked since DNS is essential for network operation.

Features

- SoftEther VPN on multiple ports (TCP 53, 443, 992, 5555)
- WireGuard VPN (UDP 443)
- Web control panel showing VPN status
- Automatic protocol fallback for restricted networks

Quick Start

Connect via SoftEther (Recommended)

Host: 161.118.177.7
Port: 53 (TCP)
Hub: WYND
Username: wynduser
Password: wyndpass123

Install client:
- Android: SoftEther VPN Client app
- Windows: OpenVPN or SoftEther VPN Client
- macOS: OpenVPN or SoftEther

Connect via WireGuard

Port: UDP 443
Network: 10.66.66.0/24

Web Control Panel

URL: http://harshitsehgal.online
Shows: Active sessions, connection instructions, server status

Architecture

Oracle Cloud VM (Ubuntu 22.04)
├── SoftEther VPN Server
│   ├── TCP 53 (Primary)
│   ├── TCP 443 (SSTP)
│   ├── TCP 992
│   └── TCP 5555
├── WireGuard
│   └── UDP 443
├── Web Control Panel (FastAPI)
└── Nginx (Reverse Proxy)

Why TCP 53?

Most networks block everything except DNS traffic:
- TCP 53 is used for DNS queries
- DNS is essential infrastructure
- Almost never blocked by network admins
- TCP ensures reliable delivery

Project Structure

wynd-server/        Rust TCP tunnel server
wynd-client/        Python TCP tunnel client
index.html          Web UI
main.py             FastAPI control panel

Services Status

SoftEther (TCP 53)    ✓ Running
SoftEther (TCP 443)   ✓ Running
WireGuard (UDP 443)   ✓ Running
Web Panel (Port 8080) ✓ Running
Nginx Proxy (Port 80) ✓ Running

Configuration Files

wynd-openvpn-client-tcp53.ovpn    OpenVPN config (TCP 53)
wynd-openvpn-client-tcp443.ovpn   OpenVPN config (TCP 443)
openvpn-ca.crt                     CA certificate

Development

Run the Rust server:

cd wynd-server
cargo run

Run the Python client:

cd wynd-client/python
python3 client.py

Testing

test-server.py      Tests TCP connectivity to server
test-vpn.py         Tests VPN connection
check-ports.ps1     Checks if VPN ports are open

Firewall Rules (UFW)

Port 22 (SSH)    ✓ Open
Port 53 (TCP)    ✓ Open
Port 80 (HTTP)   ✓ Open
Port 443 (TCP+UDP) ✓ Open
Port 5555 (TCP)  ✓ Open
Port 9000 (TCP)  ✓ Open

Roadmap

- [ ] HTTPS/SSL certificate for web panel
- [ ] Auto-reconnect on connection loss
- [ ] Real-time bandwidth monitoring
- [ ] WireGuard client config download
- [ ] iOS support
- [ ] Speed test integration

Troubleshooting

Cannot connect to TCP 53?
Try alternative ports: 443, 992, or 5555

Web panel not loading?
Check server status: curl http://161.118.177.7:80

WireGuard not connecting?
Verify firewall allows UDP 443

Server Logs

SSH into server:
ssh -i key.pem ubuntu@161.118.177.7

View web panel logs:
tail -20 /home/ubuntu/wynd-web/app.log

Check VPN sessions:
sudo /usr/local/vpnserver/vpncmd localhost /HUB:WYND /CMD SessionList

License

MIT
