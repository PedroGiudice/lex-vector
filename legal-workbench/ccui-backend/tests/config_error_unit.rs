use std::io;
use std::path::PathBuf;

use axum::http::StatusCode;
use axum::response::IntoResponse;
use ccui_backend::config::AppConfig;
use ccui_backend::error::AppError;

// ---------------------------------------------------------------------------
// config.rs -- defaults
// ---------------------------------------------------------------------------

#[test]
fn default_port_is_8005() {
    let cfg = AppConfig::default();
    assert_eq!(cfg.port, 8005);
}

#[test]
fn default_host_is_0000() {
    let cfg = AppConfig::default();
    assert_eq!(cfg.host, "0.0.0.0");
}

#[test]
fn default_prefix_is_ccui() {
    let cfg = AppConfig::default();
    assert_eq!(cfg.tmux_session_prefix, "ccui");
}

#[test]
fn default_claude_bin() {
    let cfg = AppConfig::default();
    assert_eq!(cfg.claude_bin, "claude");
}

#[test]
fn default_claude_flags() {
    let cfg = AppConfig::default();
    assert!(
        cfg.claude_flags
            .iter()
            .any(|f| f == "--dangerously-skip-permissions"),
        "esperado '--dangerously-skip-permissions' em claude_flags, obtido: {:?}",
        cfg.claude_flags
    );
}

// ---------------------------------------------------------------------------
// config.rs -- from_env (rodar com --test-threads=1 para evitar races de env)
// ---------------------------------------------------------------------------

#[test]
fn from_env_reads_port() {
    // SAFETY: teste single-thread (--test-threads=1)
    unsafe { std::env::set_var("CCUI_PORT", "9999") };
    let cfg = AppConfig::from_env();
    unsafe { std::env::remove_var("CCUI_PORT") };
    assert_eq!(cfg.port, 9999);
}

#[test]
fn from_env_reads_host() {
    unsafe { std::env::set_var("CCUI_HOST", "127.0.0.1") };
    let cfg = AppConfig::from_env();
    unsafe { std::env::remove_var("CCUI_HOST") };
    assert_eq!(cfg.host, "127.0.0.1");
}

#[test]
fn from_env_invalid_port_keeps_default() {
    unsafe { std::env::set_var("CCUI_PORT", "abc") };
    let cfg = AppConfig::from_env();
    unsafe { std::env::remove_var("CCUI_PORT") };
    assert_eq!(cfg.port, 8005);
}

#[test]
fn from_env_without_vars_uses_defaults() {
    unsafe {
        std::env::remove_var("CCUI_PORT");
        std::env::remove_var("CCUI_HOST");
    }
    let cfg = AppConfig::from_env();
    assert_eq!(cfg.port, 8005);
    assert_eq!(cfg.host, "0.0.0.0");
}

// ---------------------------------------------------------------------------
// config.rs -- cases_dir
// ---------------------------------------------------------------------------

#[test]
fn default_cases_dir() {
    let cfg = AppConfig::default();
    assert_eq!(cfg.cases_dir, PathBuf::from("/home/opc/casos"));
}

#[test]
fn from_env_reads_cases_dir() {
    unsafe { std::env::set_var("CCUI_CASES_DIR", "/tmp/test-cases") };
    let cfg = AppConfig::from_env();
    unsafe { std::env::remove_var("CCUI_CASES_DIR") };
    assert_eq!(cfg.cases_dir, PathBuf::from("/tmp/test-cases"));
}

// ---------------------------------------------------------------------------
// error.rs -- IntoResponse status codes
// ---------------------------------------------------------------------------

#[test]
fn session_not_found_is_404() {
    let err = AppError::SessionNotFound {
        id: "sess-abc".into(),
    };
    let response = err.into_response();
    assert_eq!(response.status(), StatusCode::NOT_FOUND);
}

#[test]
fn pane_not_found_is_404() {
    let err = AppError::PaneNotFound {
        session_id: "sess-1".into(),
        pane_id: "pane-2".into(),
    };
    let response = err.into_response();
    assert_eq!(response.status(), StatusCode::NOT_FOUND);
}

#[test]
fn tmux_error_is_500() {
    let err = AppError::Tmux("falha no tmux".into());
    let response = err.into_response();
    assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
}

#[test]
fn io_error_is_500() {
    let err = AppError::Io(io::Error::new(io::ErrorKind::Other, "erro de io"));
    let response = err.into_response();
    assert_eq!(response.status(), StatusCode::INTERNAL_SERVER_ERROR);
}

// ---------------------------------------------------------------------------
// error.rs -- Display
// ---------------------------------------------------------------------------

#[test]
fn display_session_not_found() {
    let id = "sess-xyz".to_string();
    let err = AppError::SessionNotFound { id: id.clone() };
    let msg = format!("{err}");
    assert!(
        msg.contains(&id),
        "esperado id '{id}' na mensagem, obtido: '{msg}'"
    );
}

#[test]
fn display_pane_not_found() {
    let session_id = "sess-abc".to_string();
    let pane_id = "pane-99".to_string();
    let err = AppError::PaneNotFound {
        session_id: session_id.clone(),
        pane_id: pane_id.clone(),
    };
    let msg = format!("{err}");
    assert!(
        msg.contains(&pane_id),
        "esperado pane_id '{pane_id}' na mensagem, obtido: '{msg}'"
    );
    assert!(
        msg.contains(&session_id),
        "esperado session_id '{session_id}' na mensagem, obtido: '{msg}'"
    );
}
