//! Testes de integração para o módulo `team_watcher`.
//!
//! Executa com: `cargo test --test team_watcher_integration -- --test-threads=1`

use std::time::Duration;

use ccui_backend::team_watcher::TeamWatcher;
use ccui_backend::ws::ServerMessage;
use tokio::sync::broadcast;
use tokio::time::{sleep, timeout};

/// Drena todas as mensagens disponíveis no receiver sem bloquear.
fn drain(rx: &mut broadcast::Receiver<ServerMessage>) -> Vec<ServerMessage> {
    let mut msgs = Vec::new();
    loop {
        match rx.try_recv() {
            Ok(msg) => msgs.push(msg),
            Err(_) => break,
        }
    }
    msgs
}

/// Aguarda até receber uma mensagem que satisfaz o predicado, com timeout.
async fn wait_for<F>(rx: &mut broadcast::Receiver<ServerMessage>, pred: F) -> Option<ServerMessage>
where
    F: Fn(&ServerMessage) -> bool,
{
    let result = timeout(Duration::from_secs(2), async {
        loop {
            match rx.recv().await {
                Ok(msg) => {
                    if pred(&msg) {
                        return Some(msg);
                    }
                }
                Err(broadcast::error::RecvError::Lagged(_)) => continue,
                Err(broadcast::error::RecvError::Closed) => return None,
            }
        }
    })
    .await;

    result.unwrap_or(None)
}

#[tokio::test]
async fn agent_joined_emitted_when_pane_id_appears() {
    let dir = tempfile::tempdir().expect("falha ao criar tempdir");
    let teams_dir = dir.path().to_path_buf();

    let (tx, mut rx) = broadcast::channel::<ServerMessage>(64);

    let watcher = TeamWatcher::new(teams_dir.clone(), tx);
    let handle = watcher.start();

    // Aguarda o watcher inicializar o inotify
    sleep(Duration::from_millis(100)).await;

    // Cria subdiretório da equipe
    let team_dir = teams_dir.join("team-test");
    tokio::fs::create_dir_all(&team_dir)
        .await
        .expect("falha ao criar team dir");

    // Escreve config sem pane_id (string vazia)
    let config_path = team_dir.join("config.json");
    let config_sem_pane = serde_json::json!({
        "name": "team-test",
        "members": [
            {
                "name": "researcher",
                "agentId": "abc",
                "agentType": "general",
                "model": "sonnet",
                "color": "blue",
                "tmuxPaneId": ""
            }
        ]
    });
    tokio::fs::write(&config_path, config_sem_pane.to_string())
        .await
        .expect("falha ao escrever config sem pane");

    // Dá tempo ao inotify processar
    sleep(Duration::from_millis(300)).await;

    // Drena mensagens existentes — não deve haver AgentJoined ainda
    drain(&mut rx);

    // Reescreve config COM pane_id
    let config_com_pane = serde_json::json!({
        "name": "team-test",
        "members": [
            {
                "name": "researcher",
                "agentId": "abc",
                "agentType": "general",
                "model": "sonnet",
                "color": "blue",
                "tmuxPaneId": "%34"
            }
        ]
    });
    tokio::fs::write(&config_path, config_com_pane.to_string())
        .await
        .expect("falha ao reescrever config com pane");

    // Aguarda AgentJoined
    let msg = wait_for(&mut rx, |m| matches!(m, ServerMessage::AgentJoined { .. })).await;

    handle.abort();

    let msg = msg.expect("AgentJoined nao recebido em 2s");
    match msg {
        ServerMessage::AgentJoined { name, pane_id, .. } => {
            assert_eq!(name, "researcher");
            assert_eq!(pane_id, "%34");
        }
        other => panic!("mensagem inesperada: {other:?}"),
    }
}

