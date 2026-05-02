# WYND TCP-53 Protocol Specification

## Overview
This document describes the custom protocol used between the WYND Android client and the `wynd-tcp53d` Rust server over a single TCP connection.

## Design Goals
1. **Low Overhead:** Minimal headers to reduce payload size.
2. **Stream Framing:** Reliable packet framing over a continuous TCP stream.
3. **Simplicity:** Easy to implement in both Rust (server) and Kotlin/Java (Android).

## Packet Structure
Since TCP is a stream protocol, we need to frame our IP packets so the receiver knows where one packet ends and the next begins. 

Each frame sent over the TCP connection has the following structure:

| Field | Length | Description |
|-------|--------|-------------|
| Length | 2 bytes (u16) | The length of the IP Packet Payload in bytes (Big Endian). |
| Payload| `Length` bytes | The raw IPv4 or IPv6 packet intercepted from the TUN interface. |

### Example Frame
If an app sends a 40-byte IPv4 packet, the client writes 42 bytes to the TCP socket:
`[0x00, 0x28] [ ... 40 bytes of raw IP packet ... ]`

## Connection Lifecycle

### 1. Handshake (Future)
Currently, in the MVP, the protocol is purely raw framing. 
In the future, a handshake will be introduced:
* **Client -> Server:** Magic bytes, Version, Authentication Token.
* **Server -> Client:** Success/Failure, Assigned Internal IP Address.

### 2. Tunneling (Current MVP)
* Client captures raw IP packets from `VpnService` TUN interface.
* Client calculates the packet length, prepends the 2-byte header.
* Client writes to the TCP socket connected to Port 53 (or 9000 for dev).
* Server reads 2 bytes to determine payload length.
* Server reads exactly `Length` bytes.
* Server writes the raw IP packet to its own TUN interface.
* Server reads packets from its TUN interface destined for the client's internal IP.
* Server frames it (2-byte length + payload) and writes to the TCP socket.

### 3. Teardown
* The TCP connection is closed.
* Server cleans up any NAT rules or session states associated with the client.
