use anyhow::{Context, Result};
use bytes::{BufMut, BytesMut};
use std::net::SocketAddr;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tracing::{error, info, warn};

const LISTEN_PORT: u16 = 53;
const MAX_PAYLOAD_SIZE: usize = 65535;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize structured logging
    tracing_subscriber::fmt::init();

    let addr = format!("0.0.0.0:{}", LISTEN_PORT);
    let listener = TcpListener::bind(&addr).await.context("Failed to bind TCP listener")?;

    info!("WYND tcp53d server listening on {}", addr);
    info!("Waiting for incoming connections...");

    loop {
        match listener.accept().await {
            Ok((stream, addr)) => {
                info!("New connection from: {}", addr);
                tokio::spawn(async move {
                    if let Err(e) = handle_connection(stream, addr).await {
                        error!("Connection error for {}: {:?}", addr, e);
                    }
                    info!("Connection closed for: {}", addr);
                });
            }
            Err(e) => {
                warn!("Failed to accept connection: {:?}", e);
            }
        }
    }
}

async fn handle_connection(mut stream: TcpStream, addr: SocketAddr) -> Result<()> {
    let mut buffer = BytesMut::with_capacity(4096);

    loop {
        // Read the 2-byte length header
        let mut length_buf = [0u8; 2];
        match stream.read_exact(&mut length_buf).await {
            Ok(_) => {}
            Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => {
                // Client disconnected gracefully
                return Ok(());
            }
            Err(e) => return Err(e.into()),
        }

        let payload_len = u16::from_be_bytes(length_buf) as usize;
        if payload_len == 0 || payload_len > MAX_PAYLOAD_SIZE {
            anyhow::bail!("Invalid payload length: {}", payload_len);
        }

        info!("[{}] Receiving packet of length: {}", addr, payload_len);

        // Read the actual payload
        buffer.resize(payload_len, 0);
        stream.read_exact(&mut buffer).await?;

        // --- At this point in the MVP, we just echo the packet back ---
        // In Phase 3, this is where we inject `buffer` into the TUN interface.

        info!("[{}] Echoing packet back (MVP mode)", addr);
        
        // Write frame header
        let mut response = BytesMut::with_capacity(2 + payload_len);
        response.put_u16(payload_len as u16);
        response.put_slice(&buffer);

        stream.write_all(&response).await?;
    }
}
