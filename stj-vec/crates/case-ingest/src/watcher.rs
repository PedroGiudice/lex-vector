use std::path::Path;
use std::sync::mpsc;
use std::time::Duration;

use anyhow::Result;
use notify::{EventKind, RecursiveMode, Watcher};

/// Monitors `base_dir` for file changes, calling `on_change` on each event.
///
/// Blocks indefinitely. Debounces events by 2 seconds.
pub fn watch_base(base_dir: &Path, mut on_change: impl FnMut()) -> Result<()> {
    let (tx, rx) = mpsc::channel();

    let mut watcher =
        notify::recommended_watcher(move |res: Result<notify::Event, notify::Error>| {
            if let Ok(event) = res {
                match event.kind {
                    EventKind::Create(_) | EventKind::Modify(_) | EventKind::Remove(_) => {
                        let _ = tx.send(());
                    }
                    _ => {}
                }
            }
        })?;

    watcher.watch(base_dir, RecursiveMode::NonRecursive)?;
    eprintln!("[watch] Monitorando {} ...", base_dir.display());

    while let Ok(()) = rx.recv() {
        // Debounce: drain pending events for 2s
        while rx.recv_timeout(Duration::from_secs(2)).is_ok() {}
        on_change();
    }
    Ok(())
}
