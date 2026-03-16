use clap::{Parser, Subcommand};
use std::path::PathBuf;
use stj_vec_core::config::AppConfig;
use tracing_subscriber::EnvFilter;

use stj_vec_ingest::pipeline::Pipeline;

#[derive(Parser)]
#[command(
    name = "stj-vec-ingest",
    version,
    about = "STJ vector ingestion pipeline"
)]
struct Cli {
    /// Path to config.toml
    #[arg(short, long, default_value = "config.toml")]
    config: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Scan integras dir for new sources
    Scan,
    /// Chunk pending sources
    Chunk,
    /// Generate embeddings (placeholder)
    Embed,
    /// Run full pipeline: scan + chunk + embed
    Full,
    /// Show ingest stats
    Stats,
    /// Reset a source for reprocessing
    Reset {
        /// Source name to reset (e.g. "202203")
        source: String,
    },
    /// Export chunks to JSONL for Modal embedding
    ExportChunks {
        #[arg(short, long, default_value = "/tmp/stj-vec-chunks")]
        output: PathBuf,
        #[arg(short, long)]
        limit: Option<usize>,
    },
    /// Import embeddings from Modal Volume (.npz + .json)
    ImportEmbeddings {
        #[arg(short, long, default_value = "/tmp/stj-vec-embeddings")]
        input: PathBuf,
        #[arg(short, long)]
        limit: Option<usize>,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("stj_vec=info".parse()?))
        .init();

    let cli = Cli::parse();
    let config = AppConfig::load(&cli.config)?;
    let pipeline = Pipeline::new(config)?;

    match cli.command {
        Commands::Scan => {
            let sources = pipeline.scan()?;
            println!("{} sources found", sources.len());
            for s in &sources {
                println!("  {} ({} files)", s.name, s.file_count);
            }
        }
        Commands::Chunk => pipeline.chunk_pending()?,
        Commands::Embed => pipeline.embed_pending()?,
        Commands::Full => {
            pipeline.scan()?;
            pipeline.chunk_pending()?;
            pipeline.embed_pending()?;
        }
        Commands::Stats => {
            let stats = pipeline.stats()?;
            println!("Documents:  {}", stats.document_count);
            println!("Chunks:     {}", stats.chunk_count);
            println!("Embeddings: {}", stats.embedding_count);
            println!(
                "Ingest pending: {} | chunked: {} | done: {}",
                stats.ingest_pending, stats.ingest_chunked, stats.ingest_done
            );
        }
        Commands::Reset { source } => {
            pipeline.reset(&source)?;
            println!("Reset source: {source}");
        }
        Commands::ExportChunks { output, limit } => {
            let (sources, chunks) = stj_vec_ingest::exporter::export_chunks_for_modal(
                pipeline.storage(),
                &output,
                limit,
            )?;
            println!(
                "Exported {chunks} chunks from {sources} sources to {}",
                output.display()
            );
            println!(
                "Upload: modal volume put stj-vec-data {0}/ /chunks/ --force",
                output.display()
            );
        }
        Commands::ImportEmbeddings { input, limit } => {
            let (sources, embeddings) = stj_vec_ingest::importer::import_embeddings_from_modal(
                pipeline.storage(),
                &input,
                limit,
            )?;
            println!("Imported {embeddings} embeddings from {sources} sources");
        }
    }
    Ok(())
}
