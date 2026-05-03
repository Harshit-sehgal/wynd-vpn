import socket, struct
s = socket.socket()
s.connect(('127.0.0.1', 53))
req = b'\x01' + socket.inet_aton('1.1.1.1') + struct.pack('!H', 80)
s.sendall(struct.pack('!H', len(req)) + req)
resp = s.recv(2)
resp_len = struct.unpack('!H', resp)[0]
data = s.recv(resp_len)
print('Connect response:', data[0])
if data[0] == 0:
    print('SUCCESS! Sending HTTP...')
    s.sendall(b'GET / HTTP/1.1\r\nHost: 1.1.1.1\r\n\r\n')
    r = s.recv(100)
    print('Got response:', len(r), 'bytes')
s.close()