use std::path::PathBuf;

/// Application configuration, loaded from environment variables with sensible defaults.
#[derive(Debug, Clone)]
pub struct AppConfig {
    pub host: String,
    pub port: u16,
    pub claude_bin: String,
    pub claude_flags: Vec<String>,
    pub teams_dir: PathBuf,
    pub tmux_session_prefix: String,
    pub pane_log_dir: PathBuf,
    pub ws_ping_interval_secs: u64,
    pub ws_pong_timeout_secs: u64,
    pub pane_health_interval_secs: u64,
    pub capture_poll_ms: u64,
    pub cases_dir: PathBuf,
}

impl Default for AppConfig {
    fn default() -> Self {
        let home = std::env::var("HOME").unwrap_or_else(|_| "/home/opc".into());
        Self {
            host: "0.0.0.0".into(),
            port: 8005,
            claude_bin: "claude".into(),
            claude_flags: vec!["--dangerously-skip-permissions".into()],
            teams_dir: PathBuf::from(format!("{home}/.claude/teams")),
            tmux_session_prefix: "ccui".into(),
            pane_log_dir: PathBuf::from("/tmp/ccui-pane-logs"),
            ws_ping_interval_secs: 30,
            ws_pong_timeout_secs: 10,
            pane_health_interval_secs: 5,
            capture_poll_ms: 200,
            cases_dir: PathBuf::from(format!("{home}/casos")),
        }
    }
}

impl AppConfig {
    /// Load configuration from environment variables, falling back to defaults.
    #[must_use]
    pub fn from_env() -> Self {
        let mut cfg = Self::default();
        if let Ok(p) = std::env::var("CCUI_PORT") {
            if let Ok(port) = p.parse() {
                cfg.port = port;
            }
        }
        if let Ok(h) = std::env::var("CCUI_HOST") {
            cfg.host = h;
        }
        if let Ok(d) = std::env::var("CCUI_CASES_DIR") {
            cfg.cases_dir = PathBuf::from(d);
        }
        cfg
    }
}
