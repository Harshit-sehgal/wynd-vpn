#!/usr/bin/env python3
"""
WYND VPN Server - Handles BOTH SOCKS5 and custom protocol
"""
import socket
import struct
import threading

PORT = 53
LOG = open("/tmp/wynd-both-new.log", "a")

def log(msg):
    LOG.write(msg + "\n")
    LOG.flush()
    print(msg)

def handle_client(client_sock, client_addr):
    log(f"[{client_addr}] Connected")
    
    try:
        # Peek at first byte to determine protocol
        first_byte = client_sock.recv(1, socket.MSG_PEEK)
        
        if first_byte == b'\x05':
            # SOCKS5 protocol
            log(f"[{client_addr}] SOCKS5 detected")
            handle_socks5(client_sock, client_addr)
        else:
            # Our custom protocol
            log(f"[{client_addr}] Custom protocol detected")
            handle_custom(client_sock, client_addr)
            
    except Exception as e:
        log(f"[{client_addr}] Error: {e}")
    finally:
        client_sock.close()
        log(f"[{client_addr}] Disconnected")

def handle_socks5(client_sock, client_addr):
    """Handle SOCKS5 protocol"""
    try:
        # Greeting
        ver = client_sock.recv(1)
        nmethods = client_sock.recv(1)
        methods = client_sock.recv(ord(nmethods))
        client_sock.send(b'\x05\x00')  # No auth
        
        # Request
        cmd = client_sock.recv(1)
        addr_type = client_sock.recv(1)
        
        target = ""
        port = 80
        
        if addr_type == b'\x01':  # IPv4
            ip = client_sock.recv(4)
            target = socket.inet_ntoa(ip)
        elif addr_type == b'\x03':  # Domain
            length = client_sock.recv(1)
            target = client_sock.recv(ord(length)).decode()
        
        port = struct.unpack('!H', client_sock.recv(2))[0]
        
        log(f"[{client_addr}] SOCKS5 connect to {target}:{port}")
        
        # Connect to real server
        real_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        real_sock.settimeout(60)
        real_sock.connect((target, port))
        
        # Success response
        client_sock.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
        
        log(f"[{client_addr}] SOCKS5 forwarding")
        
        # Bridge
        def forward(src, dst):
            try:
                while True:
                    d = src.recv(4096)
                    if not d: break
                    dst.sendall(d)
            except: pass
        
        t1 = threading.Thread(target=forward, args=(client_sock, real_sock))
        t2 = threading.Thread(target=forward, args=(real_sock, client_sock))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
    except Exception as e:
        log(f"[{client_addr}] SOCKS5 error: {e}")
        try:
            client_sock.send(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
        except: pass

def recv_all(sock, n):
    """Receive exactly n bytes"""
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            log(f"recv_all: got None, returning None (got {len(data)}/{n})")
            return None
        data += chunk
        log(f"recv_all: got {len(chunk)} bytes, total {len(data)}/{n}")
    return data

def handle_custom(client_sock, client_addr):
    """Handle our custom protocol"""
    try:
        header = recv_all(client_sock, 2)
        if not header:
            return
            
        length = struct.unpack('!H', header)[0]
        if length > 1024 or length == 0:
            return
            
        data = recv_all(client_sock, length)
        if not data:
            return
        
        # Handle INIT handshake
        if data == b'INIT':
            log(f"[{client_addr}] INIT OK, waiting for CONNECT...")
            client_sock.sendall(struct.pack('!H', 1) + b'\x00')
            # Wait for actual connection request
            header = recv_all(client_sock, 2)
            if not header:
                return
            length = struct.unpack('!H', header)[0]
            if length > 1024 or length == 0:
                return
            data = recv_all(client_sock, length)
            if not data:
                return
        
        if len(data) >= 7:
            addr_type = data[0]
            
            # Handle CONNECT hostname:port format
            if data.startswith(b'CONNECT '):
                try:
                    host_port = data[8:].decode('utf-8', errors='ignore').strip()
                    log(f"[{client_addr}] Received: '{host_port}'")
                    if ':' in host_port:
                        parts = host_port.split(':')
                        target_host = parts[0]
                        target_port = int(parts[1])
                    else:
                        target_host = host_port
                        target_port = 80
                    ip = socket.gethostbyname(target_host)
                    port = target_port
                    log(f"[{client_addr}] CONNECT {target_host}:{target_port} -> {ip}:{port}")
                except Exception as e:
                    log(f"[{client_addr}] CONNECT failed: {e}")
                    client_sock.sendall(struct.pack('!H', 1) + b'\x01')
                    return
            
            elif addr_type == 1:
                ip = f"{data[1]}.{data[2]}.{data[3]}.{data[4]}"
                port = (data[5] << 8) | data[6]
                log(f"[{client_addr}] Custom connect to {ip}:{port}")
                
                # Check if this is a CONNECT request with hostname
                if data[7:]:
                    try:
                        host_port_str = data[7:].decode('utf-8', errors='ignore')
                        if ':' in host_port_str:
                            target_host, target_port_str = host_port_str.split(':')
                            target_port = int(target_port_str)
                            # Resolve hostname
                            real_ip = socket.gethostbyname(target_host)
                            ip = real_ip
                            port = target_port
                            log(f"[{client_addr}] Resolved {target_host} -> {ip}:{port}")
                    except Exception as e:
                        log(f"[{client_addr}] Resolution failed: {e}")
                
                try:
                    real_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    real_sock.settimeout(60)
                    real_sock.connect((ip, port))
                    
                    client_sock.sendall(struct.pack('!H', 1) + b'\x00')
                    
                    def forward_client_to_server(src, dst):
                        try:
                            while True:
                                d = src.recv(4096)
                                if not d: break
                                dst.sendall(d)
                        except: pass
                    
                    def forward_server_to_client(src, dst):
                        try:
                            while True:
                                d = src.recv(4096)
                                if not d: break
                                dst.sendall(struct.pack('!H', len(d)) + d)
                        except: pass
                    
                    t1 = threading.Thread(target=forward_client_to_server, args=(client_sock, real_sock))
                    t2 = threading.Thread(target=forward_server_to_client, args=(real_sock, client_sock))
                    
                    t1 = threading.Thread(target=forward, args=(client_sock, real_sock))
                    t2 = threading.Thread(target=forward, args=(real_sock, client_sock))
                    t1.start()
                    t2.start()
                    t1.join()
                    t2.join()
                    
                except Exception as e:
                    log(f"[{client_addr}] Failed: {e}")
                    client_sock.sendall(struct.pack('!H', 1) + b'\x01')
                    
    except Exception as e:
        log(f"[{client_addr}] Error: {e}")

def main():
    log("=" * 50)
    log("WYND VPN Server - SOCKS5 + Custom")
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