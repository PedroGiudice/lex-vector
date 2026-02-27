//! `TmuxDriver` -- encapsula toda interacao com o binario tmux.
//!
//! Nenhum outro modulo deve chamar tmux diretamente. Este modulo e o unico
//! ponto de entrada para subprocessos tmux.

use std::path::Path;

use tokio::process::Command;

use crate::error::AppError;

/// Informacoes sobre um painel tmux.
#[derive(Debug, Clone)]
pub struct PaneInfo {
    /// ID do painel (ex: `%0`).
    pub id: String,
    /// Se o painel esta morto (processo encerrado).
    pub dead: bool,
    /// Comando atual rodando no painel.
    pub command: String,
    /// PID do processo no painel.
    pub pid: u32,
}

/// Driver que encapsula toda interacao com o binario `tmux`.
///
/// Sem estado interno -- wrapper puro sobre subprocess.
#[derive(Debug, Clone)]
pub struct TmuxDriver;

impl Default for TmuxDriver {
    fn default() -> Self {
        Self
    }
}

#[allow(clippy::missing_errors_doc)]
impl TmuxDriver {
    /// Cria uma nova instancia do driver.
    #[must_use]
    pub fn new() -> Self {
        Self
    }

    /// Cria uma nova sessao tmux detached com dimensoes especificadas.
    pub async fn new_session(&self, name: &str, width: u16, height: u16) -> Result<(), AppError> {
        self.run(&[
            "new-session",
            "-d",
            "-s",
            name,
            "-x",
            &width.to_string(),
            "-y",
            &height.to_string(),
        ])
        .await
    }

    /// Retorna `true` se a sessao com o nome dado existe.
    pub async fn session_exists(&self, name: &str) -> bool {
        Command::new("tmux")
            .args(["has-session", "-t", name])
            .output()
            .await
            .map(|o| o.status.success())
            .unwrap_or(false)
    }

    /// Encerra a sessao tmux.
    pub async fn kill_session(&self, name: &str) -> Result<(), AppError> {
        self.run(&["kill-session", "-t", name]).await
    }

    /// Envia texto para um painel usando `send-keys -l` (literal) seguido de Enter.
    pub async fn send_keys(
        &self,
        session: &str,
        pane_id: &str,
        text: &str,
    ) -> Result<(), AppError> {
        let target = Self::resolve_target(session, pane_id);
        self.run(&["send-keys", "-t", &target, "-l", text]).await?;
        self.run(&["send-keys", "-t", &target, "Enter"]).await
    }

    /// Captura o conteudo visivel do painel, preservando escapes ANSI (`-e`).
    pub async fn capture_pane(&self, session: &str, pane_id: &str) -> Result<String, AppError> {
        let target = Self::resolve_target(session, pane_id);
        self.run_output(&["capture-pane", "-e", "-p", "-t", &target])
            .await
    }

    /// Lista os paineis de uma sessao.
    ///
    /// Formato interno: `#{pane_id}\t#{pane_dead}\t#{pane_current_command}\t#{pane_pid}`
    pub async fn list_panes(&self, session: &str) -> Result<Vec<PaneInfo>, AppError> {
        let fmt = "#{pane_id}\t#{pane_dead}\t#{pane_current_command}\t#{pane_pid}";
        let raw = self
            .run_output(&["list-panes", "-t", session, "-F", fmt])
            .await?;

        raw.lines()
            .filter(|l| !l.trim().is_empty())
            .map(|line| {
                let parts: Vec<&str> = line.splitn(4, '\t').collect();
                if parts.len() < 4 {
                    return Err(AppError::Tmux(format!(
                        "formato inesperado de list-panes: {line}"
                    )));
                }
                let pid: u32 = parts[3].trim().parse().map_err(|_| {
                    AppError::Tmux(format!("pid invalido em list-panes: {}", parts[3]))
                })?;
                Ok(PaneInfo {
                    id: parts[0].to_owned(),
                    dead: parts[1].trim() == "1",
                    command: parts[2].to_owned(),
                    pid,
                })
            })
            .collect()
    }

