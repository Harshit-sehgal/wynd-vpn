# Phase 3 Deployment Guide

## Overview
Deploy the WYND v2 Rust server to Oracle VM on port 53, replacing SoftEther on that port.

## Prerequisites
- SSH access to Oracle VM: `ubuntu@161.118.177.7`
- Root/sudo access on the VM

## Steps

### 1. Build the Server on Oracle VM

```bash
# SSH into the server
ssh ubuntu@161.118.177.7

# Install Rust if not installed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Clone the repository (or transfer the server code)
git clone https://github.com/Harshit-sehgal/wynd-vpn.git
cd wynd-vpn/server/wynd-tcp53d

# Build the release binary
cargo build --release
```

### 2. Stop SoftEther on Port 53

```bash
# Check if SoftEther is running
sudo systemctl status softether-vpnserver

# Edit SoftEther config to disable port 53
# Or stop the service temporarily to test
sudo systemctl stop softether-vpnserver
```

### 3. Run the Server

```bash
# Run with sudo (required for port 53)
sudo ./target/release/wynd-tcp53d
```

### 4. Test Connectivity

```bash
# From your local machine, test port 53
nc -zv 161.118.177.7 53
```

## Current Server Status (MVP)

The current server is running in **echo mode** - it receives packets and echoes them back. This is useful for testing the protocol but won't provide actual internet access.

For full VPN functionality, the server needs a TUN interface setup to route packets to the internet.

## Rollback Plan

If issues occur:
```bash
# Restart SoftEther
sudo systemctl start softether-vpnserver

# The old VPN will be available again on port 53
```