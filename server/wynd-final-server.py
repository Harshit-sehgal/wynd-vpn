#!/usr/bin/env python3
"""
WYND VPN Server - Proper protocol handling
"""
import socket
import struct
import threading

PORT = 53

def handle_client(client_sock, client_addr):
    """Handle client - parse protocol and forward"""
    print(f"[{client_addr}] Connected")
    
    try:
        # First, receive the initial handshake
        header = client_sock.recv(2)
        if not header:
            return
            
        length = struct.unpack('!H', header)[0]
        if length > 1024 or length == 0:
            return
            
        data = client_sock.recv(length)
        if not data:
            return
        
        # Parse CONNECT request
        # Format: CMD(1) + ADDR_TYPE(1) + address + PORT(2)
        if len(data) >= 4:
            cmd = data[0]  # 1 = CONNECT
            addr_type = data[1]  # 1=IPv4, 3=Domain
            
            if addr_type == 1 and len(data) >= 8:  # IPv4
                ip = f"{data[2]}.{data[3]}.{data[4]}.{data[5]}"
                port = (data[6] << 8) | data[7]
            elif addr_type == 3:  # Domain
                domain_len = data[2]
                domain = data[3:3+domain_len].decode()
                port = (data[3+domain_len] << 8) | data[3+domain_len+1]
                ip = domain
            else:
                return
            
            print(f"[{client_addr}] Connecting to {ip}:{port}")
            
            # Connect to real destination
            try:
                real_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                real_sock.settimeout(30)
                real_sock.connect((ip, port))
                
                # Send success response
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
                print(f"[{client_addr}] Connection to {ip}:{port} failed: {e}")
                # Send failure
                client_sock.sendall(struct.pack('!H', 1) + b'\x01')
                
    except Exception as e:
        print(f"[{client_addr}] Error: {e}")
    finally:
        client_sock.close()
        print(f"[{client_addr}] Disconnected")

def main():
    print("=" * 50)
    print("WYND VPN Server")
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