    /// Redimensiona um painel.
    pub async fn resize_pane(&self, pane_id: &str, cols: u16, rows: u16) -> Result<(), AppError> {
        self.run(&[
            "resize-pane",
            "-t",
            pane_id,
            "-x",
            &cols.to_string(),
            "-y",
            &rows.to_string(),
        ])
        .await
    }

    /// Inicia o pipe de saida do painel para um arquivo de log.
    ///
    /// Usa `pipe-pane -o` para capturar apenas saida nova.
    pub async fn pipe_pane(
        &self,
        pane_id: &str,
        log_path: impl AsRef<Path>,
    ) -> Result<(), AppError> {
        let path = log_path.as_ref().to_string_lossy();
        let cmd = format!("cat >> '{path}'");
        self.run(&["pipe-pane", "-o", "-t", pane_id, &cmd]).await
    }

    /// Para o pipe de saida do painel.
    pub async fn unpipe_pane(&self, pane_id: &str) -> Result<(), AppError> {
        self.run(&["pipe-pane", "-t", pane_id]).await
    }

    /// Lista nomes de sessoes que comecam com o prefixo dado.
    pub async fn list_sessions_with_prefix(&self, prefix: &str) -> Result<Vec<String>, AppError> {
        let raw = self
            .run_output(&["list-sessions", "-F", "#{session_name}"])
            .await?;

        Ok(raw
            .lines()
            .filter(|l| l.starts_with(prefix))
            .map(ToOwned::to_owned)
            .collect())
    }

    /// Envia texto multi-linha via `load-buffer` + `paste-buffer`.
    ///
    /// Util para blocos de texto que contem newlines.
    pub async fn send_text_multiline(
        &self,
        session: &str,
        pane_id: &str,
        text: &str,
    ) -> Result<(), AppError> {
        let target = Self::resolve_target(session, pane_id);
        // Carrega o texto num buffer tmux temporario
        let mut child = Command::new("tmux")
            .args(["load-buffer", "-"])
            .stdin(std::process::Stdio::piped())
            .spawn()
            .map_err(|e| AppError::Tmux(format!("spawn load-buffer: {e}")))?;

        if let Some(stdin) = child.stdin.take() {
            use tokio::io::AsyncWriteExt as _;
            let mut stdin = stdin;
            stdin
                .write_all(text.as_bytes())
                .await
                .map_err(|e| AppError::Tmux(format!("write load-buffer stdin: {e}")))?;
        }

        child
            .wait()
            .await
            .map_err(|e| AppError::Tmux(format!("load-buffer wait: {e}")))?;

        self.run(&["paste-buffer", "-t", &target]).await
    }

    // -------------------------------------------------------------------------
    // Auxiliares privados
    // -------------------------------------------------------------------------

    /// Monta o target para comandos tmux.
    /// Pane IDs globais (`%XX`) nao precisam de prefixo de sessao.
    fn resolve_target(session: &str, pane_id: &str) -> String {
        if pane_id.starts_with('%') {
            pane_id.to_owned()
        } else {
            format!("{session}:{pane_id}")
        }
    }

    /// Executa um comando tmux, retornando erro se o exit status nao for zero.
    async fn run(&self, args: &[&str]) -> Result<(), AppError> {
        let output = Command::new("tmux")
            .args(args)
            .output()
            .await
            .map_err(|e| AppError::Tmux(format!("falha ao executar tmux: {e}")))?;

        if output.status.success() {
            return Ok(());
        }

        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(AppError::Tmux(format!(
            "tmux {} falhou ({}): {}",
            args.first().copied().unwrap_or(""),
            output.status,
            stderr.trim()
        )))
    }

    /// Executa um comando tmux e retorna stdout como `String`.
    async fn run_output(&self, args: &[&str]) -> Result<String, AppError> {
        let output = Command::new("tmux")
            .args(args)
            .output()
            .await
            .map_err(|e| AppError::Tmux(format!("falha ao executar tmux: {e}")))?;

        if output.status.success() {
            let s = String::from_utf8_lossy(&output.stdout).into_owned();
            return Ok(s);
        }

        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(AppError::Tmux(format!(
            "tmux {} falhou ({}): {}",
            args.first().copied().unwrap_or(""),
            output.status,
            stderr.trim()
        )))
    }
}
