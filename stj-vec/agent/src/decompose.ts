import Anthropic from "@anthropic-ai/sdk";
import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const RUST_API = process.env.STJ_SEARCH_URL ?? "http://localhost:8421";
const MODEL = "claude-sonnet-4-6";
const MAX_TOKENS = 8000;
const MAX_ITERATIONS = 15;

// --- Types ---

interface SearchCall {
  query: string;
  filters?: Record<string, string>;
  limit?: number;
}

interface SearchResult {
  doc_id: string;
  processo?: string;
  classe?: string;
  ministro?: string;
  data_publicacao?: string;
  tipo?: string;
  orgao_julgador?: string;
  content?: string;
  scores?: { dense: number; sparse: number; rrf: number };
}

interface CollectedAngle {
  query: string;
  filters?: Record<string, string>;
  results: SearchResult[];
}

// --- Tool Definitions ---

const tools: Anthropic.Tool[] = [
  {
    name: "stj_search",
    description:
      "Busca vetorial hibrida (dense + sparse + RRF) na base de jurisprudencia do STJ.",
    input_schema: {
      type: "object" as const,
      properties: {
        query: { type: "string", description: "Query de busca (5-10 palavras, vocabulario STJ)" },
        limit: { type: "integer", description: "Max resultados (default 10)" },
        filters: {
          type: "object",
          properties: {
            secao: { type: "string" },
            classe: { type: "string" },
            tipo: { type: "string" },
            orgao_julgador: { type: "string" },
            data_julgamento: { type: "string" },
          },
        },
      },
      required: ["query"],
    },
  },
  {
    name: "stj_filters",
    description: "Lista filtros disponiveis na base STJ.",
    input_schema: { type: "object" as const, properties: {} },
  },
  {
    name: "stj_document",
    description: "Busca documento completo por doc_id.",
    input_schema: {
      type: "object" as const,
      properties: {
        doc_id: { type: "string", description: "ID do documento" },
      },
      required: ["doc_id"],
    },
  },
];

// --- Tool Handlers ---

