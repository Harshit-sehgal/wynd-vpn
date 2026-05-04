#!/usr/bin/env python3
"""Simple forwarding server - port 53"""
import socket
import threading

PORT = 53

def handle(client_sock, addr):
    try:
        # Connect to real server (8.8.8.8 as gateway/proxy)
        real_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        real_sock.connect(('8.8.8.8', 53))
        
        # Bridge
        def f(s1, s2):
            while True:
                d = s1.recv(4096)
                if not d: break
                s2.sendall(d)
        
        t1 = threading.Thread(target=f, args=(client_sock, real_sock))
        t2 = threading.Thread(target=f, args=(real_sock, client_sock))
        t1.start(); t2.start()
        t1.join(); t2.join()
    except: pass
    finally:
        client_sock.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', PORT))
s.listen(10)
print(f"Listening on 0.0.0.0:{PORT}")

while True:
    c, a = s.accept()
    threading.Thread(target=handle, args=(c, a)).start()