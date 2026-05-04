#!/usr/bin/env python3
"""
WYND HTTP Tunnel Server
Wraps all TCP traffic in HTTP and forwards to the real destination
"""
import socket
import struct
import threading
import http.client
from urllib.parse import urlparse

PORT = 8080  # Local proxy port
SERVER_HOST = "161.118.177.7"
SERVER_PORT = 53

class HTTPTunnel:
    def __init__(self):
        pass
        
    def forward_http(self, client_sock, request):
        """Parse HTTP request and forward"""
        try:
            # Parse the request
            lines = request.split(b'\r\n')
            if not lines:
                return
                
            # Get request line (first line)
            request_line = lines[0].decode('utf-8', errors='ignore')
            parts = request_line.split()
            
            if len(parts) < 2:
                return
                
            method = parts[0]
            url = parts[1]
            
            # Parse the target from Host header
            host = None
            port = 80
            for line in lines[1:]:
                if line.lower().startswith(b'host:'):
                    host = line.split(b':')[1].strip().decode('utf-8', errors='ignore')
                    if ':' in host:
                        parts = host.split(':')
                        host = parts[0]
                        port = int(parts[1])
                    break
            
            if not host:
                client_sock.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
                return
            
            print(f"HTTP: {method} {host}:{port}{url}")
            
            # Create connection to real server through our WYND server
            # We tunnel the raw TCP connection through HTTP
            
            # Connect to our server
            wynd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            wynd_sock.connect((SERVER_HOST, SERVER_PORT))
            
            # Send as a special HTTP-tunnel request
            # We'll use CONNECT method style
            tunnel_req = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
            wynd_sock.sendall(tunnel_req.encode())
            
            # Get response from tunnel
            resp = wynd_sock.recv(1024)
            
            # If successful (200), forward the original request
            if b"200" in resp or b"Connection established" in resp:
                # Forward the original HTTP request body (after headers)
                body_start = request.find(b'\r\n\r\n')
                if body_start > 0:
                    body = request[body_start+4:]
                    if body:
                        wynd_sock.sendall(body)
                
                # Bridge the connection
                def forward(src, dst):
                    try:
                        while True:
                            data = src.recv(4096)
                            if not data:
                                break
                            dst.sendall(data)
                    except:
                        pass
                
                t1 = threading.Thread(target=forward, args=(client_sock, wynd_sock))
                t2 = threading.Thread(target=forward, args=(wynd_sock, client_sock))
                t1.start()
                t2.start()
                t1.join()
                t2.join()
                
            else:
                client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                
        except Exception as e:
            print(f"Error: {e}")
            try:
                client_sock.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
            except:
                pass
        finally:
            try:
                client_sock.close()
            except:
                pass
    
    def handle_proxy(self, client_sock, client_addr):
        """Handle SOCKS-like CONNECT for any TCP"""
        try:
            # Read the connect request
            data = client_sock.recv(1024)
            
            # Try to parse as HTTP CONNECT first
            if b"CONNECT" in data:
                # HTTP CONNECT method - tunnel through HTTP
                self.forward_http(client_sock, data)
                return
            
            # Otherwise assume it's our custom protocol
            # Forward to WYND server
            wynd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            wynd_sock.connect((SERVER_HOST, SERVER_PORT))
            
            # Forward the data
            wynd_sock.sendall(data)
            
            # Bridge
            def forward(src, dst):
                try:
                    while True:
                        d = src.recv(4096)
                        if not d:
                            break
                        dst.sendall(d)
                except:
                    pass
            
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
        print("WYND HTTP Tunnel Server")
        print("=" * 50)
        print(f"HTTP Proxy on :{PORT}")
        print(f"Forwarding through: {SERVER_HOST}:{SERVER_PORT}")
        print("")
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', PORT))
        server.listen(10)
        
        print(f"Listening on 127.0.0.1:{PORT}")
        print("")
        print("Configure your browser/app to use HTTP proxy:")
        print(f"  Host: 127.0.0.1")
        print(f"  Port: {PORT}")
        print("")
        
        while True:
            client, addr = server.accept()
            print(f"Connection from {addr}")
            t = threading.Thread(target=self.handle_proxy, args=(client, addr))
            t.daemon = True
            t.start()

if __name__ == "__main__":
    HTTPTunnel().run()