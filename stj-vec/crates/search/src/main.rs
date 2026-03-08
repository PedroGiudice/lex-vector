use clap::Parser;
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "stj-vec-search", about = "Busca hibrida STJ")]
struct Cli {
    #[arg(long, default_value = "search-config.toml")]
    config: PathBuf,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    let cli = Cli::parse();
    let config_str = std::fs::read_to_string(&cli.config)?;
    let config: stj_vec_search::config::SearchConfig = toml::from_str(&config_str)?;
    tracing::info!("Config loaded from {:?}", cli.config);
    tracing::info!("Server would start on port {}", config.server.port);
    Ok(())
}
