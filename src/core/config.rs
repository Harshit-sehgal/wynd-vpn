#[derive(Debug, Clone)]
pub struct Config {
    pub log_level: LogLevel,
    pub server_host: String,
    pub server_port: u16,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LogLevel {
    #[allow(dead_code)]
    Error,
    Info,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            log_level: LogLevel::Info,
            server_host: "161.118.177.7".to_string(),
            server_port: 9000,
        }
    }
}

impl Config {
    pub fn load() -> Self {
        Self::default()
    }
}
