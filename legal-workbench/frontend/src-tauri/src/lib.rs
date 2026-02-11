mod commands;
mod models;

use commands::{filesystem, cache};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let mut builder = tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init());

    #[cfg(all(feature = "mcp-bridge", debug_assertions))]
    {
        builder = builder.plugin(tauri_plugin_mcp_bridge::init());
    }

    builder
        .invoke_handler(tauri::generate_handler![
            filesystem::list_process_folders,
            filesystem::list_pdfs_in_folder,
            cache::init_cache,
            cache::get_cached_result,
            cache::save_cached_result,
            cache::hash_file,
            cache::list_cache_entries,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

