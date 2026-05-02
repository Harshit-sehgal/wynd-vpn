//! WYND Tunnel Server - Simple TCP VPN

use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;
use anyhow::Result;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::RwLock;

const PORT: u16 = 9000;
const MAX_PACKET: usize = 65535;

struct State {
    clients: u32,
    stats: HashMap<u32, ClientStats>,
}

#[derive(Default)]
struct ClientStats {
    packets_in: u64,
    packets_out: u64,
    bytes_in: u64,
    bytes_out: u64,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("==========================================");
    println!("WYND Server v0.1.0");
    println!("==========================================");
    println!("Listening on TCP :{}", PORT);
    println!("==========================================");
    
    let listener = TcpListener::bind(format!("0.0.0.0:{}", PORT)).await?;
    println!("Ready! Waiting for connections...");
    
    let state = Arc::new(RwLock::new(State::new()));
    
    loop {
        let (socket, addr) = listener.accept().await?;
        println!("Connection from {}", addr);
        
        let state = Arc::clone(&state);
        tokio::spawn(handle(socket, addr, state));
    }
}

impl State {
    fn new() -> Self {
        Self { clients: 0, stats: HashMap::new() }
    }
}

async fn handle(mut socket: TcpStream, addr: SocketAddr, state: Arc<RwLock<State>>) {
    let mut buf = [0u8; MAX_PACKET];
    
    // Handshake - read "HELLO"
    let n = match socket.read(&mut buf).await {
        Ok(n) if n > 0 => n,
        _ => return,
    };
    
    let msg = String::from_utf8_lossy(&buf[..n]).trim().to_string();
    println!("Handshake: {}", msg);
    
    if msg != "HELLO" {
        let _ = socket.write_all(b"ERROR\n").await;
        return;
    }
    
    let id = {
        let mut s = state.write().await;
        s.clients += 1;
        s.clients
    };
    
    println!("Client {} connected", id);
    
    let _ = socket.write_all(format!("OK:{}\n", id).as_bytes()).await;
    
    // Main loop - echo packets for testing
    // Real server would forward to internet here
    loop {
        match socket.read(&mut buf).await {
            Ok(0) => break,
            Ok(n) => {
                // Update stats
                {
                    let mut s = state.write().await;
                    if let Some(stats) = s.stats.get_mut(&id) {
                        stats.packets_in += 1;
                        stats.bytes_in += n as u64;
                    }
                }
                
                // Echo back for testing
                if socket.write_all(&buf[..n]).await.is_err() {
                    break;
                }
                
                {
                    let mut s = state.write().await;
                    if let Some(stats) = s.stats.get_mut(&id) {
                        stats.packets_out += 1;
                        stats.bytes_out += n as u64;
                    }
                }
            }
            Err(_) => break,
        }
    }
    
    println!("Client {} disconnected", id);
}