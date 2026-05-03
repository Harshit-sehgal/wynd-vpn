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

    info!("WYND VPN Server - IP Proxy Mode");
    info!("================================");

    // Start server
    let addr = format!("0.0.0.0:{}", LISTEN_PORT);
    let listener = TcpListener::bind(&addr).await.context("Failed to bind")?;
    info!("Server listening on {}", addr);
    info!("Routing traffic to internet via IP proxy");
    info!("");

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

async fn handle_client(mut client_stream: TcpStream, client_addr: SocketAddr) -> Result<()> {
    let mut header_buf = BytesMut::with_capacity(65535);

    loop {
        // Read 2-byte length header
        let mut length_buf = [0u8; 2];
        match client_stream.read_exact(&mut length_buf).await {
            Ok(_) => {}
            Err(e) if e.kind() == std::io::ErrorKind::UnexpectedEof => return Ok(()),
            Err(e) => return Err(e.into()),
        }

        let payload_len = u16::from_be_bytes(length_buf) as usize;
        if payload_len == 0 || payload_len > 65535 {
            anyhow::bail!("Invalid payload length: {}", payload_len);
        }

        // Read IP packet
        header_buf.resize(payload_len, 0);
        client_stream.read_exact(&mut header_buf).await?;

        let packet = header_buf.to_vec();

        // Parse IP packet to get destination
        if packet.len() >= 20 {
            let dst_ip = format!("{}.{}.{}.{}", packet[16], packet[17], packet[18], packet[19]);
            let src_ip = format!("{}.{}.{}.{}", packet[12], packet[13], packet[14], packet[15]);
            let protocol = packet[9];
            
            info!("[{}] {} -> {} (proto: {})", client_addr, src_ip, dst_ip, protocol);

            // For TCP (protocol 6) and UDP (protocol 17), we can try to proxy
            if protocol == 6 && packet.len() >= 20 {
                // TCP packet - try to extract port
                let dst_port = ((packet[22] as u16) << 8) | (packet[23] as u16);
                let src_port = ((packet[20] as u16) << 8) | (packet[21] as u16);
                
                info!("[{}] TCP {}:{} -> {}:{}", client_addr, src_ip, src_port, dst_ip, dst_port);
                
                // Try to connect to the destination and forward
                match TcpStream::connect(format!("{}:{}", dst_ip, dst_port)).await {
                    Ok(mut dst_stream) => {
                        // Skip IP header (20 bytes) + TCP header (usually 20 bytes) = 40
                        let tcp_header_len = ((packet[46] >> 4) as usize) * 4;
                        let payload_start = 20 + tcp_header_len;
                        
                        // Send data after TCP header to destination
                        if payload_start < packet.len() {
                            let app_data = &packet[payload_start..];
                            if !app_data.is_empty() {
                                dst_stream.write_all(app_data).await?;
                            }
                        }
                        
                        // Read response
                        let mut response_buf = vec![0u8; 65535];
                        match dst_stream.read(&mut response_buf).await {
                            Ok(n) if n > 0 => {
                                // Construct response packet
                                // For now, just echo back the data we got (simplified)
                                // Real implementation would build proper IP/TCP response
                                let mut response = BytesMut::with_capacity(2 + n);
                                response.put_u16(n as u16);
                                response.put_slice(&response_buf[..n]);
                                client_stream.write_all(&response).await?;
                            }
                            _ => {}
                        }
                    }
                    Err(e) => {
                        // Destination unreachable - just echo back (simplified)
                        warn!("[{}] Could not connect to {}:{} - {}", client_addr, dst_ip, dst_port, e);
                        
                        // Echo back for now
                        let mut response = BytesMut::with_capacity(2 + packet.len());
                        response.put_u16(payload_len as u16);
                        response.put_slice(&packet);
                        client_stream.write_all(&response).await?;
                    }
                }
            } else if protocol == 17 {
                // UDP - echo back for now
                let dst_port = ((packet[22] as u16) << 8) | (packet[23] as u16);
                info!("[{}] UDP -> {}:{}", client_addr, dst_ip, dst_port);
                
                // Echo back
                let mut response = BytesMut::with_capacity(2 + packet.len());
                response.put_u16(payload_len as u16);
                response.put_slice(&packet);
                client_stream.write_all(&response).await?;
            } else {
                // Other protocols - echo
                let mut response = BytesMut::with_capacity(2 + packet.len());
                response.put_u16(payload_len as u16);
                response.put_slice(&packet);
                client_stream.write_all(&response).await?;
            }
        } else {
            // Not enough data for IP header - echo
            let mut response = BytesMut::with_capacity(2 + packet.len());
            response.put_u16(payload_len as u16);
            response.put_slice(&packet);
            client_stream.write_all(&response).await?;
        }
    }
}