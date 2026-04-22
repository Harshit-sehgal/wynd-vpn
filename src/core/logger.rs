use std::sync::OnceLock;

use crate::core::config::{Config, LogLevel};

static LOG_LEVEL: OnceLock<LogLevel> = OnceLock::new();

pub fn init(config: &Config) {
    let _ = LOG_LEVEL.set(config.log_level);
}

pub fn info(message: &str) {
    if should_log(LogLevel::Info) {
        log("INFO", message);
    }
}

#[allow(dead_code)]
pub fn error(message: &str) {
    if should_log(LogLevel::Error) {
        log("ERROR", message);
    }
}

fn should_log(level: LogLevel) -> bool {
    let configured = LOG_LEVEL.get().copied().unwrap_or(LogLevel::Info);

    match (configured, level) {
        (LogLevel::Error, LogLevel::Error) => true,
        (LogLevel::Error, LogLevel::Info) => false,
        (LogLevel::Info, LogLevel::Error) => true,
        (LogLevel::Info, LogLevel::Info) => true,
    }
}

fn log(level: &str, message: &str) {
    println!("[{level}] {message}");
}
