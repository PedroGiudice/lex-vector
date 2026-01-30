mod commands;
mod models;

use commands::{filesystem, cache};
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![
            filesystem::list_process_folders,
            filesystem::list_pdfs_in_folder,
            cache::init_cache,
            cache::get_cached_result,
            cache::save_cached_result,
            cache::hash_file,
            cache::list_cache_entries,
        ])
        .setup(|app| {
            // Always open DevTools for debugging network issues
            if let Some(window) = app.get_webview_window("main") {
                window.open_devtools();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
