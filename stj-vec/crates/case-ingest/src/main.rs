mod file_index;
mod ingestor;

use clap::{Parser, Subcommand};

use ingestor::Ingestor;
use stj_vec_core::embedder::OllamaEmbedder;

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
        Commands::Init => {
            let work_dir = std::env::current_dir()?;
            let ing = Ingestor::create(&work_dir)?;
            let embedder = OllamaEmbedder::new(
                "http://100.114.203.28:11434/api/embeddings",
                "bge-m3",
                1024,
                30,
            );
            let (docs, chunks) = ing.init(&embedder).await?;
            println!("Inicializado: {docs} documentos, {chunks} chunks embedados");
        }
        Commands::Sync => todo!("Task 4"),
        Commands::Watch => todo!("Task 5"),
        Commands::Stats => {
            let work_dir = std::env::current_dir()?;
            let ing = Ingestor::open(&work_dir)?;
            let stats = ing.storage.stats()?;
            println!("Documentos:  {}", stats.document_count);
            println!("Chunks:      {}", stats.chunk_count);
            println!("Embeddings:  {}", stats.embedding_count);
        }
        Commands::Search {
            query: _,
            limit: _,
        } => todo!("Task 6"),
    }
    Ok(())
}
