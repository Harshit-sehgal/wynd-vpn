#!/usr/bin/env python3
"""
WYND VPN Server - Fixed with longer timeouts
"""
import socket
import struct
import threading
import sys
import os

PORT = 53

def log(msg):
    print(msg)

def handle_client(client_sock, client_addr):
    log(f"[{client_addr}] Connected")
    
    try:
        # Set timeout
        client_sock.settimeout(30)
        header = client_sock.recv(2)
        log(f"[{client_addr}] Got header: {header}")
        
        length = struct.unpack('!H', header)[0]
        
        if length > 1024 or length == 0:
            return
            
        data = client_sock.recv(length)
        log(f"[{client_addr}] Got data: {data}")
        if not data:
            return
        
        # Handle INIT handshake
        if data == b'INIT':
            log(f"[{client_addr}] INIT OK, waiting for connect...")
            # Send response WITHOUT length prefix (keep simple)
            client_sock.sendall(b'\x00')
            log(f"[{client_addr}] Sent INIT response, waiting for connect request...")
            # Wait for actual connect
            header = client_sock.recv(2)
            log(f"[{client_addr}] Got header: {header}")
            length = struct.unpack('!H', header)[0]
            log(f"[{client_addr}] Expecting {length} bytes")
            if length > 1024 or length == 0:
                return
            data = client_sock.recv(length)
            log(f"[{client_addr}] Got connect data: {data}")
        
        if len(data) >= 7:
            addr_type = data[0]
            
            if addr_type == 1:
                ip = f"{data[1]}.{data[2]}.{data[3]}.{data[4]}"
                port = (data[5] << 8) | data[6]
                log(f"[{client_addr}] CONNECT to {ip}:{port}")
                
                try:
                    real_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    real_sock.settimeout(60)  # Longer timeout
                    real_sock.connect((ip, port))
                    log(f"[{client_addr}] Connected to {ip}:{port}")
                    
                    # Success - send without length prefix
                    client_sock.sendall(b'\x00')
                    
                    log(f"[{client_addr}] Forwarding data...")
                    
                    def forward_client_to_server(src, dst):
                        try:
                            while True:
                                d = src.recv(4096)
                                if not d:
                                    break
                                dst.sendall(d)
                        except Exception as e:
                            log(f"[{client_addr}] Forward error: {e}")
                    
                    def forward_server_to_client(src, dst):
                        try:
                            while True:
                                d = src.recv(4096)
                                if not d:
                                    break
                                dst.sendall(struct.pack('!H', len(d)) + d)
                        except Exception as e:
                            log(f"[{client_addr}] Forward error: {e}")
                    
                    t1 = threading.Thread(target=forward_client_to_server, args=(client_sock, real_sock))
                    t2 = threading.Thread(target=forward_server_to_client, args=(real_sock, client_sock))
                    t1.start()
                    t2.start()
                    t1.join()
                    t2.join()
                    
                except Exception as e:
                    log(f"[{client_addr}] Failed: {e}")
                    client_sock.sendall(b'\x01')
                    
    except Exception as e:
        log(f"[{client_addr}] Error: {e}")
    finally:
        client_sock.close()
        log(f"[{client_addr}] Disconnected")

def main():
    log("=" * 50)
    log("WYND VPN Server - Final")
    log(f"Port: {PORT}")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(10)
    
    log(f"Listening on 0.0.0.0:{PORT}")
    
    while True:
        client, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(client, addr))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    main()