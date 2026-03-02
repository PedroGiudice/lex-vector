use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::sync::Mutex;
use tauri_plugin_shell::process::CommandChild;

#[derive(Debug, Serialize, Deserialize)]
pub struct AppConfig {
    pub vm_host: String,
    pub local_port: u16,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            vm_host: "217.76.48.35".into(),
            local_port: 8005,
        }
    }
}

struct TunnelState(Mutex<Option<CommandChild>>);

fn ccui_dir() -> Result<PathBuf, String> {
    let home = dirs::home_dir().ok_or("home directory nao encontrado")?;
    let dir = home.join(".ccui");
    std::fs::create_dir_all(&dir).map_err(|e| format!("falha ao criar ~/.ccui: {e}"))?;
    Ok(dir)
}

#[tauri::command]
fn get_config() -> AppConfig {
    AppConfig::default()
}

#[tauri::command]
async fn check_health() -> Result<bool, String> {
    let config = AppConfig::default();
    let url = format!("http://localhost:{}/health", config.local_port);
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()
        .map_err(|e| format!("falha ao criar client HTTP: {e}"))?;
    match client.get(&url).send().await {
        Ok(resp) => Ok(resp.status().is_success()),
        Err(_) => Ok(false),
    }
}

#[tauri::command]
async fn generate_keypair() -> Result<String, String> {
    use ssh_key::{Algorithm, PrivateKey};

    let dir = ccui_dir()?;
    let priv_path = dir.join("id_ed25519");
    let pub_path = dir.join("id_ed25519.pub");

    let private_key = PrivateKey::random(&mut rand_core::OsRng, Algorithm::Ed25519)
        .map_err(|e| format!("falha ao gerar keypair ED25519: {e}"))?;

    let openssh_priv = private_key
        .to_openssh(ssh_key::LineEnding::LF)
        .map_err(|e| format!("falha ao serializar chave privada: {e}"))?;

    let public_key = private_key.public_key();
    let openssh_pub = public_key
        .to_openssh()
        .map_err(|e| format!("falha ao serializar chave publica: {e}"))?;

    std::fs::write(&priv_path, openssh_priv.as_bytes())
        .map_err(|e| format!("falha ao salvar chave privada em {}: {e}", priv_path.display()))?;

    // Permissoes 600 na chave privada (Unix)
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&priv_path, std::fs::Permissions::from_mode(0o600))
            .map_err(|e| format!("falha ao definir permissoes da chave privada: {e}"))?;
    }

    std::fs::write(&pub_path, openssh_pub.as_bytes())
        .map_err(|e| format!("falha ao salvar chave publica em {}: {e}", pub_path.display()))?;

    Ok(openssh_pub)
}

#[tauri::command]
async fn check_keypair_exists() -> bool {
    if let Ok(dir) = ccui_dir() {
        dir.join("id_ed25519").exists() && dir.join("id_ed25519.pub").exists()
    } else {
        false
    }
}

#[tauri::command]
async fn open_tunnel(
    app: tauri::AppHandle,
    state: tauri::State<'_, TunnelState>,
    host: String,
) -> Result<(), String> {
    use tauri_plugin_shell::ShellExt;

    let dir = ccui_dir()?;
    let key_path = dir.join("id_ed25519");

    if !key_path.exists() {
        return Err("chave ED25519 nao encontrada em ~/.ccui/id_ed25519. Execute generate_keypair primeiro.".into());
    }

    let key_str = key_path.to_string_lossy().to_string();
    let config = AppConfig::default();

    // Matar tunnel anterior se existir
    if let Some(old_child) = state.0.lock().unwrap().take() {
        let _ = old_child.kill();
    }

    let (_rx, child) = app
        .shell()
        .command("ssh")
        .args([
            "-N",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "-L", &format!("{}:localhost:{}", config.local_port, config.local_port),
            "-i", &key_str,
            &format!("opc@{host}"),
        ])
        .spawn()
        .map_err(|e| format!("falha ao abrir tunnel SSH: {e}"))?;

    *state.0.lock().unwrap() = Some(child);

    Ok(())
}

#[tauri::command]
async fn close_tunnel(state: tauri::State<'_, TunnelState>) -> Result<(), String> {
    if let Some(child) = state.0.lock().unwrap().take() {
        child.kill().map_err(|e| format!("falha ao fechar tunnel: {e}"))?;
    }
    Ok(())
}

#[tauri::command]
async fn check_tunnel() -> Result<bool, String> {
    check_health().await
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_opener::init())
        .manage(TunnelState(Mutex::new(None)));

    builder = builder.plugin(tauri_plugin_mcp_bridge::init());

    builder
        .invoke_handler(tauri::generate_handler![
            get_config,
            check_health,
            generate_keypair,
            check_keypair_exists,
            open_tunnel,
            close_tunnel,
            check_tunnel,
        ])
        .run(tauri::generate_context!())
        .expect("erro ao iniciar ccui-app");
}
