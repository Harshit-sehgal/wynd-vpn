//! WYND VPN Server - TCP tunnel for bypassing network restrictions

use std::net::SocketAddr;
use std::sync::Arc;
use anyhow::Result;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::RwLock;

const PORT: u16 = 53;
const MAX_PACKET: usize = 65535;

struct ServerState {
    connections: u32,
}

#[tokio::main]
async fn main() -> Result<()> {
    println!("WYND Server v0.1.0 - TCP {}", PORT);
    
    let listener = TcpListener::bind(format!("0.0.0.0:{}", PORT)).await?;
    println!("Listening on port {}", PORT);
    
    let state = Arc::new(RwLock::new(ServerState { connections: 0 }));
    
    loop {
        let (socket, addr) = listener.accept().await?;
        println!("Connection from {}", addr);
        
        let state = Arc::clone(&state);
        tokio::spawn(handle_connection(socket, addr, state));
    }
}

async fn handle_connection(mut socket: TcpStream, addr: SocketAddr, state: Arc<RwLock<ServerState>>) {
    let mut buf = [0u8; MAX_PACKET];
    
    // Handshake
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
        s.connections += 1;
        s.connections
    };
    
    let _ = socket.write_all(format!("OK:{}\n", id).as_bytes()).await;
    println!("Client {} connected", id);
    
    // Echo loop
    loop {
        match socket.read(&mut buf).await {
            Ok(0) => break,
            Ok(n) => {
                if socket.write_all(&buf[..n]).await.is_err() {
                    break;
                }
            }
            Err(_) => break,
        }
    }
    
    println!("Client {} disconnected", id);
}