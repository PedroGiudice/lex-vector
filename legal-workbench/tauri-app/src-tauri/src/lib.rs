mod commands;
mod models;

use commands::{filesystem, cache};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            filesystem::list_process_folders,
            filesystem::list_pdfs_in_folder,
            cache::init_cache,
            cache::get_cached_result,
            cache::save_cached_result,
            cache::hash_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
