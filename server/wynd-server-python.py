#!/usr/bin/env python3
"""
WYND VPN Server - Python with proper TUN support
"""

import socket
import struct
import threading
import os
import subprocess
import sys

PORT = 53

def setup_tun():
    """Set up TUN interface and NAT"""
    # Create TUN device
    subprocess.run(['ip', 'tuntap', 'add', 'mode', 'tun', 'dev', 'tun0'], capture_output=True)
    subprocess.run(['ip', 'addr', 'add', '10.0.0.1/24', 'dev', 'tun0'], capture_output=True)
    subprocess.run(['ip', 'link', 'set', 'tun0', 'up'], capture_output=True)
    
    # Enable IP forwarding
    with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
        f.write('1')
    
    # NAT
    subprocess.run(['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-s', '10.0.0.0/24', '-j', 'MASQUERADE'], capture_output=True)
    subprocess.run(['iptables', '-A', 'FORWARD', '-i', 'tun0', '-j', 'ACCEPT'], capture_output=True)
    
    print("TUN interface configured: 10.0.0.1/24")

def handle_client(client_sock, client_addr):
    """Handle client connection"""
    print(f"[{client_addr}] Client connected")
    
    try:
        # Open TUN device for this client
        tun_fd = os.open('/dev/net/tun', os.O_RDWR)
        
        while True:
            # Read length header
            header = client_sock.recv(2)
            if not header:
                break
                
            length = struct.unpack('!H', header)[0]
            
            # Read IP packet
            packet = client_sock.recv(length)
            if not packet:
                break
                
            # Write to TUN (this sends to internet via NAT)
            os.write(tun_fd, packet)
            
            # Read response from TUN (blocking - this is the internet response)
            try:
                response = os.read(tun_fd, 65535)
                if response:
                    # Send response back to client
                    client_sock.sendall(struct.pack('!H', len(response)) + response)
            except:
                pass
                
    except Exception as e:
        print(f"[{client_addr}] Error: {e}")
    finally:
        client_sock.close()
        try:
            os.close(tun_fd)
        except:
            pass
        print(f"[{client_addr}] Disconnected")

def main():
    print("=" * 50)
    print("WYND VPN Server (Python TUN)")
    print("=" * 50)
    
    setup_tun()
    
    # Start server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(10)
    
    print(f"Server listening on port {PORT}")
    print("Waiting for connections...\n")
    
    while True:
        client, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client, addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    main()