#[tokio::test]
async fn agent_left_emitted_when_member_removed() {
    let dir = tempfile::tempdir().expect("falha ao criar tempdir");
    let teams_dir = dir.path().to_path_buf();

    let (tx, mut rx) = broadcast::channel::<ServerMessage>(64);

    let watcher = TeamWatcher::new(teams_dir.clone(), tx);
    let handle = watcher.start();

    sleep(Duration::from_millis(100)).await;

    let team_dir = teams_dir.join("team-left");
    tokio::fs::create_dir_all(&team_dir)
        .await
        .expect("falha ao criar team dir");

    let config_path = team_dir.join("config.json");

    // Escreve config com 2 membros, ambos com pane_id
    let config_dois = serde_json::json!({
        "name": "team-left",
        "members": [
            {
                "name": "alpha",
                "agentId": "id-alpha",
                "agentType": "general",
                "model": "sonnet",
                "color": "blue",
                "tmuxPaneId": "%10"
            },
            {
                "name": "beta",
                "agentId": "id-beta",
                "agentType": "general",
                "model": "sonnet",
                "color": "green",
                "tmuxPaneId": "%11"
            }
        ]
    });
    tokio::fs::write(&config_path, config_dois.to_string())
        .await
        .expect("falha ao escrever config com 2 membros");

    sleep(Duration::from_millis(300)).await;

    // Consome os AgentJoined para limpar o canal
    drain(&mut rx);

    // Reescreve config com apenas 1 membro (beta removido)
    let config_um = serde_json::json!({
        "name": "team-left",
        "members": [
            {
                "name": "alpha",
                "agentId": "id-alpha",
                "agentType": "general",
                "model": "sonnet",
                "color": "blue",
                "tmuxPaneId": "%10"
            }
        ]
    });
    tokio::fs::write(&config_path, config_um.to_string())
        .await
        .expect("falha ao reescrever config com 1 membro");

    // Aguarda AgentLeft para "beta"
    let msg = wait_for(
        &mut rx,
        |m| matches!(m, ServerMessage::AgentLeft { name } if name == "beta"),
    )
    .await;

    handle.abort();

    let msg = msg.expect("AgentLeft para beta nao recebido em 2s");
    match msg {
        ServerMessage::AgentLeft { name } => {
            assert_eq!(name, "beta");
        }
        other => panic!("mensagem inesperada: {other:?}"),
    }
}

#[tokio::test]
async fn no_event_when_pane_id_empty() {
    let dir = tempfile::tempdir().expect("falha ao criar tempdir");
    let teams_dir = dir.path().to_path_buf();

    let (tx, mut rx) = broadcast::channel::<ServerMessage>(64);

    let watcher = TeamWatcher::new(teams_dir.clone(), tx);
    let handle = watcher.start();

    sleep(Duration::from_millis(100)).await;

    let team_dir = teams_dir.join("team-nopane");
    tokio::fs::create_dir_all(&team_dir)
        .await
        .expect("falha ao criar team dir");

    let config_path = team_dir.join("config.json");

    // Membro sem tmuxPaneId (string vazia)
    let config_sem = serde_json::json!({
        "name": "team-nopane",
        "members": [
            {
                "name": "ghost",
                "agentId": "id-ghost",
                "agentType": "general",
                "model": "haiku",
                "color": "cyan",
                "tmuxPaneId": ""
            }
        ]
    });
    tokio::fs::write(&config_path, config_sem.to_string())
        .await
        .expect("falha ao escrever config sem pane");

    // Aguarda 1 segundo — nenhum evento deve ser emitido
    sleep(Duration::from_secs(1)).await;

    handle.abort();

    // Não deve ter chegado nenhuma mensagem
    let msgs = drain(&mut rx);
    let joined: Vec<_> = msgs
        .iter()
        .filter(|m| matches!(m, ServerMessage::AgentJoined { .. }))
        .collect();

    assert!(
        joined.is_empty(),
        "AgentJoined nao deveria ser emitido quando pane_id esta vazio, mas recebemos: {joined:?}"
    );
}

#[tokio::test]
async fn watcher_handles_nonexistent_dir() {
    // Diretório que não existe
    let nonexistent = std::path::PathBuf::from("/tmp/ccui-test-nonexistent-xyz-987654");

    // Garantir que de fato não existe
    let _ = tokio::fs::remove_dir_all(&nonexistent).await;

    let (tx, _rx) = broadcast::channel::<ServerMessage>(16);

    let watcher = TeamWatcher::new(nonexistent, tx);
    let handle = watcher.start();

    // Aguarda a task processar (deve retornar imediatamente sem crash)
    sleep(Duration::from_millis(500)).await;

    // A task deve ter terminado sozinha (dir não existe) ou pode ser abortada sem pânico
    handle.abort();

    // Se chegou aqui sem panic, o teste passou
}
