//! `SessionManager` -- gerencia sessoes Claude Code via tmux headless.

use std::collections::HashMap;
use std::sync::Arc;

use tokio::sync::RwLock;

use crate::config::AppConfig;
use crate::error::AppError;
use crate::tmux::TmuxDriver;

/// Informacoes sobre uma sessao ativa.
#[derive(Debug, Clone)]
pub struct SessionInfo {
    /// UUID curto (8 chars).
    pub id: String,
    /// Nome da sessao tmux: `"{prefix}-{id}"`.
    pub tmux_session: String,
    /// ID do pane principal (ex: `%0`).
    pub main_pane_id: String,
    /// Diretorio de trabalho, se fornecido na criacao.
    pub working_dir: Option<String>,
}

/// Gerencia sessoes Claude Code via tmux headless.
///
/// Clonar e barato -- o mapa de sessoes e compartilhado via `Arc`.
#[derive(Debug, Clone)]
pub struct SessionManager {
    config: AppConfig,
    tmux: TmuxDriver,
    sessions: Arc<RwLock<HashMap<String, SessionInfo>>>,
}

impl SessionManager {
    /// Cria uma nova instancia do `SessionManager`.
    #[must_use]
    pub fn new(config: AppConfig, tmux: TmuxDriver) -> Self {
        Self {
            config,
            tmux,
            sessions: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Cria uma nova sessao tmux headless e a registra no mapa interno.
    ///
    /// Nao inicia o Claude Code -- isso deve ser feito externamente.
    /// Retorna o `session_id` (8 primeiros chars de um UUID v4).
    ///
    /// # Errors
    ///
    /// Retorna `AppError::Io` se nao conseguir criar o diretorio de logs.
    /// Retorna `AppError::Tmux` se o tmux falhar.
    /// Cria uma nova sessao tmux headless e a registra no mapa interno.
    ///
    /// Se `case_id` for fornecido, resolve o diretorio via `config.cases_dir / case_id`
    /// e valida que o diretorio existe. A sessao tmux e criada com esse working_dir.
    ///
    /// Retorna o `session_id` (8 primeiros chars de um UUID v4).
    ///
    /// # Errors
    ///
    /// Retorna `AppError::Io` se nao conseguir criar o diretorio de logs.
    /// Retorna `AppError::Tmux` se o tmux falhar.
    /// Retorna `AppError::InvalidCaseId` se o case_id nao corresponder a um diretorio existente.
    pub async fn create_session(&self, case_id: Option<&str>) -> Result<String, AppError> {
        // Garante que o diretorio de logs existe.
        tokio::fs::create_dir_all(&self.config.pane_log_dir).await?;

        // Resolve case_id -> working_dir
        let working_dir = if let Some(cid) = case_id {
            let path = self.config.cases_dir.join(cid);
            if !path.is_dir() {
                return Err(AppError::Tmux(format!(
                    "case_id '{cid}' nao encontrado em {}",
                    self.config.cases_dir.display()
                )));
            }
            Some(path.to_string_lossy().to_string())
        } else {
            None
        };

        let session_id = short_uuid();
        let tmux_session = format!("{}-{session_id}", self.config.tmux_session_prefix);

        self.tmux
            .new_session_in_dir(&tmux_session, 220, 50, working_dir.as_deref())
            .await?;

        // Descobre o pane principal criado automaticamente.
        let panes = self.tmux.list_panes(&tmux_session).await?;
        let main_pane_id = panes
            .into_iter()
            .next()
            .ok_or_else(|| AppError::Tmux(format!("nenhum pane encontrado em {tmux_session}")))?
            .id;

        let info = SessionInfo {
            id: session_id.clone(),
            tmux_session,
            main_pane_id,
            working_dir,
        };

        self.sessions.write().await.insert(session_id.clone(), info);

        Ok(session_id)
    }

    /// Destroi uma sessao pelo seu `session_id`.
    ///
    /// # Errors
    ///
    /// Retorna `AppError::SessionNotFound` se o id nao existir no mapa.
    /// Retorna `AppError::Tmux` se o tmux falhar ao encerrar a sessao.
    pub async fn destroy_session(&self, session_id: &str) -> Result<(), AppError> {
        let info = self
            .sessions
            .write()
            .await
            .remove(session_id)
            .ok_or_else(|| AppError::SessionNotFound {
                id: session_id.to_owned(),
            })?;

        self.tmux.kill_session(&info.tmux_session).await
    }

    /// Retorna todas as sessoes ativas.
    pub async fn list_sessions(&self) -> Vec<SessionInfo> {
        self.sessions.read().await.values().cloned().collect()
    }

    /// Retorna a sessao com o `session_id` dado, ou `None` se nao existir.
    pub async fn get_session(&self, session_id: &str) -> Option<SessionInfo> {
        self.sessions.read().await.get(session_id).cloned()
    }

    /// Descobre sessoes tmux orfas (criadas fora desta instancia) e as registra.
    ///
    /// Sessoes ja presentes no mapa sao ignoradas.
    /// Retorna os `session_id`s das sessoes recuparadas.
    ///
    /// # Errors
    ///
    /// Retorna `AppError::Tmux` se a listagem tmux falhar.
    pub async fn recover_orphan_sessions(&self) -> Result<Vec<String>, AppError> {
        let prefix = &self.config.tmux_session_prefix;
        let tmux_sessions = self.tmux.list_sessions_with_prefix(prefix).await?;

        let mut recovered = Vec::new();
        let mut map = self.sessions.write().await;

        for tmux_session in tmux_sessions {
            // Extrai o session_id removendo o prefixo e o separador.
            let separator = format!("{prefix}-");
            let Some(session_id) = tmux_session.strip_prefix(&separator) else {
                continue;
            };

            if map.contains_key(session_id) {
                continue;
            }

            // Tenta descobrir o pane principal.
            let panes = self
                .tmux
                .list_panes(&tmux_session)
                .await
                .unwrap_or_default();
            let main_pane_id = panes.into_iter().next().map(|p| p.id).unwrap_or_default();

            let info = SessionInfo {
                id: session_id.to_owned(),
                tmux_session: tmux_session.clone(),
                main_pane_id,
                working_dir: None,
            };

            map.insert(session_id.to_owned(), info);
            recovered.push(session_id.to_owned());
        }

        Ok(recovered)
    }

    /// Insere uma sessao fake para testes de integracao.
    #[doc(hidden)]
    pub async fn insert_fake_session(&self, session_id: &str) {
        let info = SessionInfo {
            id: session_id.to_owned(),
            tmux_session: format!("fake-{session_id}"),
            main_pane_id: "%0".to_owned(),
            working_dir: None,
        };
        self.sessions
            .write()
            .await
            .insert(session_id.to_owned(), info);
    }
}

/// Gera os primeiros 8 caracteres de um UUID v4.
fn short_uuid() -> String {
    let id = uuid::Uuid::new_v4().to_string();
    id[..8].to_owned()
}
