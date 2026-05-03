#!/usr/bin/env python3
"""
WYND VPN Client - Full System Tunnel
Uses routing to redirect ALL traffic through WYND server
"""

import socket
import struct
import threading
import subprocess
import sys
import os
import time

SERVER_HOST = "161.118.177.7"
SERVER_PORT = 53
LOCAL_PROXY_HOST = "127.0.0.1"
LOCAL_PROXY_PORT = 1080
VPN_NETWORK = "10.98.0.0"
VPN_NETMASK = "255.255.255.0"

class WYNDTunnel:
    def __init__(self):
        self.server_conn = None
        self.running = False
        
    def connect_to_server(self):
        """Connect to WYND server"""
        print(f"Connecting to WYND server {SERVER_HOST}:{SERVER_PORT}...")
        self.server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_conn.settimeout(30)
        self.server_conn.connect((SERVER_HOST, SERVER_PORT))
        
        # Handshake
        payload = b"VPN_INIT"
        self.server_conn.sendall(struct.pack('!H', len(payload)) + payload)
        
        # Wait for response
        header = self.server_conn.recv(2)
        resp_len = struct.unpack('!H', header)[0]
        if resp_len > 0:
            resp = self.server_conn.recv(resp_len)
        
        print("Connected to WYND VPN server!")
        return True
        
    def handle_client(self, client_sock):
        """Handle a client connection - forward to server"""
        try:
            while self.running:
                data = client_sock.recv(65535)
                if not data:
                    break
                    
                # Send through WYND protocol
                self.server_conn.sendall(struct.pack('!H', len(data)) + data)
                
                # Get response
                resp_header = self.server_conn.recv(2)
                if not resp_header:
                    break
                resp_len = struct.unpack('!H', resp_header)[0]
                if resp_len > 0:
                    resp_data = self.server_conn.recv(resp_len)
                    client_sock.send(resp_data)
                    
        except Exception as e:
            if self.running:
                pass  # Ignore errors during shutdown
        finally:
            try:
                client_sock.close()
            except:
                pass
    
    def start_proxy(self):
        """Start local SOCKS5-like proxy server"""
        global LOCAL_PROXY_PORT
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT))
        except:
            print(f"Port {LOCAL_PROXY_PORT} in use, trying alternative...")
            LOCAL_PROXY_PORT = 1081
            server.bind((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT))
            
        server.listen(10)
        
        print(f"\n{'='*50}")
        print("WYND VPN Client")
        print(f"{'='*50}")
        print(f"Proxy running on: {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}")
        print(f"Server: {SERVER_HOST}:{SERVER_PORT}")
        print("\nNow setting up routing...")
        
        return server
    
    def setup_windows_routing(self):
        """Set up Windows routing to redirect traffic through proxy"""
        print("\nSetting up Windows routing...")
        
        # Store original gateway
        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            # Find default gateway
            for line in result.stdout.split('\n'):
                if 'Default Gateway' in line or 'default gateway' in line.lower():
                    parts = line.split(':')
                    if len(parts) > 1:
                        gw = parts[1].strip()
                        if gw and gw != '':
                            print(f"Original gateway: {gw}")
                            # Save for later
                            with open('original_gateway.txt', 'w') as f:
                                f.write(gw)
        except Exception as e:
            print(f"Note: {e}")
        
        # Method 1: Usenetsh to add a persistent route (requires admin)
        # This redirects specific traffic through our proxy
        print("\nTo enable full VPN, run these commands as ADMINISTRATOR:")
        print("-" * 40)
        print(f"1. Add route to redirect traffic:")
        print(f'   netsh interface portproxy add v4tov4 listenport=80 connectaddress={LOCAL_PROXY_HOST} connectport={LOCAL_PROXY_PORT}')
        print(f"\n2. Or use Proxychains approach:")
        print(f"   Download Proxychains from https://github.com/rofl0r/proxychains-ng")
        print(f"   Then run: proxychains your_app.exe")
        print("-" * 40)
        
    def run_with_proxychains(self):
        """Alternative: Use proxychains to run apps through VPN"""
        print("\n" + "="*50)
        print("USING PROXYCHAINS (RECOMMENDED)")
        print("="*50)
        print("\n1. Download proxychains from:")
        print("   https://github.com/rofl0r/proxychains-ng")
        print("\n2. Configure proxychains.conf:")
        print(f"   [ProxyList]")
        print(f"   socks5  {LOCAL_PROXY_HOST}  {LOCAL_PROXY_PORT}")
        print("\n3. Run any app through VPN:")
        print(f"   proxychains your_application.exe")
        print("\nExample:")
        print("   proxychains curl http://ip-api.com/json")
        print("   proxychains teams.exe")
        print("="*50)

    def main(self):
        print("="*50)
        print("WYND VPN - Desktop Client")
        print("="*50)
        
        # Connect to server
        try:
            self.connect_to_server()
        except Exception as e:
            print(f"Failed to connect: {e}")
            return
        
        self.running = True
        
        # Start proxy server
        proxy = self.start_proxy()
        
        # Start client handler thread
        def accept_clients():
            while self.running:
                try:
                    proxy.settimeout(1)
                    client, addr = proxy.accept()
                    thread = threading.Thread(target=self.handle_client, args=(client,))
                    thread.daemon = True
                    thread.start()
                except socket.timeout:
                    continue
                except:
                    break
        
        accept_thread = threading.Thread(target=accept_clients)
        accept_thread.daemon = True
        accept_thread.start()
        
        # Show usage options
        self.run_with_proxychains()
        
        print(f"\nProxy is running on {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}")
        print("Keep this window open while using the VPN")
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.running = False
            if self.server_conn:
                self.server_conn.close()

if __name__ == "__main__":
    tunnel = WYNDTunnel()
    tunnel.main()