async function executeTool(
  name: string,
  input: Record<string, unknown>,
): Promise<string> {
  switch (name) {
    case "stj_search": {
      const res = await fetch(`${RUST_API}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      if (!res.ok) return JSON.stringify({ error: `HTTP ${res.status}` });
      return JSON.stringify(await res.json());
    }
    case "stj_filters": {
      const res = await fetch(`${RUST_API}/api/filters`);
      if (!res.ok) return JSON.stringify({ error: `HTTP ${res.status}` });
      return JSON.stringify(await res.json());
    }
    case "stj_document": {
      const docId = input.doc_id as string;
      const res = await fetch(
        `${RUST_API}/api/document/${encodeURIComponent(docId)}`,
      );
      if (!res.ok) return JSON.stringify({ error: `HTTP ${res.status}` });
      return JSON.stringify(await res.json());
    }
    default:
      return JSON.stringify({ error: `Tool desconhecida: ${name}` });
  }
}

// --- System Prompt ---

function loadSystemPrompt(): string {
  const promptPath = resolve(__dirname, "../prompts/decomposer.md");
  try {
    return readFileSync(promptPath, "utf-8");
  } catch {
    return "Voce e um decompositor de queries juridicas. Use stj_search para buscar. Nao gere output final.";
  }
}

// --- Result Collection ---

function buildOutput(
  originalQuery: string,
  angles: CollectedAngle[],
  meta: Record<string, unknown>,
): Record<string, unknown> {
  // Deduplicate results by doc_id, keeping the highest RRF score
  const seen = new Map<string, { result: SearchResult; foundVia: string }>();

  for (const angle of angles) {
    for (const r of angle.results) {
      if (!r.doc_id) continue;
      const existing = seen.get(r.doc_id);
      const rrf = r.scores?.rrf ?? 0;
      if (!existing || rrf > (existing.result.scores?.rrf ?? 0)) {
        seen.set(r.doc_id, { result: r, foundVia: angle.query });
      }
    }
  }

  const deduped = Array.from(seen.values())
    .sort((a, b) => (b.result.scores?.rrf ?? 0) - (a.result.scores?.rrf ?? 0))
    .slice(0, 50);

  return {
    original_query: originalQuery,
    decomposition: {
      intent: "exploratoria",
      angles: angles.map((a) => ({
        query: a.query,
        angle: a.query, // query IS the angle description in this mode
        results_count: a.results.length,
        filters: a.filters,
      })),
      rounds: meta.iterations,
    },
    results: deduped.map(({ result, foundVia }) => ({
      doc_id: result.doc_id,
      processo: result.processo ?? null,
      classe: result.classe ?? null,
      ministro: result.ministro ?? null,
      data_publicacao: result.data_publicacao ?? null,
      tipo: result.tipo ?? null,
      orgao_julgador: result.orgao_julgador ?? null,
      content_preview: (result.content ?? "").substring(0, 300),
      scores: result.scores ?? { dense: 0, sparse: 0, rrf: 0 },
      found_via: foundVia,
    })),
    total_results: deduped.length,
    total_searches: angles.length,
    _meta: meta,
  };
}

// --- Main ---

async function main() {
  const query = process.argv[2];
  if (!query) {
    process.stderr.write("Uso: bun run src/decompose.ts <query>\n");
    process.exit(1);
  }

  const client = new Anthropic();
  const startTime = Date.now();
  let totalInput = 0;
  let totalOutput = 0;
  let toolCalls = 0;
  const collectedAngles: CollectedAngle[] = [];

  // Map tool_use_id -> search input for correlating results
  const pendingSearches = new Map<string, SearchCall>();

  const messages: Anthropic.MessageParam[] = [
    { role: "user", content: query },
  ];

  const systemPrompt = loadSystemPrompt();

  for (let iteration = 1; iteration <= MAX_ITERATIONS; iteration++) {
    const response = await client.messages.create({
      model: MODEL,
      max_tokens: MAX_TOKENS,
      tools,
      system: systemPrompt,
      messages,
    });

    totalInput += response.usage.input_tokens;
    totalOutput += response.usage.output_tokens;

    // end_turn: model is done searching. Build output from collected data.
    if (response.stop_reason === "end_turn") {
      const elapsed = (Date.now() - startTime) / 1000;
      const output = buildOutput(query, collectedAngles, {
        elapsed_seconds: elapsed,
        input_tokens: totalInput,
        output_tokens: totalOutput,
        tool_calls: toolCalls,
        iterations: iteration,
        model: MODEL,
        runner: "sdk-ts-v2",
      });
      console.log(JSON.stringify(output));
      return;
    }

    // Process tool_use blocks
    const toolUseBlocks = response.content.filter(
      (b): b is Anthropic.ToolUseBlock => b.type === "tool_use",
    );

    if (toolUseBlocks.length === 0) {
      console.log(
        JSON.stringify({
          error: "Unexpected stop_reason",
          stop_reason: response.stop_reason,
        }),
      );
      return;
    }

    messages.push({ role: "assistant", content: response.content });

    // Execute tools, collect search inputs/results
    const toolResults: Anthropic.ToolResultBlockParam[] = [];

    for (const block of toolUseBlocks) {
      toolCalls++;
      const input = block.input as Record<string, unknown>;
      const resultStr = await executeTool(block.name, input);

      // Track search calls for result collection
      if (block.name === "stj_search") {
        pendingSearches.set(block.id, {
          query: (input.query as string) ?? "",
          filters: input.filters as Record<string, string> | undefined,
          limit: input.limit as number | undefined,
        });

        // Parse and collect results
        try {
          const parsed = JSON.parse(resultStr);
          const results: SearchResult[] = parsed.results ?? [];
          const searchCall = pendingSearches.get(block.id)!;
          collectedAngles.push({
            query: searchCall.query,
            filters: searchCall.filters,
            results,
          });
        } catch {
          // Failed to parse -- skip collection, tool result still sent to model
        }
      }

      toolResults.push({
        type: "tool_result",
        tool_use_id: block.id,
        content: resultStr,
      });
    }

    messages.push({ role: "user", content: toolResults });
  }

  // Max iterations
  const output = buildOutput(query, collectedAngles, {
    elapsed_seconds: (Date.now() - startTime) / 1000,
    input_tokens: totalInput,
    output_tokens: totalOutput,
    tool_calls: toolCalls,
    iterations: MAX_ITERATIONS,
    model: MODEL,
    runner: "sdk-ts-v2",
    warning: "max_iterations_reached",
  });
  console.log(JSON.stringify(output));
}

main().catch((err) => {
  console.error(
    JSON.stringify({ error: err.message, type: err.constructor.name }),
  );
  process.exit(1);
});
