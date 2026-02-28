use serde::Serialize;

/// Parte de uma mensagem do assistente, emitida via WS como `chat_delta`.
/// Alinhado 1:1 com o tipo TypeScript `MessagePart` do frontend.
#[derive(Debug, Clone, Serialize)]
pub struct MessagePart {
    #[serde(rename = "type")]
    pub kind: MessagePartType,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<MessagePartMetadata>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MessagePartType {
    Text,
    Thinking,
    ToolUse,
    ToolResult,
}

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct MessagePartMetadata {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_error: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_streaming: Option<bool>,
}
