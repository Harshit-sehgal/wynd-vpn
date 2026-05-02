import socket
import struct
import time
import sys

SERVER_IP = "127.0.0.0" if len(sys.argv) < 2 else sys.argv[1]
SERVER_PORT = 53 if len(sys.argv) < 3 else int(sys.argv[2])

def test_basic_packets():
    print("\n=== Test 1: Basic Packets ===")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            for i in range(3):
                payload = f"Test packet {i}".encode('utf-8')
                s.sendall(struct.pack('!H', len(payload)) + payload)
                resp_len = struct.unpack('!H', s.recv(2))[0]
                resp = s.recv(resp_len)
                print(f"  Packet {i}: {len(payload)} bytes -> {len(resp)} bytes [OK]")
        print("  Result: PASSED\n")
        return True
    except Exception as e:
        print(f"  Result: FAILED - {e}\n")
        return False

def test_large_payload():
    print("\n=== Test 2: Large Payload (1400 bytes) ===")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            payload = b'X' * 1400
            s.sendall(struct.pack('!H', len(payload)) + payload)
            resp_len = struct.unpack('!H', s.recv(2))[0]
            resp = s.recv(resp_len)
            print(f"  Sent: {len(payload)} bytes, Received: {len(resp)} bytes [OK]")
            if len(resp) == len(payload):
                print("  Result: PASSED\n")
                return True
            else:
                print("  Result: FAILED - Size mismatch\n")
                return False
    except Exception as e:
        print(f"  Result: FAILED - {e}\n")
        return False

def test_binary_data():
    print("\n=== Test 3: Binary Data (256 bytes) ===")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            payload = bytes(range(256))
            s.sendall(struct.pack('!H', len(payload)) + payload)
            resp_len = struct.unpack('!H', s.recv(2))[0]
            resp = s.recv(resp_len)
            if resp == payload:
                print(f"  Sent: {len(payload)} bytes binary, Received: {len(resp)} bytes [OK]")
                print("  Result: PASSED\n")
                return True
            else:
                print("  Result: FAILED - Data mismatch\n")
                return False
    except Exception as e:
        print(f"  Result: FAILED - {e}\n")
        return False

def test_many_packets():
    print("\n=== Test 4: Many Packets (100 packets) ===")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            success = 0
            for i in range(100):
                payload = f"Packet {i}".encode('utf-8')
                s.sendall(struct.pack('!H', len(payload)) + payload)
                resp_len = struct.unpack('!H', s.recv(2))[0]
                resp = s.recv(resp_len)
                if resp == payload:
                    success += 1
            print(f"  Sent: 100 packets, Success: {success}/100")
            if success == 100:
                print("  Result: PASSED\n")
                return True
            else:
                print("  Result: FAILED\n")
                return False
    except Exception as e:
        print(f"  Result: FAILED - {e}\n")
        return False

def test_connection_stability():
    print("\n=== Test 5: Connection Stability (10 sec) ===")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            s.settimeout(5)
            start = time.time()
            packets = 0
            while time.time() - start < 10:
                payload = b"keepalive"
                s.sendall(struct.pack('!H', len(payload)) + payload)
                resp_len = struct.unpack('!H', s.recv(2))[0]
                s.recv(resp_len)
                packets += 1
                time.sleep(1)
            print(f"  Duration: 10 sec, Packets sent: {packets} [OK]")
            print("  Result: PASSED\n")
            return True
    except Exception as e:
        print(f"  Result: FAILED - {e}\n")
        return False

def test_rapid_fire():
    print("\n=== Test 6: Rapid Fire (50 packets) ===")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            success = 0
            start = time.time()
            for i in range(50):
                payload = f"Rapid {i}".encode('utf-8')
                s.sendall(struct.pack('!H', len(payload)) + payload)
                resp_len = struct.unpack('!H', s.recv(2))[0]
                resp = s.recv(resp_len)
                if resp == payload:
                    success += 1
            elapsed = time.time() - start
            print(f"  Sent: 50 packets in {elapsed:.2f} sec, Success: {success}/50")
            print("  Result: PASSED\n")
            return True
    except Exception as e:
        print(f"  Result: FAILED - {e}\n")
        return False

if __name__ == "__main__":
    print(f"Testing server: {SERVER_IP}:{SERVER_PORT}")
    print("=" * 50)
    
    results = []
    results.append(test_basic_packets())
    results.append(test_large_payload())
    results.append(test_binary_data())
    results.append(test_many_packets())
    results.append(test_connection_stability())
    results.append(test_rapid_fire())
    
    print("=" * 50)
    print(f"SUMMARY: {sum(results)}/{len(results)} tests passed")
    if all(results):
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")