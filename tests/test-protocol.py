import socket
import struct
import time
import sys

SERVER_IP = "127.0.0.0" if len(sys.argv) < 2 else sys.argv[1]
SERVER_PORT = 9000

def test_protocol():
    print(f"Connecting to {SERVER_IP}:{SERVER_PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            print("Connected successfully.")
            
            # Send 3 test packets
            for i in range(3):
                # Create a fake payload
                payload = f"Hello WYND server, this is packet {i}.".encode('utf-8')
                
                # Create the 2-byte header (Big Endian)
                header = struct.pack('!H', len(payload))
                
                # Send frame
                print(f"Sending packet {i} (Length: {len(payload)})")
                s.sendall(header + payload)
                
                # Receive response
                resp_header = s.recv(2)
                if not resp_header:
                    print("Server closed connection unexpectedly while waiting for header.")
                    break
                    
                resp_len = struct.unpack('!H', resp_header)[0]
                print(f"Server responded with length: {resp_len}")
                
                resp_payload = s.recv(resp_len)
                print(f"Server payload: {resp_payload.decode('utf-8')}")
                print("-" * 20)
                
                time.sleep(1)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_protocol()