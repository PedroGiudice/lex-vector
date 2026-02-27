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
        ClientMessage::CreateSession { case_id: None }
    ));
}

#[test]
fn deserialize_create_session_with_case_id() {
    let json = r#"{"type": "create_session", "case_id": "bianka-sfdc"}"#;
    let msg: ClientMessage = serde_json::from_str(json).unwrap();
    match msg {
        ClientMessage::CreateSession { case_id } => {
            assert_eq!(case_id.as_deref(), Some("bianka-sfdc"));
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

// --- Serialize gaps ---

#[test]
fn serialize_session_created() {
    let msg = ServerMessage::SessionCreated {
        session_id: "abc".into(),
        case_id: None,
    };
    let json = serde_json::to_string(&msg).unwrap();
    assert!(
        json.contains("session_created"),
        "missing session_created in: {json}"
    );
    assert!(json.contains("abc"), "missing session_id value in: {json}");
    assert!(
        !json.contains("case_id"),
        "case_id should be skipped when None: {json}"
    );
}

#[test]
fn serialize_session_created_with_case_id() {
    let msg = ServerMessage::SessionCreated {
        session_id: "abc".into(),
        case_id: Some("bianka-sfdc".into()),
    };
    let json = serde_json::to_string(&msg).unwrap();
    assert!(json.contains("bianka-sfdc"), "missing case_id in: {json}");
}

#[test]
fn serialize_session_ended() {
    let msg = ServerMessage::SessionEnded {
        session_id: "xyz".into(),
    };
    let json = serde_json::to_string(&msg).unwrap();
    assert!(
        json.contains("session_ended"),
        "missing session_ended in: {json}"
    );
    assert!(json.contains("xyz"), "missing session_id value in: {json}");
}

#[test]
fn serialize_agent_left() {
    let msg = ServerMessage::AgentLeft {
        name: "researcher".into(),
    };
    let json = serde_json::to_string(&msg).unwrap();
    assert!(json.contains("agent_left"), "missing agent_left in: {json}");
    assert!(json.contains("researcher"), "missing name value in: {json}");
}

#[test]
fn serialize_agent_crashed() {
    let msg = ServerMessage::AgentCrashed {
        name: "strategist".into(),
    };
    let json = serde_json::to_string(&msg).unwrap();
    assert!(
        json.contains("agent_crashed"),
        "missing agent_crashed in: {json}"
    );
    assert!(json.contains("strategist"), "missing name value in: {json}");
}

// --- Deserialize error paths ---

#[test]
fn deserialize_input_missing_channel() {
    let json = r#"{"type": "input", "text": "hi"}"#;
    let result = serde_json::from_str::<ClientMessage>(json);
    assert!(result.is_err(), "expected error for missing channel field");
}

#[test]
fn deserialize_input_missing_text() {
    let json = r#"{"type": "input", "channel": "main"}"#;
    let result = serde_json::from_str::<ClientMessage>(json);
    assert!(result.is_err(), "expected error for missing text field");
}

#[test]
fn deserialize_resize_missing_cols() {
    let json = r#"{"type": "resize", "channel": "x", "rows": 40}"#;
    let result = serde_json::from_str::<ClientMessage>(json);
    assert!(result.is_err(), "expected error for missing cols field");
}

#[test]
fn deserialize_destroy_missing_session_id() {
    let json = r#"{"type": "destroy_session"}"#;
    let result = serde_json::from_str::<ClientMessage>(json);
    assert!(
        result.is_err(),
        "expected error for missing session_id field"
    );
}

#[test]
fn deserialize_empty_json() {
    let json = r#"{}"#;
    let result = serde_json::from_str::<ClientMessage>(json);
    assert!(result.is_err(), "expected error for empty JSON object");
}

#[test]
fn deserialize_not_json() {
    let input = "not json at all";
    let result = serde_json::from_str::<ClientMessage>(input);
    assert!(result.is_err(), "expected error for non-JSON input");
}

// --- Roundtrip ---

#[test]
fn roundtrip_output() {
    let msg = ServerMessage::Output {
        channel: "main".into(),
        data: "hello\r\n".into(),
    };
    let json = serde_json::to_string(&msg).unwrap();
    let value: serde_json::Value = serde_json::from_str(&json).unwrap();
    assert_eq!(value["type"], "output");
    assert_eq!(value["channel"], "main");
    assert_eq!(value["data"], "hello\r\n");
}

#[test]
fn roundtrip_agent_joined() {
    let msg = ServerMessage::AgentJoined {
        name: "tester".into(),
        color: "green".into(),
        model: "haiku".into(),
        pane_id: "%42".into(),
    };
    let json = serde_json::to_string(&msg).unwrap();
    let value: serde_json::Value = serde_json::from_str(&json).unwrap();
    assert_eq!(value["type"], "agent_joined");
    assert_eq!(value["name"], "tester");
    assert_eq!(value["color"], "green");
    assert_eq!(value["model"], "haiku");
    assert_eq!(value["pane_id"], "%42");
}
