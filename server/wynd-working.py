#!/usr/bin/env python3
"""
WYND VPN Server - Fixed forwarding
"""
import socket
import struct
import threading
import sys

PORT = 53

def handle_client(client_sock, client_addr):
    """Handle client - forward connections to real internet"""
    print(f"[{client_addr}] Connected")
    
    try:
        # Read request (length + data)
        header = client_sock.recv(2)
        if not header:
            return
            
        length = struct.unpack('!H', header)[0]
        if length > 1024 or length == 0:
            return
            
        data = client_sock.recv(length)
        if not data:
            return
        
        # Parse CONNECT request: ADDR_TYPE(1) + address + PORT(2)
        if len(data) >= 4:
            addr_type = data[0]
            
            if addr_type == 1 and len(data) >= 7:  # IPv4
                ip = f"{data[1]}.{data[2]}.{data[3]}.{data[4]}"
                port = (data[5] << 8) | data[6]
            elif addr_type == 3:  # Domain
                domain_len = data[1]
                if len(data) >= 2 + domain_len + 2:
                    domain = data[2:2+domain_len].decode()
                    port = (data[2+domain_len] << 8) | data[2+domain_len+1]
                    ip = domain
                else:
                    return
            else:
                return
            
            print(f"[{client_addr}] Forwarding to {ip}:{port}")
            
            # Connect to real destination
            try:
                real_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                real_sock.settimeout(30)
                real_sock.connect((ip, port))
                
                # Send success (0x00 = success)
                client_sock.sendall(struct.pack('!H', 1) + b'\x00')
                
                # Bidirectional forwarding
                def forward(src, dst):
                    try:
                        while True:
                            d = src.recv(4096)
                            if not d:
                                break
                            dst.sendall(d)
                    except:
                        pass
                
                t1 = threading.Thread(target=forward, args=(client_sock, real_sock))
                t2 = threading.Thread(target=forward, args=(real_sock, client_sock))
                t1.start()
                t2.start()
                t1.join()
                t2.join()
                
            except Exception as e:
                print(f"[{client_addr}] Failed: {e}")
                # Send failure response (0x01 = general failure)
                client_sock.sendall(struct.pack('!H', 1) + b'\x01')
                
    except Exception as e:
        print(f"[{client_addr}] Error: {e}")
    finally:
        client_sock.close()
        print(f"[{client_addr}] Disconnected")

def main():
    print("=" * 50)
    print("WYND VPN Server - Forwarding Mode")
    print("=" * 50)
    print(f"Port: {PORT}\n")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(10)
    
    print(f"Listening on 0.0.0.0:{PORT}\n")
    
    while True:
        client, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(client, addr))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    main()