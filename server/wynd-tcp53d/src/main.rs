use anyhow::{Context, Result};
use bytes::{BufMut, BytesMut};
use std::net::SocketAddr;
use std::process::Command;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tracing::{error, info, warn};

const LISTEN_PORT: u16 = 53;

fn setup_tun() -> Result<()> {
    info!("Setting up TUN interface on Linux...");
    
    // Create TUN interface
    let output = Command::new("ip")
        .args(&["tuntap", "add", "mode", "tun", "dev", "tun0"])
        .output();

    if let Ok(o) = output {
        if !o.status.success() {
            // Maybe already exists
            info!("TUN device may already exist");
        }
    }

    // Set IP address
    let _ = Command::new("ip")
        .args(&["addr", "add", "10.0.0.1/24", "dev", "tun0"])
        .output();

    // Bring up
    let _ = Command::new("ip")
        .args(&["link", "set", "tun0", "up"])
        .output();

    info!("TUN interface configured: 10.0.0.1/24");
    info!("To enable NAT, run on server:");
    info!("  sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -j MASQUERADE");
    info!("  sudo iptables -A FORWARD -i tun0 -j ACCEPT");
    
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    info!("WYND tcp53d server with TUN support");
    info!("=====================================");

    // Try to set up TUN (may require root)
    if let Err(e) = setup_tun() {
        warn!("Could not set up TUN (may need root): {}", e);
    }

    // Start TCP server
    let addr = format!("0.0.0.0:{}", LISTEN_PORT);
    let listener = TcpListener::bind(&addr).await.context("Failed to bind TCP listener")?;
    info!("Server listening on {}", addr);
    info!("Waiting for client connections...");

    loop {
        match listener.accept().await {
            Ok((stream, addr)) => {
                info!("Client connected: {}", addr);
                tokio::spawn(async move {
                    if let Err(e) = handle_client(stream, addr).await {
                        error!("Client error {}: {:?}", addr, e);
                    }
                    info!("Client {} disconnected", addr);
                });
            }
            Err(e) => warn!("Failed to accept: {:?}", e),
        }
    }
}

async fn handle_client(mut stream: TcpStream, addr: SocketAddr) -> Result<()> {
    let mut buffer = BytesMut::with_capacity(65535);

    info!("[{}] Handling client", addr);

    loop {
        // Read 2-byte length header
        let mut length_buf = [0u8; 2];
        match stream.read_exact(&mut length_buf).await {
            Ok(_) => {}
            Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => {
                return Ok(());
            }
            Err(e) => return Err(e.into()),
        }

        let payload_len = u16::from_be_bytes(length_buf) as usize;
        if payload_len == 0 || payload_len > 65535 {
            anyhow::bail!("Invalid payload length: {}", payload_len);
        }

        // Read payload
        buffer.resize(payload_len, 0);
        stream.read_exact(&mut buffer).await?;

        let packet = buffer.to_vec();
        
        // In TUN mode: would write to TUN interface
        // In echo mode: just echo back for testing
        info!("[{}] Received packet: {} bytes (TUN mode - logging only)", addr, packet.len());

        // For now, echo back (MVP mode)
        // Real TUN would inject packet here and read response from TUN
        let mut response = BytesMut::with_capacity(2 + packet.len());
        response.put_u16(payload_len as u16);
        response.put_slice(&packet);
        stream.write_all(&response).await?;
    }
}