#!/usr/bin/env python3
"""
WYND VPN Client - Fixed protocol
"""
import socket
import struct
import threading

SERVER = "161.118.177.7"
SERVER_PORT = 53
PROXY_PORT = 1080

class WYNDFullVPN:
    def __init__(self):
        pass
        
    def connect_to_server(self):
        """Test connection to WYND server"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER, SERVER_PORT))
        s.sendall(struct.pack('!H', 4) + b"PING")
        resp = s.recv(10)
        s.close()
        return True
    
    def handle_client(self, client_sock, client_addr):
        """Handle SOCKS5 client - forward via WYND server"""
        try:
            # SOCKS5 greeting
            ver = client_sock.recv(1)
            if ver != b'\x05':
                client_sock.close()
                return
            
            nmethods = client_sock.recv(1)
            methods = client_sock.recv(ord(nmethods))
            client_sock.send(b'\x05\x00')  # No auth
            
            # SOCKS5 request
            cmd = client_sock.recv(1)
            _ = client_sock.recv(1)  # reserved
            addr_type = client_sock.recv(1)
            
            if addr_type == b'\x01':  # IPv4
                target_ip = client_sock.recv(4)
                target = socket.inet_ntoa(target_ip)
            elif addr_type == b'\x03':  # Domain
                domain_len = client_sock.recv(1)
                target = client_sock.recv(ord(domain_len)).decode()
            
            target_port = struct.unpack('!H', client_sock.recv(2))[0]
            
            # Connect to WYND server with our custom protocol
            wynd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            wynd_sock.connect((SERVER, SERVER_PORT))
            
            # Send CONNECT command through our protocol
            # Format: length(2) + CMD(1) + ADDR_TYPE(1) + address + port(2)
            if addr_type == b'\x01':
                request = b'\x01' + target_ip + struct.pack('!H', target_port)
            else:
                request = b'\x03' + target.encode() + struct.pack('!H', target_port)
            
            wynd_sock.sendall(struct.pack('!H', len(request)) + request)
            
            # Get response
            resp_header = wynd_sock.recv(2)
            resp_len = struct.unpack('!H', resp_header)[0]
            if resp_len > 0:
                resp = wynd_sock.recv(resp_len)
            
            # Tell client we're connected
            client_sock.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            
            # Bridge the connections
            def forward(src, dst):
                try:
                    while True:
                        data = src.recv(4096)
                        if not data:
                            break
                        # Wrap in our protocol
                        dst.sendall(struct.pack('!H', len(data)) + data)
                except:
                    pass
            
            # Bidirectional forwarding
            t1 = threading.Thread(target=forward, args=(client_sock, wynd_sock))
            t2 = threading.Thread(target=forward, args=(wynd_sock, client_sock))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_sock.close()
    
    def run(self):
        print("=" * 50)
        print("WYND VPN Client")
        print("=" * 50)
        
        if not self.connect_to_server():
            print("Failed to connect to server")
            return
            
        print(f"Connected to {SERVER}:{SERVER_PORT}")
        
        # Start SOCKS5 proxy
        proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            proxy.bind(('127.0.0.1', PROXY_PORT))
        except:
            PROXY_PORT = 1081
            proxy.bind(('127.0.0.1', PROXY_PORT))
            
        proxy.listen(5)
        
        print(f"SOCKS5 proxy on 127.0.0.1:{PROXY_PORT}")
        print("Configure your app to use this proxy")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                client, addr = proxy.accept()
                print(f"Client: {addr}")
                t = threading.Thread(target=self.handle_client, args=(client, addr))
                t.daemon = True
                t.start()
        except KeyboardInterrupt:
            print("\nStopping...")

if __name__ == "__main__":
    WYNDFullVPN().run()