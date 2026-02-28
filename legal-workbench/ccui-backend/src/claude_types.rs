//! Tipos para deserializacao do output NDJSON do Claude Code (`--output-format stream-json`).
//!
//! Referencia: <https://platform.claude.com/docs/en/agent-sdk/typescript>
//! O stream emite uma linha JSON por evento. Cada linha e um `SDKMessage`.

use serde::Deserialize;

// ---------------------------------------------------------------------------
// SDKMessage -- union discriminada por `type`
// ---------------------------------------------------------------------------

/// Mensagem emitida pelo Claude Code em modo stream-json.
/// Apenas os tipos relevantes para o frontend sao modelados;
/// variantes desconhecidas sao capturadas por `Unknown`.
#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "type")]
pub enum SDKMessage {
    /// Inicializacao da sessao.
    #[serde(rename = "system")]
    System(SystemMessage),

    /// Resposta completa do assistente (um turno inteiro).
    #[serde(rename = "assistant")]
    Assistant(AssistantMessage),

    /// Mensagem do usuario (replay ou sintetica).
    #[serde(rename = "user")]
    User(UserMessage),

    /// Resultado final da query.
    #[serde(rename = "result")]
    Result(ResultMessage),

    /// Evento de streaming parcial (requer --include-partial-messages).
    #[serde(rename = "stream_event")]
    StreamEvent(StreamEventMessage),
}

// ---------------------------------------------------------------------------
// System
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct SystemMessage {
    pub subtype: String,
    pub session_id: String,
    #[serde(default)]
    pub model: Option<String>,
    #[serde(default)]
    pub tools: Option<Vec<String>>,
    #[serde(default)]
    pub claude_code_version: Option<String>,
    #[serde(default)]
    pub cwd: Option<String>,
}

// ---------------------------------------------------------------------------
// Assistant
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct AssistantMessage {
    pub uuid: String,
    pub session_id: String,
    pub message: AnthropicMessage,
    #[serde(default)]
    pub parent_tool_use_id: Option<String>,
}

/// Subconjunto do `BetaMessage` da Anthropic API.
#[derive(Debug, Clone, Deserialize)]
pub struct AnthropicMessage {
    pub id: String,
    pub content: Vec<ContentBlock>,
    pub model: String,
    #[serde(default)]
    pub stop_reason: Option<String>,
    #[serde(default)]
    pub usage: Option<Usage>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct Usage {
    #[serde(default)]
    pub input_tokens: u64,
    #[serde(default)]
    pub output_tokens: u64,
    #[serde(default)]
    pub cache_read_input_tokens: Option<u64>,
    #[serde(default)]
    pub cache_creation_input_tokens: Option<u64>,
}

// ---------------------------------------------------------------------------
// Content blocks
// ---------------------------------------------------------------------------

/// Bloco de conteudo dentro de uma mensagem do assistente.
#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "type")]
pub enum ContentBlock {
    #[serde(rename = "text")]
    Text { text: String },

    #[serde(rename = "thinking")]
    Thinking {
        thinking: String,
        #[serde(default)]
        signature: Option<String>,
    },

    #[serde(rename = "tool_use")]
    ToolUse {
        id: String,
        name: String,
        input: serde_json::Value,
    },

    #[serde(rename = "tool_result")]
    ToolResult {
        tool_use_id: String,
        content: serde_json::Value,
        #[serde(default)]
        is_error: Option<bool>,
    },
}

// ---------------------------------------------------------------------------
// User
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct UserMessage {
    pub session_id: String,
    #[serde(default)]
    pub uuid: Option<String>,
    #[serde(default)]
    pub parent_tool_use_id: Option<String>,
}

// ---------------------------------------------------------------------------
// Result
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct ResultMessage {
    pub session_id: String,
    pub subtype: String,
    #[serde(default)]
    pub duration_ms: Option<u64>,
    #[serde(default)]
    pub is_error: Option<bool>,
    #[serde(default)]
    pub num_turns: Option<u64>,
    #[serde(default)]
    pub result: Option<String>,
    #[serde(default)]
    pub total_cost_usd: Option<f64>,
}

// ---------------------------------------------------------------------------
// StreamEvent (partial messages)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Deserialize)]
pub struct StreamEventMessage {
    pub session_id: String,
    pub uuid: String,
    #[serde(default)]
    pub parent_tool_use_id: Option<String>,
    /// O evento raw da Anthropic Streaming API.
    /// Deserializado como Value generico porque o schema e extenso
    /// e varia entre versoes. O backend extrai apenas o necessario.
    pub event: serde_json::Value,
}
