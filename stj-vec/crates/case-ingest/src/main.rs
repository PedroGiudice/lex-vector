mod file_index;
mod ingestor;
mod watcher;

use clap::{Parser, Subcommand};

use ingestor::Ingestor;
use stj_vec_core::embedder::{Embedder, TeiEmbedder};

#[derive(Parser)]
#[command(name = "case-ingest", about = "Ingestao de documentos por caso juridico")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Cria knowledge.db e indexa tudo em base/
    Init {
        /// Forcar embedding via TEI local (CPU)
        #[arg(long)]
        cpu: bool,
        /// Forcar export para Modal GPU
        #[arg(long)]
        gpu: bool,
    },
    /// Sync delta desde ultimo sync
    Sync {
        /// Forcar embedding via TEI local (CPU)
        #[arg(long)]
        cpu: bool,
        /// Forcar export para Modal GPU
        #[arg(long)]
        gpu: bool,
    },
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
        Commands::Init { cpu, gpu } => {
            let work_dir = std::env::current_dir()?;
            let ing = Ingestor::create(&work_dir)?;
            let embedder = TeiEmbedder::default_local();
            let (docs, chunks) = ing.init_with_strategy(&embedder, cpu, gpu).await?;
            Ingestor::generate_claude_config(&work_dir)?;
            println!("Inicializado: {docs} documentos, {chunks} chunks");
        }
        Commands::Sync { cpu, gpu } => {
            let work_dir = std::env::current_dir()?;
            let ing = Ingestor::open(&work_dir)?;
            let embedder = TeiEmbedder::default_local();
            let (new, modified, removed) = ing.sync_with_strategy(&embedder, cpu, gpu).await?;
            println!("Sync: {new} novos, {modified} modificados, {removed} removidos");
        }
        Commands::Watch => {
            let work_dir = std::env::current_dir()?;
            let base_dir = work_dir.join("base");
            anyhow::ensure!(base_dir.is_dir(), "base/ nao encontrado");

            eprintln!("[watch] Modo watch. Ctrl+C para parar.");
            watcher::watch_base(&base_dir, || {
                let rt = tokio::runtime::Runtime::new().expect("falha ao criar tokio runtime");
                rt.block_on(async {
                    match Ingestor::open(&work_dir) {
                        Ok(ing) => {
                            let embedder = TeiEmbedder::default_local();
                            match ing.sync_with_strategy(&embedder, true, false).await {
                                Ok((n, m, r)) => eprintln!(
                                    "[watch] Sync: {n} novos, {m} modificados, {r} removidos"
                                ),
                                Err(e) => eprintln!("[watch] Erro no sync: {e}"),
                            }
                        }
                        Err(e) => eprintln!("[watch] Erro ao abrir ingestor: {e}"),
                    }
                });
            })?;
        }
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
            let embedder = TeiEmbedder::default_local();
            let query_vec = embedder.embed(&query).await?;
            let filters = stj_vec_core::types::SearchFilters::default();
            let results = ing.storage.hybrid_search(&query_vec, &query, limit, 0.3, &filters)?;
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
