mod core;

use crate::core::{config::Config, logger};
use std::io::{BufRead, BufReader, Write};
use std::net::TcpStream;

fn main() {
    let mut args = std::env::args().skip(1);
    if let Some(arg) = args.next() {
        match arg.as_str() {
            "--help" => {
                print_usage();
                return;
            }
            "--version" => {
                println!("wynd {}", env!("CARGO_PKG_VERSION"));
                return;
            }
            _ => {
                eprintln!("error: unrecognized argument: {arg}");
                std::process::exit(2);
            }
        }
    }

    let config = Config::load();
    logger::init(&config);
    logger::info("WYND started");

    let addr = format!("{}:{}", config.server_host, config.server_port);
    let mut stream = match TcpStream::connect(&addr) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("error: failed to connect to {addr}: {e}");
            std::process::exit(1);
        }
    };

    if let Err(e) = stream.write_all(b"HELLO\n") {
        eprintln!("error: failed to send request: {e}");
        std::process::exit(1);
    }
    if let Err(e) = stream.flush() {
        eprintln!("error: failed to flush request: {e}");
        std::process::exit(1);
    }

    let mut reader = BufReader::new(stream);
    let mut response = String::new();
    match reader.read_line(&mut response) {
        Ok(0) => {
            eprintln!("error: server closed connection without a response");
            std::process::exit(1);
        }
        Ok(_) => {}
        Err(e) => {
            eprintln!("error: failed to read response: {e}");
            std::process::exit(1);
        }
    }

    let id = match parse_ok_id(&response) {
        Ok(id) => id,
        Err(msg) => {
            eprintln!("error: {msg}");
            std::process::exit(1);
        }
    };

    print!("raw: {response}");
    println!("id: {id}");
}

fn print_usage() {
    println!("Usage: wynd [--help] [--version]");
}

fn parse_ok_id(line: &str) -> Result<u64, String> {
    let trimmed = line.trim_end_matches(['\r', '\n']);
    let prefix = "OK id=";
    let rest = trimmed
        .strip_prefix(prefix)
        .ok_or_else(|| format!("unexpected response: {trimmed}"))?;
    rest.parse::<u64>()
        .map_err(|_| format!("invalid id in response: {trimmed}"))
}
