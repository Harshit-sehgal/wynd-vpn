#!/usr/bin/env python3
"""
WYND VPN Server - With Debug
"""
import socket
import struct
import threading
import sys
import os

PORT = 53
LOG = open("/tmp/wynd-debug.log", "a")

def log(msg):
    LOG.write(msg + "\n")
    LOG.flush()
    print(msg)

def handle_client(client_sock, client_addr):
    log(f"[{client_addr}] Connected")
    
    try:
        header = client_sock.recv(2)
        if not header:
            return
            
        length = struct.unpack('!H', header)[0]
        log(f"[{client_addr}] Request length: {length}")
        
        if length > 1024 or length == 0:
            return
            
        data = client_sock.recv(length)
        if not data:
            return
        
        log(f"[{client_addr}] Data: {data[:10].hex()}")
        
        if len(data) >= 7:
            addr_type = data[0]
            
            if addr_type == 1:
                ip = f"{data[1]}.{data[2]}.{data[3]}.{data[4]}"
                port = (data[5] << 8) | data[6]
                log(f"[{client_addr}] CONNECT to {ip}:{port}")
                
                try:
                    real_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    real_sock.settimeout(10)
                    real_sock.connect((ip, port))
                    log(f"[{client_addr}] Connected to {ip}:{port}")
                    
                    # Success
                    client_sock.sendall(struct.pack('!H', 1) + b'\x00')
                    
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
                    log(f"[{client_addr}] Failed: {e}")
                    client_sock.sendall(struct.pack('!H', 1) + b'\x01')
            else:
                log(f"[{client_addr}] Unknown addr type: {addr_type}")
                
    except Exception as e:
        log(f"[{client_addr}] Error: {e}")
    finally:
        client_sock.close()
        log(f"[{client_addr}] Disconnected")

def main():
    log("=" * 50)
    log("WYND VPN Server - Debug")
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