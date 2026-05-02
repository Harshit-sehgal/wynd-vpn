import socket
import struct
import threading
import sys

SERVER_HOST = "161.118.177.7"
SERVER_PORT = 53
LOCAL_PROXY_HOST = "127.0.0.1"
LOCAL_PROXY_PORT = 1080

def handle_client(client_socket, client_addr):
    """Handle incoming SOCKS5 connection"""
    try:
        # SOCKS5 greeting
        version = client_socket.recv(1)
        if version != b'\x05':
            client_socket.close()
            return

        # Auth methods
        nmethods = client_socket.recv(1)
        methods = client_socket.recv(ord(nmethods))

        # Select method (no auth)
        client_socket.send(b'\x05\x00')

        # Request
        version = client_socket.recv(1)
        cmd = client_socket.recv(1)
        _ = client_socket.recv(1)  # reserved
        addr_type = client_socket.recv(1)

        if addr_type == b'\x01':  # IPv4
            target_ip = client_socket.recv(4)
            target = socket.inet_ntoa(target_ip)
        elif addr_type == b'\x03':  # Domain
            domain_len = client_socket.recv(1)
            target = client_socket.recv(ord(domain_len)).decode()
        elif addr_type == b'\x04':  # IPv6
            target_ip = client_socket.recv(16)
            target = socket.inet_ntop(socket.AF_INET6, target_ip)
        
        target_port = struct.unpack('!H', client_socket.recv(2))[0]

        # Connect to WYND server with framing
        wynd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        wynd_sock.connect((SERVER_HOST, SERVER_PORT))

        # Send connect request to server (framed)
        # Format: [2-byte length][1-byte cmd][1-byte addr_type][addr][2-byte port]
        if addr_type == b'\x03':
            request = struct.pack('!BB', cmd[0], addr_type) + target.encode() + struct.pack('!H', target_port)
        elif addr_type == b'\x01':
            request = struct.pack('!BB', cmd[0], addr_type) + target_ip + struct.pack('!H', target_port)
        
        wynd_sock.sendall(struct.pack('!H', len(request)) + request)

        # Get response from server
        resp_header = wynd_sock.recv(2)
        resp_len = struct.unpack('!H', resp_header)[0]
        resp = wynd_sock.recv(resp_len)

        if resp[0] == 0x00:  # Success
            client_socket.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            
            # Bridge: client <-> WYND server
            def forward(src, dst):
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    # Wrap in WYND framing
                    dst.sendall(struct.pack('!H', len(data)) + data)

            # Read response from server and forward to client
            while True:
                resp_header = wynd_sock.recv(2)
                if not resp_header:
                    break
                resp_len = struct.unpack('!H', resp_header)[0]
                resp_data = wynd_sock.recv(resp_len)
                client_socket.send(resp_data)

                # Also handle incoming from client
                client_socket.setblocking(False)
                try:
                    data = client_socket.recv(4096)
                    if data:
                        wynd_sock.sendall(struct.pack('!H', len(data)) + data)
                except:
                    pass
                client_socket.setblocking(True)
        else:
            client_socket.send(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')

    except Exception as e:
        print(f"Error handling client {client_addr}: {e}")
    finally:
        client_socket.close()

def start_socks_proxy():
    """Start the SOCKS5 proxy server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT))
    server.listen(5)
    
    print(f"WYND Desktop Client - SOCKS5 Proxy")
    print(f"=====================================")
    print(f"Server: {SERVER_HOST}:{SERVER_PORT}")
    print(f"Local Proxy: {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}")
    print(f"\nConfigure your browser/app to use SOCKS5 proxy:")
    print(f"  Host: {LOCAL_PROXY_HOST}")
    print(f"  Port: {LOCAL_PROXY_PORT}")
    print(f"\nWaiting for connections...")
    
    while True:
        client_socket, client_addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, client_addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    start_socks_proxy()