//! [`PaneProxy`] -- bridge bidirecional entre panes tmux e broadcast WebSocket.
//!
//! O proxy registra canais (mapeamentos nome -> pane tmux), inicia pipe de saida
//! via `pipe-pane`, faz tail do arquivo de log resultante e publica no broadcast.
//! Input do WebSocket e encaminhado ao pane via `send_keys` ou `send_text_multiline`.

use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;

use tokio::sync::{broadcast, RwLock};
use tokio_util::sync::CancellationToken;

use crate::config::AppConfig;
use crate::error::AppError;
use crate::tmux::TmuxDriver;
use crate::ws::ServerMessage;

// ---------------------------------------------------------------------------
// Tipos internos
// ---------------------------------------------------------------------------

/// Mapeamento de um canal logico para um pane tmux.
struct ChannelMapping {
    pane_id: String,
    tmux_session: String,
    log_path: PathBuf,
    cancel: CancellationToken,
}

// ---------------------------------------------------------------------------
// PaneProxy
// ---------------------------------------------------------------------------

/// Bridge bidirecional: output de panes tmux -> broadcast WebSocket,
/// input do WebSocket -> panes tmux.
#[derive(Clone)]
pub struct PaneProxy {
    config: AppConfig,
    tmux: TmuxDriver,
    channels: Arc<RwLock<HashMap<String, ChannelMapping>>>,
    tx: broadcast::Sender<ServerMessage>,
}

#[allow(clippy::missing_errors_doc)]
impl PaneProxy {
    /// Cria uma nova instancia do proxy.
    #[must_use]
    pub fn new(config: AppConfig, tmux: TmuxDriver, tx: broadcast::Sender<ServerMessage>) -> Self {
        Self {
            config,
            tmux,
            channels: Arc::new(RwLock::new(HashMap::new())),
            tx,
        }
    }

    /// Registra um canal mapeando-o a um pane tmux.
    ///
    /// Cria o diretorio de log se necessario, inicia `pipe-pane` no tmux
    /// e spawna a task de tail do arquivo de log.
    pub async fn register_channel(
        &self,
        channel_name: &str,
        tmux_session: &str,
        pane_id: &str,
    ) -> Result<(), AppError> {
        tokio::fs::create_dir_all(&self.config.pane_log_dir).await?;

        let log_path = self.config.pane_log_dir.join(format!("{channel_name}.log"));

        // Cria arquivo de log vazio (trunca se ja existir)
        tokio::fs::File::create(&log_path).await?;

        // Inicia pipe do tmux para o arquivo de log
        self.tmux.pipe_pane(pane_id, &log_path).await?;

        let cancel = CancellationToken::new();

        let mapping = ChannelMapping {
            pane_id: pane_id.to_owned(),
            tmux_session: tmux_session.to_owned(),
            log_path: log_path.clone(),
            cancel: cancel.clone(),
        };

        self.channels
            .write()
            .await
            .insert(channel_name.to_owned(), mapping);

        // Spawna task de tail em background com cancellation
        let tx = self.tx.clone();
        let channel = channel_name.to_owned();
        tokio::spawn(async move {
            tokio::select! {
                result = tail_log(&log_path, &channel, &tx) => {
                    if let Err(e) = result {
                        tracing::warn!(channel = %channel, "tail_log encerrado com erro: {e}");
                    }
                }
                () = cancel.cancelled() => {
                    tracing::debug!(channel = %channel, "tail_log cancelado");
                }
            }
        });

        Ok(())
    }

    /// Remove o registro de um canal. Para a task de tail, o pipe tmux e o log.
    pub async fn unregister_channel(&self, channel_name: &str) -> Result<(), AppError> {
        let mapping = self
            .channels
            .write()
            .await
            .remove(channel_name)
            .ok_or_else(|| AppError::PaneNotFound {
                session_id: String::new(),
                pane_id: channel_name.to_owned(),
            })?;

        // Cancela a task de tail ANTES de limpar recursos
        mapping.cancel.cancel();

        self.tmux.unpipe_pane(&mapping.pane_id).await?;
        let _ = tokio::fs::remove_file(&mapping.log_path).await;

        Ok(())
    }

    /// Envia texto para o pane associado ao canal.
    pub async fn send_input(&self, channel_name: &str, text: &str) -> Result<(), AppError> {
        let guard = self.channels.read().await;
        let mapping = guard
            .get(channel_name)
            .ok_or_else(|| AppError::PaneNotFound {
                session_id: String::new(),
                pane_id: channel_name.to_owned(),
            })?;

        if text.contains('\n') {
            self.tmux
                .send_text_multiline(&mapping.tmux_session, &mapping.pane_id, text)
                .await
        } else {
            self.tmux
                .send_keys(&mapping.tmux_session, &mapping.pane_id, text)
                .await
        }
    }

    /// Redimensiona o pane associado ao canal.
    pub async fn resize_channel(
        &self,
        channel_name: &str,
        cols: u16,
        rows: u16,
    ) -> Result<(), AppError> {
        let guard = self.channels.read().await;
        let mapping = guard
            .get(channel_name)
            .ok_or_else(|| AppError::PaneNotFound {
                session_id: String::new(),
                pane_id: channel_name.to_owned(),
            })?;

        self.tmux.resize_pane(&mapping.pane_id, cols, rows).await
    }

    /// Captura o conteudo visivel atual do pane associado ao canal.
    pub async fn capture_snapshot(&self, channel_name: &str) -> Result<String, AppError> {
        let guard = self.channels.read().await;
        let mapping = guard
            .get(channel_name)
            .ok_or_else(|| AppError::PaneNotFound {
                session_id: String::new(),
                pane_id: channel_name.to_owned(),
            })?;

        self.tmux
            .capture_pane(&mapping.tmux_session, &mapping.pane_id)
            .await
    }

    /// Retorna a lista de nomes de canais registrados.
    pub async fn list_channels(&self) -> Vec<String> {
        self.channels.read().await.keys().cloned().collect()
    }

    /// Retorna detalhes dos canais ativos: `(nome, pane_id)`.
    pub async fn list_channel_details(&self) -> Vec<(String, String)> {
        self.channels
            .read()
            .await
            .iter()
            .map(|(name, mapping)| (name.clone(), mapping.pane_id.clone()))
            .collect()
    }
}

// ---------------------------------------------------------------------------
// tail_log
// ---------------------------------------------------------------------------

/// Faz tail de um arquivo de log, publicando novos dados no broadcast.
async fn tail_log(
    path: &std::path::Path,
    channel: &str,
    tx: &broadcast::Sender<ServerMessage>,
) -> Result<(), std::io::Error> {
    use tokio::io::AsyncReadExt as _;

    let mut file = tokio::fs::File::open(path).await?;
    let mut buf = vec![0u8; 8192];

    loop {
        let n = file.read(&mut buf).await?;
        if n == 0 {
            tokio::time::sleep(std::time::Duration::from_millis(100)).await;
            continue;
        }

        let data = String::from_utf8_lossy(&buf[..n]).into_owned();
        let _ = tx.send(ServerMessage::Output {
            channel: channel.to_owned(),
            data,
        });
    }
}
