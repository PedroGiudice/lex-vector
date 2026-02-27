//! Unit tests for WebSocket protocol message serialization.

use ccui_backend::ws::{ClientMessage, ServerMessage};

#[test]
fn deserialize_ping() {
    let json = r#"{"type": "ping"}"#;
    let msg: ClientMessage = serde_json::from_str(json).unwrap();
    assert!(matches!(msg, ClientMessage::Ping));
}

#[test]
fn deserialize_input() {
    let json = r#"{"type": "input", "channel": "main", "text": "hello world"}"#;
    let msg: ClientMessage = serde_json::from_str(json).unwrap();
    match msg {
        ClientMessage::Input { channel, text } => {
            assert_eq!(channel, "main");
            assert_eq!(text, "hello world");
        }
        _ => panic!("expected Input"),
    }
}

#[test]
fn deserialize_resize() {
    let json = r#"{"type": "resize", "channel": "main", "cols": 120, "rows": 40}"#;
    let msg: ClientMessage = serde_json::from_str(json).unwrap();
    match msg {
        ClientMessage::Resize {
            channel,
            cols,
            rows,
        } => {
            assert_eq!(channel, "main");
            assert_eq!(cols, 120);
            assert_eq!(rows, 40);
        }
        _ => panic!("expected Resize"),
    }
}

#[test]
fn deserialize_create_session() {
    let json = r#"{"type": "create_session"}"#;
    let msg: ClientMessage = serde_json::from_str(json).unwrap();
    assert!(matches!(
        msg,
        ClientMessage::CreateSession { working_dir: None }
    ));

    let json = r#"{"type": "create_session", "working_dir": "/tmp"}"#;
    let msg: ClientMessage = serde_json::from_str(json).unwrap();
    match msg {
        ClientMessage::CreateSession { working_dir } => {
            assert_eq!(working_dir.as_deref(), Some("/tmp"));
        }
        _ => panic!("expected CreateSession"),
    }
}

#[test]
fn deserialize_destroy_session() {
    let json = r#"{"type": "destroy_session", "session_id": "abc123"}"#;
    let msg: ClientMessage = serde_json::from_str(json).unwrap();
    match msg {
        ClientMessage::DestroySession { session_id } => {
            assert_eq!(session_id, "abc123");
        }
        _ => panic!("expected DestroySession"),
    }
}

#[test]
fn serialize_pong() {
    let msg = ServerMessage::Pong;
    let json = serde_json::to_string(&msg).unwrap();
    assert!(json.contains(r#""type":"pong"#));
}

#[test]
fn serialize_output() {
    let msg = ServerMessage::Output {
        channel: "main".into(),
        data: "hello\r\n".into(),
    };
    let json = serde_json::to_string(&msg).unwrap();
    assert!(json.contains(r#""type":"output"#));
    assert!(json.contains(r#""channel":"main"#));
}

#[test]
fn serialize_agent_joined() {
    let msg = ServerMessage::AgentJoined {
        name: "researcher".into(),
        color: "blue".into(),
        model: "sonnet".into(),
        pane_id: "%34".into(),
    };
    let json = serde_json::to_string(&msg).unwrap();
    assert!(json.contains(r#""type":"agent_joined"#));
    assert!(json.contains(r#""name":"researcher"#));
}

#[test]
fn serialize_error() {
    let msg = ServerMessage::Error {
        message: "something broke".into(),
    };
    let json = serde_json::to_string(&msg).unwrap();
    assert!(json.contains(r#""type":"error"#));
}

#[test]
fn reject_unknown_type() {
    let json = r#"{"type": "unknown_garbage"}"#;
    let result = serde_json::from_str::<ClientMessage>(json);
    assert!(result.is_err());
}
