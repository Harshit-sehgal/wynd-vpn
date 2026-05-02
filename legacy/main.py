import os
import subprocess
import socket
from pathlib import Path
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

SERVER_IP = "161.118.177.7"
BASE_DIR = Path(__file__).parent

def get_public_ip():
    try:
        result = subprocess.run(
            ["curl", "-s", "https://api.ipify.org"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        return "Unknown"

def check_softether_sessions():
    try:
        result = subprocess.run(
            ["/usr/local/vpnserver/vpncmd", "localhost", "/SERVER", "/PASSWORD:wyndvpn123", "/HUB:WYND", "/CMD", "SessionList"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout.upper()
        if "SESSION" in output or "CONNECTION" in output:
            lines = output.split('\n')
            for line in lines:
                if "WYNDUSER" in line.upper() or ("VIRTUAL" in line.upper() and "HUB" not in line):
                    return True
    except:
        pass
    return False

def check_wireguard():
    try:
        result = subprocess.run(
            ["wg", "show"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout
        if "latest handshake" in output.lower():
            return True
    except:
        pass
    return False

def get_vpn_status():
    try:
        softether_active = check_softether_sessions()
        wireguard_active = check_wireguard()
        
        if softether_active:
            return {"connected": True, "ip": SERVER_IP, "mode": "SoftEther VPN (TCP 53)", "status": "connected", "type": "softether"}
        elif wireguard_active:
            return {"connected": True, "ip": SERVER_IP, "mode": "WireGuard (UDP 443)", "status": "connected", "type": "wireguard"}
        else:
            ip = get_public_ip()
            return {"connected": False, "ip": ip, "mode": "Disconnected", "status": "disconnected", "type": "none"}
    except Exception as e:
        ip = get_public_ip()
        return {"connected": False, "ip": ip, "mode": "Disconnected", "status": "disconnected", "type": "none"}

@app.get("/api/status")
def api_status():
    return get_vpn_status()

@app.get("/api/connect/{mode}")
def api_connect(mode: str):
    if mode == "softether":
        return {
            "status": "instructions",
            "message": "Use SoftEther VPN Client on your device",
            "host": "161.118.177.7",
            "port": 53,
            "hub": "WYND",
            "username": "wynduser",
            "password": "wyndpass123"
        }
    elif mode == "sstp":
        return {
            "status": "instructions", 
            "message": "Use Windows built-in VPN or SSTP Client",
            "host": "161.118.177.7",
            "port": 443,
            "username": "wynduser@WYND",
            "password": "wyndpass123"
        }
    elif mode == "wireguard":
        return {
            "status": "instructions",
            "message": "Use WireGuard app",
            "host": "161.118.177.7",
            "port": 443,
            "type": "UDP"
        }
    return {"status": "error", "message": "Unknown mode"}

@app.get("/api/disconnect")
def api_disconnect():
    return {"status": "success", "message": "Disconnect from your VPN client"}

@app.get("/", response_class=HTMLResponse)
def index():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WYND VPN</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1a1a2e">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d0d1a 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 480px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; padding-top: 20px; }
        .logo {
            font-size: 3rem;
            font-weight: 900;
            background: linear-gradient(135deg, #00d4ff, #00ff94);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { opacity: 0.6; font-size: 0.9rem; }
        
        .status-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 30px;
            margin-bottom: 20px;
        }
        
        .status-indicator { text-align: center; margin-bottom: 20px; }
        .dot {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .dot-connected { background: #00ff94; box-shadow: 0 0 20px #00ff94; }
        .dot-disconnected { background: #ff4757; }
        
        .status-badge {
            padding: 10px 24px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 700;
            display: inline-block;
        }
        .status-connected { background: rgba(0,255,148,0.2); color: #00ff94; border: 1px solid #00ff94; }
        .status-disconnected { background: rgba(255,71,87,0.2); color: #ff4757; border: 1px solid #ff4757; }
        
        .ip-display { text-align: center; margin: 25px 0; }
        .ip-label { font-size: 0.8rem; opacity: 0.6; text-transform: uppercase; letter-spacing: 1px; }
        .ip-value { font-size: 1.8rem; font-weight: 700; color: #00d4ff; margin-top: 8px; }
        
        .vpn-type { font-size: 0.9rem; color: #00ff94; margin-top: 5px; }
        
        .section-title {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            opacity: 0.5;
            margin-bottom: 15px;
        }
        
        .btn-group { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
        .btn {
            flex: 1;
            min-width: 130px;
            padding: 16px 12px;
            border: none;
            border-radius: 14px;
            font-size: 0.9rem;
            font-weight: 700;
            cursor: pointer;
        }
        .btn:active { transform: scale(0.96); }
        .btn-softether { background: linear-gradient(135deg, #00b894, #00a383); color: white; }
        .btn-sstp { background: linear-gradient(135deg, #6c5ce7, #a855f7); color: white; }
        .btn-wireguard { background: linear-gradient(135deg, #fdcb6e, #f39c12); color: #1a1a2e; }
        .btn-disconnect { background: rgba(255,71,87,0.2); color: #ff4757; border: 1px solid #ff4757; }
        
        .info-card {
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            padding: 20px;
        }
        .server-info { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.85rem; }
        .info-item { opacity: 0.7; }
        .info-value { font-weight: 600; color: #00d4ff; margin-top: 4px; }
        
        .instructions {
            background: rgba(0,212,255,0.1);
            border: 1px solid rgba(0,212,255,0.3);
            border-radius: 16px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }
        .instructions.show { display: block; }
        .instructions h3 { color: #00d4ff; font-size: 1rem; margin-bottom: 12px; }
        .instructions p { font-size: 0.85rem; opacity: 0.8; line-height: 1.6; }
        .instructions code { background: rgba(0,0,0,0.3); padding: 3px 10px; border-radius: 4px; }
        
        .footer { text-align: center; margin-top: 30px; opacity: 0.4; font-size: 0.75rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">WYND</div>
            <div class="subtitle">VPN Control Panel</div>
        </div>
        
        <div class="status-card">
            <div class="status-indicator">
                <span class="dot" id="statusDot"></span>
                <div class="status-badge" id="statusBadge">CHECKING</div>
            </div>
            <div class="ip-display">
                <div class="ip-label">Your Public IP</div>
                <div class="ip-value" id="ipValue">...</div>
                <div class="vpn-type" id="vpnType"></div>
            </div>
        </div>
        
        <div class="section-title">Connect via SoftEther</div>
        <div class="btn-group">
            <button class="btn btn-softether" onclick="connectVPN('softether')">SoftEther (TCP 53)</button>
        </div>
        
        <div class="section-title">Other Options</div>
        <div class="btn-group">
            <button class="btn btn-sstp" onclick="connectVPN('sstp')">SSTP</button>
            <button class="btn btn-wireguard" onclick="connectVPN('wireguard')">WireGuard</button>
        </div>
        
        <div class="btn-group">
            <button class="btn btn-disconnect" onclick="disconnectVPN()">Disconnect</button>
        </div>
        
        <div class="info-card">
            <div class="section-title">Server Details</div>
            <div class="server-info">
                <div class="info-item"><div>Server</div><div class="info-value">161.118.177.7</div></div>
                <div class="info-item"><div>Port (SoftEther)</div><div class="info-value">TCP 53</div></div>
                <div class="info-item"><div>Hub</div><div class="info-value">WYND</div></div>
                <div class="info-item"><div>Username</div><div class="info-value">wynduser</div></div>
            </div>
        </div>
        
        <div class="instructions" id="instructions">
            <h3>How to Connect</h3>
            <div id="instructionText"></div>
        </div>
        
        <div class="footer">
            <p>Last updated: <span id="lastUpdate"></span></p>
        </div>
    </div>
    
    <script>
        async function updateStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                document.getElementById('ipValue').textContent = data.ip;
                
                const dot = document.getElementById('statusDot');
                const badge = document.getElementById('statusBadge');
                const vpnType = document.getElementById('vpnType');
                
                if (data.connected) {
                    dot.className = 'dot dot-connected';
                    badge.textContent = 'CONNECTED';
                    badge.className = 'status-badge status-connected';
                    vpnType.textContent = data.mode || 'VPN Active';
                } else {
                    dot.className = 'dot dot-disconnected';
                    badge.textContent = 'DISCONNECTED';
                    badge.className = 'status-badge status-disconnected';
                    vpnType.textContent = '';
                }
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            } catch(e) {
                document.getElementById('ipValue').textContent = 'Error';
            }
        }
        
        async function connectVPN(mode) {
            const btn = event.target;
            btn.textContent = 'Loading...';
            
            try {
                const res = await fetch('/api/connect/' + mode);
                const data = await res.json();
                
                const instr = document.getElementById('instructions');
                const text = document.getElementById('instructionText');
                instr.classList.add('show');
                
                if (mode === 'softether') {
                    text.innerHTML = '<p><strong>SoftEther VPN Client:</strong></p><p style="margin-top:10px;">Host: <code>161.118.177.7</code><br>Port: <code>53</code><br>Hub: <code>WYND</code><br>User: <code>wynduser</code><br>Pass: <code>wyndpass123</code></p>';
                } else if (mode === 'sstp') {
                    text.innerHTML = '<p><strong>Windows SSTP:</strong></p><p style="margin-top:10px;">Host: <code>161.118.177.7</code><br>User: <code>wynduser@WYND</code><br>Pass: <code>wyndpass123</code></p>';
                } else if (mode === 'wireguard') {
                    text.innerHTML = '<p><strong>WireGuard:</strong></p><p style="margin-top:10px;">Download config and import to WireGuard app.</p>';
                }
            } catch(e) {}
            
            btn.textContent = mode === 'softether' ? 'SoftEther (TCP 53)' : mode === 'sstp' ? 'SSTP' : 'WireGuard';
        }
        
        async function disconnectVPN() {
            event.target.textContent = 'Disconnecting...';
            try { await fetch('/api/disconnect'); setTimeout(updateStatus, 2000); } catch(e) {}
            event.target.textContent = 'Disconnect';
        }
        
        updateStatus();
        // Don't auto-refresh - only check when user wants to see status
    </script>
</body>
</html>"""
    return html

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)