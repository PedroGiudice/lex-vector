//! Observa mudancas em `~/.claude/teams/*/config.json` para detectar
//! quando teammates entram ou saem de um Agent Team.

use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use notify::{Event, EventKind, RecommendedWatcher, RecursiveMode, Watcher};
use serde::Deserialize;
use tokio::sync::{broadcast, mpsc, RwLock};
use tokio::task::JoinHandle;
use tracing::{info, warn};

use crate::ws::ServerMessage;

/// Representa um membro de um Agent Team conforme serializado no config.json do Claude Code.
#[derive(Debug, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct TeamMember {
    pub name: String,
    #[serde(default)]
    pub agent_id: String,
    #[serde(default)]
    pub agent_type: String,
    #[serde(default)]
    pub model: String,
    #[serde(default)]
    pub color: String,
    #[serde(default)]
    pub tmux_pane_id: String,
}

#[derive(Debug, Deserialize)]
struct TeamConfig {
    #[serde(default)]
    name: String,
    #[serde(default)]
    members: Vec<TeamMember>,
}

/// Observa o diretorio de teams do Claude Code e emite eventos WebSocket
/// quando teammates entram ou saem.
pub struct TeamWatcher {
    teams_dir: PathBuf,
    known_members: Arc<RwLock<HashMap<String, Vec<String>>>>,
    tx: broadcast::Sender<ServerMessage>,
}

impl TeamWatcher {
    /// Cria um novo `TeamWatcher` apontando para `teams_dir`.
    #[must_use]
    pub fn new(teams_dir: PathBuf, tx: broadcast::Sender<ServerMessage>) -> Self {
        Self {
            teams_dir,
            known_members: Arc::new(RwLock::new(HashMap::new())),
            tx,
        }
    }

    /// Spawna a task de watch e retorna o `JoinHandle`.
    #[must_use]
    pub fn start(self) -> JoinHandle<()> {
        tokio::spawn(async move {
            if let Err(e) = self.run().await {
                warn!("team_watcher encerrou com erro: {e:#}");
            }
        })
    }

    async fn run(&self) -> anyhow::Result<()> {
        if !self.teams_dir.exists() {
            warn!(
                path = %self.teams_dir.display(),
                "diretorio de teams nao encontrado, team_watcher inativo"
            );
            return Ok(());
        }

        let (event_tx, mut event_rx) = mpsc::channel::<notify::Result<Event>>(100);

        let mut watcher = RecommendedWatcher::new(
            move |result| {
                let _ = event_tx.blocking_send(result);
            },
            notify::Config::default(),
        )?;

        watcher.watch(&self.teams_dir, RecursiveMode::Recursive)?;

        info!(path = %self.teams_dir.display(), "team_watcher iniciado");

        while let Some(result) = event_rx.recv().await {
            match result {
                Ok(event) => {
                    if !matches!(event.kind, EventKind::Modify(_) | EventKind::Create(_)) {
                        continue;
                    }

                    for path in event.paths {
                        if path.file_name().and_then(|n| n.to_str()) == Some("config.json") {
                            if let Err(e) = self.process_config_change(&path).await {
                                warn!(path = %path.display(), "erro ao processar config.json: {e:#}");
                            }
                        }
                    }
                }
                Err(e) => {
                    warn!("erro de notify: {e}");
                }
            }
        }

        Ok(())
    }

    async fn process_config_change(&self, path: &Path) -> anyhow::Result<()> {
        let team_name = path
            .parent()
            .and_then(|p| p.file_name())
            .and_then(|n| n.to_str())
            .unwrap_or("unknown")
            .to_owned();

        let raw = tokio::fs::read_to_string(path).await?;
        let config: TeamConfig = serde_json::from_str(&raw)?;

        // Se o config nao tem name, usa o nome do diretorio.
        let team_display_name = if config.name.is_empty() {
            team_name.clone()
        } else {
            config.name.clone()
        };

        let current_names: Vec<String> = config.members.iter().map(|m| m.name.clone()).collect();

        let mut known = self.known_members.write().await;
        let previous = known.entry(team_name.clone()).or_default();

        // Detecta novos membros.
        for member in &config.members {
            if !previous.contains(&member.name) && !member.tmux_pane_id.is_empty() {
                info!(
                    team = %team_display_name,
                    agent = %member.name,
                    "agente entrou no team"
                );
                let _ = self.tx.send(ServerMessage::AgentJoined {
                    name: member.name.clone(),
                    color: member.color.clone(),
                    model: member.model.clone(),
                    pane_id: member.tmux_pane_id.clone(),
                });
            }
        }

        // Detecta membros removidos.
        for name in previous.iter() {
            if !current_names.contains(name) {
                info!(
                    team = %team_display_name,
                    agent = %name,
                    "agente saiu do team"
                );
                let _ = self
                    .tx
                    .send(ServerMessage::AgentLeft { name: name.clone() });
            }
        }

        *previous = current_names;

        Ok(())
    }
}
