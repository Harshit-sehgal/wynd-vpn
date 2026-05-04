#!/usr/bin/env python3
"""Persistent server runner"""
import os
import sys
import time

server_script = "/home/ubuntu/wynd-final.py"

while True:
    print(f"Starting server at {time.strftime('%H:%M:%S')}")
    pid = os.fork()
    if pid == 0:
        # Child - run the server
        os.execvp("python3", ["python3", server_script])
    else:
        # Parent - wait for child
        _, status = os.waitpid(pid, 0)
        print(f"Server died with status {status}, restarting in 2s...")
        time.sleep(2)