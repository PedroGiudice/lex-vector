mod file_index;
mod ingestor;

use clap::{Parser, Subcommand};

use ingestor::Ingestor;
use stj_vec_core::embedder::{Embedder, OllamaEmbedder};

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
        Commands::Sync => {
            let work_dir = std::env::current_dir()?;
            let ing = Ingestor::open(&work_dir)?;
            let embedder = OllamaEmbedder::new(
                "http://100.114.203.28:11434/api/embeddings",
                "bge-m3",
                1024,
                30,
            );
            let (new, modified, removed) = ing.sync(&embedder).await?;
            println!("Sync: {new} novos, {modified} modificados, {removed} removidos");
        }
        Commands::Watch => todo!("Task 5"),
        Commands::Stats => {
            let work_dir = std::env::current_dir()?;
            let ing = Ingestor::open(&work_dir)?;
            let stats = ing.storage.stats()?;
            println!("Documentos:  {}", stats.document_count);
            println!("Chunks:      {}", stats.chunk_count);
            println!("Embeddings:  {}", stats.embedding_count);
        }
        Commands::Search { query, limit } => {
            let work_dir = std::env::current_dir()?;
            let ing = Ingestor::open(&work_dir)?;
            let embedder = OllamaEmbedder::new(
                "http://100.114.203.28:11434/api/embeddings",
                "bge-m3",
                1024,
                30,
            );
            let query_vec = embedder.embed(&query).await?;
            let filters = stj_vec_core::types::SearchFilters::default();
            let results = ing.storage.search(&query_vec, limit, 0.3, &filters)?;
            if results.is_empty() {
                println!("Nenhum resultado encontrado.");
            } else {
                for (i, r) in results.iter().enumerate() {
                    println!("--- Resultado {} (score: {:.3}) ---", i + 1, r.score);
                    if let Some(ref src) = r.document.source_file {
                        println!("Arquivo: {src}");
                    }
                    let preview: String = r.chunk.content.chars().take(300).collect();
                    println!("{preview}\n");
                }
            }
        }
    }
    Ok(())
}
