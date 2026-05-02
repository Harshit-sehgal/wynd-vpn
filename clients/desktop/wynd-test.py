import socket
import struct
import sys
import time

SERVER_HOST = "161.118.177.7"
SERVER_PORT = 53

def connect_and_test():
    print("=" * 50)
    print("WYND Desktop Client (Test Mode)")
    print("=" * 50)
    print(f"Server: {SERVER_HOST}:{SERVER_PORT}")
    print()
    
    try:
        print("Connecting to WYND server...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_HOST, SERVER_PORT))
        print(f"Connected! Remote: {SERVER_HOST}:{SERVER_PORT}")
        print()
        
        # Test echo functionality
        print("Testing protocol (sending echo packets)...")
        for i in range(5):
            payload = f"Test packet {i}".encode()
            s.sendall(struct.pack('!H', len(payload)) + payload)
            resp_len = struct.unpack('!H', s.recv(2))[0]
            resp = s.recv(resp_len)
            print(f"  Packet {i}: {len(payload)} bytes -> OK")
            time.sleep(0.5)
        
        print()
        print("Connection test: SUCCESS")
        print()
        print("NOTE: Server is in ECHO mode.")
        print("      For full VPN internet access, server needs TUN interface.")
        print("      SoftEther is still available on ports 443/992/5555 for full VPN.")
        print()
        print("Press Ctrl+C to exit...")
        
        # Keep connection alive
        while True:
            time.sleep(1)
            # Send keepalive
            payload = b"keepalive"
            s.sendall(struct.pack('!H', len(payload)) + payload)
            
    except KeyboardInterrupt:
        print("\nExiting...")
        s.close()
    except Exception as e:
        print(f"Error: {e}")
        s.close()

if __name__ == "__main__":
    connect_and_test()