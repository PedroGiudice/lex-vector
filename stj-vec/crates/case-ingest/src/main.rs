mod file_index;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "case-ingest", about = "Ingestao de documentos por caso juridico")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Cria knowledge.db e indexa tudo em base/
    Init,
    /// Sync delta desde ultimo sync
    Sync,
    /// Monitora base/ por mudancas
    Watch,
    /// Mostra estatisticas do knowledge.db
    Stats,
    /// Busca vetorial no knowledge.db
    Search {
        query: String,
        #[arg(short, long, default_value = "5")]
        limit: usize,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Init => todo!("Task 3"),
        Commands::Sync => todo!("Task 4"),
        Commands::Watch => todo!("Task 5"),
        Commands::Stats => todo!("Task 3"),
        Commands::Search {
            query: _,
            limit: _,
        } => todo!("Task 6"),
    }
}
