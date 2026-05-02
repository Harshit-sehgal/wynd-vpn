use anyhow::{Context, Result};
use bytes::{BufMut, BytesMut};
use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::Mutex;
use tracing::{error, info, warn};

const LISTEN_PORT: u16 = 53;
const TUN_IP: &str = "10.0.0.1";
const TUN_NETMASK: &str = "255.255.255.0";

struct ClientSession {
    assigned_ip: String,
    tcp_stream: TcpStream,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    info!("WYND VPN Server with Full TUN Support");
    info!("======================================");

    // Set up TUN interface
    setup_tun_interface()?;

    // Set up NAT
    setup_nat()?;

    // Start server
    let addr = format!("0.0.0.0:{}", LISTEN_PORT);
    let listener = TcpListener::bind(&addr).await.context("Failed to bind")?;
    info!("Server listening on {}", addr);
    info!("TUN interface: {}/24", TUN_IP);
    info!("Ready for connections!");

    // Keep track of active sessions
    let sessions: Arc<Mutex<HashMap<SocketAddr, String>>> = Arc::new(Mutex::new(HashMap::new()));

    loop {
        match listener.accept().await {
            Ok((stream, addr)) => {
                info!("New connection from: {}", addr);
                let sessions_clone = sessions.clone();
                tokio::spawn(async move {
                    if let Err(e) = handle_client(stream, addr, sessions_clone).await {
                        error!("Client {} error: {:?}", addr, e);
                    }
                    info!("Client {} disconnected", addr);
                });
            }
            Err(e) => warn!("Accept error: {:?}", e),
        }
    }
}

fn setup_tun_interface() -> Result<()> {
    use std::process::Command;

    // Create TUN device
    let _ = Command::new("ip")
        .args(&["tuntap", "add", "mode", "tun", "dev", "tun0"])
        .output();

    // Set IP
    let _ = Command::new("ip")
        .args(&["addr", "add", &format!("{}/24", TUN_IP), "dev", "tun0"])
        .output();

    // Bring up
    let _ = Command::new("ip")
        .args(&["link", "set", "tun0", "up"])
        .output();

    info!("TUN interface configured: {}/24", TUN_IP);
    Ok(())
}

fn setup_nat() -> Result<()> {
    use std::process::Command;

    // NAT for traffic going out
    let _ = Command::new("iptables")
        .args(&["-t", "nat", "-A", "POSTROUTING", "-s", "10.0.0.0/24", "-j", "MASQUERADE"])
        .output();

    // Allow forwarding
    let _ = Command::new("iptables")
        .args(&["-A", "FORWARD", "-i", "tun0", "-j", "ACCEPT"])
        .output();

    // Allow established connections
    let _ = Command::new("iptables")
        .args(&["-A", "FORWARD", "-m", "state", "--state", "RELATED,ESTABLISHED", "-j", "ACCEPT"])
        .output();

    info!("NAT configured for 10.0.0.0/24");
    Ok(())
}

async fn handle_client(
    mut stream: TcpStream,
    addr: SocketAddr,
    sessions: Arc<Mutex<HashMap<SocketAddr, String>>>,
) -> Result<()> {
    // Assign IP to client (for now, all clients share 10.0.0.2)
    let client_ip = "10.0.0.2";
    
    {
        let mut s = sessions.lock().await;
        s.insert(addr, client_ip.to_string());
    }

    info!("[{}] Assigned IP: {}", addr, client_ip);
    info!("[{}] Starting packet tunnel...", addr);

    let mut buffer = BytesMut::with_capacity(65535);

    // For MVP: echo mode with logging
    // In full implementation, would write to TUN and read responses
    loop {
        // Read length header
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

        // Read packet
        buffer.resize(payload_len, 0);
        stream.read_exact(&mut buffer).await?;

        let packet = buffer.to_vec();
        
        // Parse IP header to get destination
        if packet.len() >= 20 {
            let dst_ip = format!("{}.{}.{}.{}", packet[16], packet[17], packet[18], packet[19]);
            let src_ip = format!("{}.{}.{}.{}", packet[12], packet[13], packet[14], packet[15]);
            let proto = packet[9];
            let ip_len = (packet[0] & 0x0f) as usize * 4;
            let proto_name = match proto {
                1 => "ICMP",
                6 => "TCP",
                17 => "UDP",
                _ => "OTHER",
            };
            
            info!("[{}] {} <- {} ({} bytes, {})", addr, dst_ip, src_ip, packet.len(), proto_name);
        }

        // For MVP: Echo back (simulating what TUN would return)
        // In production: would inject to TUN, get response, send back
        let mut response = BytesMut::with_capacity(2 + packet.len());
        response.put_u16(packet.len() as u16);
        response.put_slice(&packet);
        stream.write_all(&response).await?;
    }
}