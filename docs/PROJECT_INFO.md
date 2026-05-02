# WYND VPN - Complete Project Documentation

## IMPORTANT UPDATE (May 2026) - WYND v2

The WYND v2 custom VPN is now **deployed and running**!

### v2 Status
- **Rust Server:** Running on Oracle VM (161.118.177.7:53)
- **Protocol:** Custom TCP framing protocol (2-byte length header)
- **Testing:** All 6 tests passed
- **Clients:** Android (code ready), Desktop (test mode)

### Connection Details for v2
- Server: `161.118.177.7`
- Port: `53` (TCP)
- Protocol: Custom WYND framing (see docs/TCP53_PROTOCOL.md)

---

## PROJECT OVERVIEW (v1)

### What Are We Building?

WYND is a **multi-protocol VPN control panel** and server infrastructure that allows users to connect to a remote Oracle Cloud server through various VPN protocols, primarily for bypassing network restrictions (like hostel WiFi that blocks certain ports).

### Current Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WYND VPN SYSTEM                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────┐           │
│   │              ORACLE CLOUD VM (Ubuntu)               │           │
│   │              161.118.177.7                    │           │
│   │                                             │           │
│   │  ┌─────────────────────────────────────────┐  │           │
│   │  │    SOFTEETHER VPN SERVER             │  │           │
│   │  │    Port: TCP 53 (DNS)              │  │           │
│   │  │    Port: TCP 443 (SSTP)           │  │           │
│   │  │    Port: TCP 992                  │  │           │
│   │  │    Port: TCP 5555                 │  │           │
│   │  │    Hub: WYND                    │  │           │
│   │  │    User: wynduser             │  │           │
│   │  └─────────────────────────────────┘  │           │
│   │                                             │           │
│   │  ┌─────────────────────────────────────────┐  │           │
│   │  │    WIREGUARD VPN                    │  │           │
│   │  │    Port: UDP 443                 │  │           │
│   │  │    Subnet: 10.66.66.0/24       │  │           │
│   │  └─────────────────────────────────┘  │           │
│   │                                             │           │
│   │  ┌─────────────────────────────────────────┐  │           │
│   │  │    WYND CONTROL PANEL (Web App)        │  │           │
│   │  │    Port: 8080 (Python/FastAPI)       │  │           │
│   │  │    Proxy: Nginx :80                 │  │           │
│   │  │    Domain: harshitsehgal.online      │  │           │
│   │  └─────────────────────────────────┘  │           │
│   │                                             │           │
│   │  ┌─────────────────────────────────────────┐  │           │
│   │  │    WYND PROXY (Original)            │  │           │
│   │  │    Port: TCP 9000               │  │           │
│   │  └─────────────────────────────────┘  │           │
│   └──────────────────────────────────────────────────────────────┘           │
│                                                                         │
│   ┌──────────────────────────────────────────────────────────────┐           │
│   │              USER DEVICES                                │           │
│   │                                                     │           │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │           │
│   │  │ Android  │  │ Windows │  │  iOS    │         │           │
│   │  │Phone    │  │   PC    │  │        │         │           │
│   │  │SoftEther│  │SSTP/WG  │  │        │         │           │
│   │  │Client  │  │Built-in │  │        │         │           │
│   │  └────────┘  └──────────┘  └──────────┘         │           │
│   └──────────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

## WHAT HAS BEEN DONE

### 1. Oracle Cloud Server Setup
- Ubuntu 22.04.5 LTS VM on Oracle Cloud (AP-Mumbai-1)
- Public IP: 161.118.177.7
- SSH access configured with key-based authentication

### 2. VPN Services Installed and Running

| Service | Port | Protocol | Status | Config |
|---------|------|----------|--------|--------|
| SoftEther | 53 | TCP | ✅ Running | WYND hub, wynduser |
| SoftEther | 443 | TCP (SSTP) | ✅ Running | WYND hub |
| SoftEther | 992 | TCP | ✅ Running | Alternative port |
| SoftEther | 5555 | TCP | ✅ Running | Alternative port |
| WireGuard | 443 | UDP | ✅ Running | 10.66.66.0/24 |
| WYND Server | 9000 | TCP | ✅ Running | NETREQ proxy |
| Web Control Panel | 8080 | HTTP | ✅ Running | FastAPI |
| Nginx Proxy | 80 | HTTP | ✅ Running | Reverse proxy |

### 3. Firewall Configuration (UFW)
- Port 22: Open (SSH)
- Port 53: Open (TCP)
- Port 80: Open (HTTP)
- Port 443: Open (TCP + UDP)
- Port 992: Open
- Port 5555: Open
- Port 9000: Open

### 4. Domain Configuration
- Domain: harshitsehgal.online
- DNS: Points to 161.118.177.7 (updated on Namecheap)
- HTTPS: Not configured (HTTP only)

### 5. Web Control Panel
- Location: /home/ubuntu/wynd-web/
- Tech Stack: Python 3.10 + FastAPI + Uvicorn + Nginx
- Features:
  - Real-time VPN status (checks active sessions)
  - Server details display
  - Connection instructions for each protocol

## WHY THIS APPROACH (Why It Won't Work The Other Way)

### 1. Why Port 53?

Many networks block everything except DNS (port 53). SoftEther on TCP 53 works because:
- DNS is essential for network operation
- Almost no networks block port 53
- TCP ensures reliable delivery (unlike UDP)

### 2. Why Multiple Protocols?

Different networks block different things:

| Network Type | Likely Open | Use |
|------------|-----------|-----------|
| Normal WiFi | All | Any VPN |
| Hostel (strict) | TCP 53 only | SoftEther TCP 53 |
| Corporate | HTTP/HTTPS | SSTP (TCP 443) |
| Very strict | DNS only | SoftEther TCP 53 |

