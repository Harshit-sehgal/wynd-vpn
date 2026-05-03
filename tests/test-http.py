import socket, struct
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 53))
req = b'\x01' + socket.inet_aton('93.184.216.34') + struct.pack('!H', 80)
s.sendall(struct.pack('!H', len(req)) + req)
resp = s.recv(2)
resp_len = struct.unpack('!H', resp)[0]
data = s.recv(resp_len)
print('Connect:', data[0] if data else 'none')
if data and data[0] == 0:
    print('Connected! HTTP...')
    s.sendall(b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n')
    r = s.recv(200)
    print('Response:', r[:50])
s.close()