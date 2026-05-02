# WYND v2 Architecture

## Overview
WYND v2 is a custom VPN solution designed specifically to bypass highly restricted WiFi networks (such as those in hostels, cafes, and corporate environments) by tunneling all traffic over TCP port 53.

## The Problem
Many restricted networks block standard VPN protocols (WireGuard, OpenVPN, IPSec) and non-standard ports. However, TCP port 53 (DNS) is almost always left open. Existing solutions like SoftEther over TCP-53 work but are heavyweight, hard to set up on mobile, and not optimized for seamless one-tap connection on Android.

## The Solution
A lightweight, custom VPN protocol specifically engineered to operate over a single TCP connection on port 53.

### Key Components
1. **The Server (`wynd-tcp53d`)**: A high-performance Rust daemon that listens on TCP port 53, accepts incoming connections, unwraps the custom protocol, and proxies the raw IP packets to the internet via a NAT interface.
2. **The Android Client**: A native Android application utilizing the `VpnService` API to capture device traffic, encapsulate it in the custom WYND protocol, and send it over a persistent TCP connection to the server.

## Architecture Diagram
```mermaid
graph TD
    subgraph Android Device
        Apps[Apps] -->|IP Packets| VpnService[VpnService]
        VpnService -->|TUN Interface| WyndApp[WYND Client App]
        WyndApp -->|TCP Socket| TCP53Out[TCP Outbound]
    end

    subgraph Restricted Network
        TCP53Out -->|TCP Port 53| Firewall[Captive Portal / Firewall]
    end

    subgraph Cloud Server
        Firewall -->|TCP Port 53| WyndServer[wynd-tcp53d (Rust)]
        WyndServer -->|Raw IP| TUNServer[Server TUN Interface]
        TUNServer -->|NAT| Internet[Internet]
    end
```

## Implementation Phases
* **Phase 1 (Server):** Build the Rust server listening on port 9000 (dev) proxying packets.
* **Phase 2 (Client):** Build the Android MVP client and connect it to port 9000.
* **Phase 3 (Migration):** Move the server to port 53, replacing the legacy SoftEther instance.

## Technical Constraints & Trade-offs
* **TCP-over-TCP Meltdown:** Tunneling TCP traffic inside another TCP connection can lead to performance degradation during packet loss. Since the primary goal is access (bypassing the firewall) rather than high speed, this trade-off is accepted.
* **Encryption:** Initial MVP will focus on the tunnel encapsulation (plain routing). Subsequent iterations will implement lightweight encryption (e.g., ChaCha20-Poly1305) over the TCP stream.