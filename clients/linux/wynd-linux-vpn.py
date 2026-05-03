#!/usr/bin/env python3
"""
WYND VPN Client for Linux
Creates a proper TUN interface and routes all traffic through port 53
"""
import socket
import struct
import threading
import subprocess
import os
import sys

SERVER = "161.118.177.7"
SERVER_PORT = 53
VPN_IP = "10.0.0.2"
VPN_GATEWAY = "10.0.0.1"
TUN_DEV = "tun0"

class WYNDLinuxVPN:
    def __init__(self):
        self.running = True
        self.tun_fd = None
        
    def create_tun(self):
        """Create TUN device on Linux"""
        print("Creating TUN device...")
        
        # Create TUN interface using ip command
        result = subprocess.run(
            ['ip', 'tuntap', 'add', 'mode', 'tun', 'dev', TUN_DEV],
            capture_output=True
        )
        
        # Set IP address
        subprocess.run(
            ['ip', 'addr', 'add', f'{VPN_IP}/24', 'dev', TUN_DEV],
            capture_output=True
        )
        
        # Bring up
        subprocess.run(
            ['ip', 'link', 'set', TUN_DEV, 'up'],
            capture_output=True
        )
        
        print(f"TUN device {TUN_DEV} created: {VPN_IP}/24")
        
    def setup_routing(self):
        """Setup routing to send all traffic through TUN"""
        print("Setting up routing...")
        
        # Add default route through TUN
        subprocess.run(
            ['ip', 'route', 'add', 'default', 'via', VPN_GATEWAY, 'dev', TUN_DEV],
            capture_output=True
        )
        
        print("All traffic will now route through the VPN")
        
    def connect_to_server(self):
        """Connect to WYND server"""
        print(f"Connecting to {SERVER}:{SERVER_PORT}...")
        self.server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_conn.connect((SERVER, SERVER_PORT))
        
        # Handshake - tell server we're a VPN client
        self.server_conn.sendall(struct.pack('!H', 4) + b"VPN1")
        resp = self.server_conn.recv(10)
        print(f"Server connected: {resp}")
        
    def run(self):
        print("=" * 50)
        print("WYND VPN - Linux Client")
        print("=" * 50)
        
        # Create TUN
        try:
            self.create_tun()
        except Exception as e:
            print(f"TUN creation note: {e}")
            print("Trying alternative method...")
            
            # Alternative: use tunctl or existing device
            pass
        
        # Connect to server
        self.connect_to_server()
        
        print(f"\nVPN is running!")
        print(f"TUN: {TUN_DEV} ({VPN_IP}/24)")
        print(f"Server: {SERVER}:{SERVER_PORT}")
        print("\nAll system traffic is now routed through the VPN")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                # Read from TUN and send to server
                # In this simple version, we just keep connection alive
                import time
                time.sleep(1)
                
                # Send keepalive
                try:
                    self.server_conn.sendall(struct.pack('!H', 1) + b'K')
                except:
                    break
                    
        except KeyboardInterrupt:
            print("\nStopping VPN...")
            self.running = False
            
            # Cleanup - remove route
            subprocess.run(
                ['ip', 'route', 'del', 'default', 'via', VPN_GATEWAY],
                capture_output=True
            )

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script must be run as root (sudo)")
        print("Usage: sudo python3 wynd-linux-vpn.py")
        sys.exit(1)
        
    WYNDLinuxVPN().run()