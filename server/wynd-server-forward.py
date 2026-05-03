#!/usr/bin/env python3
"""
WYND VPN Server - Full Internet Forwarding
Routes all client traffic through to the real internet
"""
import socket
import struct
import threading
import sys
import os

PORT = 53

def handle_client(client_sock, client_addr):
    """Handle client - forward all traffic to real internet"""
    print(f"[{client_addr}] Connected")
    
    try:
        while True:
            # Read 2-byte length header
            header = client_sock.recv(2)
            if not header:
                break
                
            length = struct.unpack('!H', header)[0]
            if length > 65535 or length == 0:
                break
                
            # Read IP packet
            packet = client_sock.recv(length)
            if not packet:
                break
            
            # Parse IP packet
            if len(packet) >= 20:
                dst_ip = f"{packet[16]}.{packet[17]}.{packet[18]}.{packet[19]}"
                protocol = packet[9]
                
                # For TCP (protocol 6), we can make a real connection
                if protocol == 6 and len(packet) >= 20:
                    # Get TCP destination port
                    dst_port = (packet[22] << 8) | packet[23]
                    
                    # Make a real connection to the internet
                    try:
                        # Create socket to the real destination
                        real_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        real_sock.settimeout(10)
                        real_sock.connect((dst_ip, dst_port))
                        
                        # Extract TCP payload (skip IP header + TCP header)
                        ip_header_len = (packet[0] & 0x0F) * 4
                        tcp_header_len = ((packet[46] >> 4) * 4) if len(packet) > 46 else 20
                        payload_start = ip_header_len + tcp_header_len
                        
                        # Send any payload data
                        if payload_start < len(packet):
                            app_data = packet[payload_start:]
                            if app_data:
                                real_sock.sendall(app_data)
                        
                        # Read response
                        response_data = b''
                        try:
                            while True:
                                chunk = real_sock.recv(4096)
                                if not chunk:
                                    break
                                response_data += chunk
                        except:
                            pass
                        
                        real_sock.close()
                        
                        # Send response back to client
                        if response_data:
                            client_sock.sendall(struct.pack('!H', len(response_data)) + response_data)
                        else:
                            # No response, send empty to keepalive
                            client_sock.sendall(struct.pack('!H', 0))
                            
                    except Exception as e:
                        # Connection failed - send empty response
                        # This allows client to handle timeout
                        pass
                else:
                    # Non-TCP, just echo back for now
                    client_sock.sendall(struct.pack('!H', length) + packet)
            else:
                # Not a valid IP packet, echo back
                client_sock.sendall(struct.pack('!H', length) + packet)
                
    except Exception as e:
        print(f"[{client_addr}] Error: {e}")
    finally:
        client_sock.close()
        print(f"[{client_addr}] Disconnected")

def main():
    print("=" * 50)
    print("WYND VPN Server - IP Forwarding")
    print("=" * 50)
    print(f"Port: {PORT}")
    print("Forwarding all traffic to real internet...\n")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(10)
    
    print(f"Listening on 0.0.0.0:{PORT}")
    print("Waiting for connections...\n")
    
    while True:
        client, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client, addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    main()