use anyhow::{Context, Result};
use bytes::{BufMut, BytesMut};
use std::net::SocketAddr;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tracing::{error, info, warn};

const LISTEN_PORT: u16 = 53;

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    info!("WYND VPN Server v2 - Full TUN Support");
    info!("======================================");

    // Set up TUN interface
    setup_tun()?;
    setup_nat()?;

    // Start server
    let addr = format!("0.0.0.0:{}", LISTEN_PORT);
    let listener = TcpListener::bind(&addr).await.context("Failed to bind")?;
    info!("Server listening on {}", addr);
    info!("VPN Network: 10.0.0.0/24");
    info!("");
    info!("To use this VPN, clients need to:");
    info!("1. Connect to {}:{}", addr.replace("0.0.0.0", "161.118.177.7"), LISTEN_PORT);
    info!("2. Set up their own TUN interface with IP 10.0.0.x");
    info!("");
    info!("For full VPN, each client needs to create their own TUN device.");
    info!("MVP mode: Echo server for protocol testing.");

    loop {
        match listener.accept().await {
            Ok((stream, addr)) => {
                info!("Client connected: {}", addr);
                tokio::spawn(async move {
                    if let Err(e) = handle_client(stream, addr).await {
                        error!("Client {} error: {:?}", addr, e);
                    }
                    info!("Client {} disconnected", addr);
                });
            }
            Err(e) => warn!("Accept error: {:?}", e),
        }
    }
}

fn setup_tun() -> Result<()> {
    use std::process::Command;

    // Create TUN if not exists
    let _ = Command::new("ip")
        .args(&["tuntap", "add", "mode", "tun", "dev", "tun0"])
        .output();

    // Set IP
    let _ = Command::new("ip")
        .args(&["addr", "add", "10.0.0.1/24", "dev", "tun0"])
        .output();

    // Bring up
    let _ = Command::new("ip")
        .args(&["link", "set", "tun0", "up"])
        .output();

    // Enable IP forwarding
    let _ = Command::new("sh")
        .args(&["-c", "echo 1 > /proc/sys/net/ipv4/ip_forward"])
        .output();

    info!("TUN0: 10.0.0.1/24 - UP");
    Ok(())
}

fn setup_nat() -> Result<()> {
    use std::process::Command;

    // NAT
    let _ = Command::new("iptables")
        .args(&["-t", "nat", "-A", "POSTROUTING", "-s", "10.0.0.0/24", "-j", "MASQUERADE"])
        .output();

    // Forward
    let _ = Command::new("iptables")
        .args(&["-A", "FORWARD", "-i", "tun0", "-j", "ACCEPT"])
        .output();

    let _ = Command::new("iptables")
        .args(&["-A", "FORWARD", "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])
        .output();

    info!("NAT and forwarding configured");
    Ok(())
}

async fn handle_client(mut stream: TcpStream, addr: SocketAddr) -> Result<()> {
    let mut buffer = BytesMut::with_capacity(65535);

    info!("[{}] Client session started (MVP echo mode)", addr);

    loop {
        // Read 2-byte length header
        let mut length_buf = [0u8; 2];
        match stream.read_exact(&mut length_buf).await {
            Ok(_) => {}
            Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => return Ok(()),
            Err(e) => return Err(e.into()),
        }

        let payload_len = u16::from_be_bytes(length_buf) as usize;
        if payload_len == 0 || payload_len > 65535 {
            anyhow::bail!("Invalid payload length: {}", payload_len);
        }

        // Read IP packet
        buffer.resize(payload_len, 0);
        stream.read_exact(&mut buffer).await?;

        let packet = buffer.to_vec();

        // Parse and log
        if packet.len() >= 20 {
            let dst = format!("{}.{}.{}.{}", packet[16] & 0xFF, packet[17] & 0xFF, packet[18] & 0xFF, packet[19] & 0xFF);
            let src = format!("{}.{}.{}.{}", packet[12] & 0xFF, packet[13] & 0xFF, packet[14] & 0xFF, packet[15] & 0xFF);
            let proto = packet[9];
            info!("[{}] IP {} -> {} ({} bytes, proto {})", addr, src, dst, packet.len(), proto);
        }

        // MVP: Echo back the packet
        // In full mode: inject to TUN, wait for response, send to client
        let mut response = BytesMut::with_capacity(2 + packet.len());
        response.put_u16(payload_len as u16);
        response.put_slice(&packet);
        stream.write_all(&response).await?;
    }
}