### 3. Why Not Just One VPN?

- **Reliability**: If one protocol fails, others work
- **Flexibility**: Different situations need different approaches
- **Development**: WYND was also a learning project

## WHAT NEEDS TO BE DONE

### HIGH PRIORITY

1. **HTTPS/SSL Certificate**
   - Install certbot: `sudo apt install certbot python3-certbot-nginx`
   - Run: `sudo certbot --nginx -d harshitsehgal.online`
   - This will enable HTTPS

2. **Make Connect Buttons Work**
   - Currently website only shows instructions
   - Need to implement actual VPN connection triggers
   - This requires client-side config file generation

3. **Keep Server Running After Reboot**
   - Create systemd service for Python app
   - Or use supervisor
   - Current: runs via nohup (not production-grade)

### MEDIUM PRIORITY

4. **Real Time Analytics**
   - Bandwidth monitoring per user
   - Session duration tracking
   - Connection history

5. **WireGuard Client Config Download**
   - Endpoint shows instructions only
   - Need /api/config/wireguard endpoint

6. **More Users**
   - Add more user accounts
   - Different credentials per user

### LOW PRIORITY / NICE TO HAVE

7. **PWA Features**
   - Add manifest.json
   - Make installable on mobile

8. **iOS Support**
   - WireGuard for iOS works (App Store)
   - SoftEther has no iOS client

9. **Data Usage Stats**
   - Track RX/TX per session
   - Display on web panel

10. **Speed Test**
    - Built-in speed test on server

## CREDENTIALS (FOR REFERENCE)

### Server Access
```
SSH: ubuntu@161.118.177.7
Key: C:\Users\harsh\Downloads\ssh-key-2026-04-22.key
```

### VPN Credentials
```
Hub: WYND
Username: wynduser
Password: wyndpass123
```

### SoftEther Ports
- TCP 53 (Primary - works everywhere)
- TCP 443 (SSTP)
- TCP 992
- TCP 5555

### WireGuard
- Port: UDP 443
- Client IP: 10.66.66.2/32
- Server IP: 10.66.66.1/24
- Config file: C:\Users\harsh\Downloads\wynd-wireguard-client.conf

### Web Panel
- URL: http://harshitsehgal.online
- Server: 161.118.177.7:80

## IMPORTANT FILES LOCATIONS

### On Oracle VM

| File | Path | Description |
|------|------|-------------|
| Web App | /home/ubuntu/wynd-web/main.py | Python FastAPI app |
| Nginx Config | /etc/nginx/sites-available/wynd | Reverse proxy config |
| WireGuard Config | /etc/wireguard/wg0.conf | Server config |
| WireGuard Keys | /etc/wireguard/ | Public/private keypairs |
| SoftEther | /usr/local/vpnserver/ | VPN server binary |
| UFW Rules | /etc/ufw/user.rules | Firewall config |

### On Local PC

| File | Description |
|------|-------------|
| C:\Users\harsh\Downloads\ssh-key-2026-04-22.key | SSH key |
| C:\Users\harsh\Downloads\wynd-wireguard-client.conf | WireGuard config |

## ACCESS COMMANDS

### SSH to Server
```bash
ssh -i "C:\Users\harsh\Downloads\ssh-key-2026-04-22.key" ubuntu@161.118.177.7
```

### Check VPN Status
```bash
ssh -i "C:\Users\harsh\Downloads\ssh-key-2026-04-22.key" ubuntu@161.118.177.7 "sudo wg show"
```

### Check SoftEther Sessions
```bash
ssh -i "C:\Users\harsh\Downloads\ssh-key-2026-04-22.key" ubuntu@161.118.177.7 "sudo /usr/local/vpnserver/vpncmd localhost /HUB:WYND /CMD SessionList"
```

### Restart Web Panel
```bash
ssh -i "C:\Users\harsh\Downloads\ssh-key-2026-04-22.key" ubuntu@161.118.177.7 "pkill -f main.py ; cd /home/ubuntu/wynd-web && nohup python3 main.py > app.log 2>&1 &"
```

### View Web Logs
```bash
ssh -i "C:\Users\harsh\Downloads\ssh-key-2026-04-22.key" ubuntu@161.118.177.7 "tail -20 /home/ubuntu/wynd-web/app.log"
```

### Test Web Panel
```bash
curl http://harshitsehgal.online/api/status
```

## NETWORK DIAGRAM

```
HOSTEL WIFI (Blocked: UDP, TCP 443)
              │
              │ (Open: TCP 53 DNS)
              ▼
┌─────────────────────────────────────────┐
│         ORACLE CLOUD VM                 │
│         161.118.177.7               │
│                                     │
│  ┌───────────────────────────┐       │
│  │ SoftEther VPN        │       │
│  │ TCP 53 (DNS)       │◄─────┼── Android/Windows
│  │ TCP 443 (SSTP)    │       │
│  └───────────────────────────┘       │
│                                     │
│  ┌───────────────────────────┐       │
│  │ WireGuard VPN      │       │
│  │ UDP 443        │       │
│  └───────────────────────────┘       │
│                                     │
│  ┌───────────────────────────┐       │
│  │ Web Control     │       │
│  │ Panel         │◄─────────── Browser
│  └───────────────────────────┘       │
└─────────────────────────────────────────┘

After VPN:
User Device → Internet appears as 161.118.177.7 (Oracle)
```

## SUMMARY

- Working: SoftEther (TCP 53, 443, 992, 5555), WireGuard (UDP 443), Web Panel
- Primary recommended port for hostels: TCP 53 (SoftEther)
- Website: http://harshitsehgal.online shows connection status
- Still needed: HTTPS, auto-reconnect, better status detection