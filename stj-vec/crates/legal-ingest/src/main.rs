use std::path::PathBuf;

use anyhow::Result;
use clap::{Parser, Subcommand};
use tracing::info;

use legal_vec_ingest::config::LegalConfig;
use legal_vec_ingest::pipeline::Pipeline;

#[derive(Parser)]
#[command(name = "legal-vec-ingest", version, about = "Legal corpus vector ingestion")]
struct Cli {
    /// Caminho para arquivo de configuracao
    #[arg(short, long, default_value = "legal-vec.toml")]
    config: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Lista fontes detectadas no corpus
    Scan,
    /// Chunka todas as fontes pendentes
    Chunk,
    /// Gera embeddings para chunks pendentes
    Embed,
    /// Executa pipeline completo: scan + chunk + embed
    Full,
    /// Mostra estatisticas do banco
    Stats,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "legal_vec=info,legal_vec_ingest=info".into()),
        )
        .init();

    let cli = Cli::parse();
    let config = LegalConfig::load(&cli.config)?;
    let pipeline = Pipeline::new(config)?;

    match cli.command {
        Commands::Scan => {
            let sources = pipeline.scan()?;
            println!("Fontes detectadas: {}", sources.len());
            for s in &sources {
                println!(
                    "  {} ({:?}) - {} docs, {} files",
                    s.name,
                    s.source_type,
                    s.doc_count,
                    s.files.len()
                );
            }
        }
        Commands::Chunk => {
            pipeline.chunk_all()?;
            info!("chunking completo");
        }
        Commands::Embed => {
            pipeline.embed_pending().await?;
            info!("embedding completo");
        }
        Commands::Full => {
            info!("pipeline completo: scan -> chunk -> embed");
            pipeline.chunk_all()?;
            pipeline.embed_pending().await?;
            let stats = pipeline.stats()?;
            println!("Pipeline completo:");
            println!("  Documentos: {}", stats.document_count);
            println!("  Chunks: {}", stats.chunk_count);
            println!("  Embeddings: {}", stats.embedding_count);
        }
        Commands::Stats => {
            let stats = pipeline.stats()?;
            println!("=== Estatisticas ===");
            println!("Documentos: {}", stats.document_count);
            println!("Chunks:     {}", stats.chunk_count);
            println!("Embeddings: {}", stats.embedding_count);
            if !stats.sources.is_empty() {
                println!("\nFontes:");
                for s in &stats.sources {
                    println!(
                        "  {} [{}] - {} docs, {} chunks",
                        s.source, s.status, s.doc_count, s.chunk_count
                    );
                }
            }
        }
    }

    Ok(())
}
