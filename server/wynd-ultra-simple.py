#!/usr/bin/env python3
import socket
import threading
import os
import sys
# Drop privileges if running as root
if os.geteuid() == 0:
    # Already root, keep for binding to port 53
    pass
PORT = 53
print(f"WYND Simple Server on port {PORT}")

def handle(client, addr):
    try:
        real = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        real.connect(('8.8.8.8', 53))
        def f(s1, s2):
            while True:
                d = s1.recv(4096)
                if not d: break
                s2.sendall(d)
        t1 = threading.Thread(target=f, args=(client, real))
        t2 = threading.Thread(target=f, args=(real, client))
        t1.start(); t2.start()
        t1.join(); t2.join()
    except: pass
    finally:
        client.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', PORT))
s.listen(10)
print(f"Listening on 0.0.0.0:{PORT}")
while True:
    c, a = s.accept()
    threading.Thread(target=handle, args=(c, a)).start()