import Anthropic from "@anthropic-ai/sdk";
import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const RUST_API = process.env.STJ_SEARCH_URL ?? "http://localhost:8421";
const MODEL = "claude-sonnet-4-6";
const MAX_TOKENS = 16000;
const MAX_ITERATIONS = 15;

// --- Tool Definitions ---

const tools: Anthropic.Tool[] = [
  {
    name: "stj_search",
    description:
      "Busca vetorial hibrida (dense + sparse + RRF) na base de jurisprudencia do STJ.",
    input_schema: {
      type: "object" as const,
      properties: {
        query: { type: "string", description: "Query de busca" },
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
      if (!res.ok)
        return JSON.stringify({ error: `HTTP ${res.status}` });
      return JSON.stringify(await res.json());
    }
    case "stj_filters": {
      const res = await fetch(`${RUST_API}/api/filters`);
      if (!res.ok)
        return JSON.stringify({ error: `HTTP ${res.status}` });
      return JSON.stringify(await res.json());
    }
    case "stj_document": {
      const docId = input.doc_id as string;
      const res = await fetch(
        `${RUST_API}/api/document/${encodeURIComponent(docId)}`,
      );
      if (!res.ok)
        return JSON.stringify({ error: `HTTP ${res.status}` });
      return JSON.stringify(await res.json());
    }
    default:
      return JSON.stringify({ error: `Tool desconhecida: ${name}` });
  }
}

// --- System Prompt ---

function loadSystemPrompt(): string {
  const agentPath = resolve(
    __dirname,
    "../../..",
    ".claude/agents/query-decomposer.md",
  );
  try {
    const content = readFileSync(agentPath, "utf-8");
    const match = content.match(/^---[\s\S]*?---\n([\s\S]*)$/);
    return match ? match[1].trim() : content;
  } catch {
    return "Voce e um decompositor de queries juridicas para busca no STJ. Retorne JSON puro.";
  }
}

// --- Output ---

function stripCodeFences(text: string): string {
  return text.replace(/^```(?:json)?\s*\n?/i, "").replace(/\n?```\s*$/i, "").trim();
}

function tryParseJson(text: string): Record<string, unknown> | null {
  const cleaned = stripCodeFences(text);
  try {
    return JSON.parse(cleaned);
  } catch {
    return null;
  }
}

function emitResult(
  data: Record<string, unknown>,
  meta: Record<string, unknown>,
): void {
  const output = { ...data, _meta: meta };
  console.log(JSON.stringify(output));
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

  const messages: Anthropic.MessageParam[] = [
    { role: "user", content: query },
  ];

  const systemPrompt = loadSystemPrompt();

  // --- Agentic loop: tools ---
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

    if (response.stop_reason === "end_turn") {
      const text = response.content
        .filter((b): b is Anthropic.TextBlock => b.type === "text")
        .map((b) => b.text)
        .join("");

      const elapsed = (Date.now() - startTime) / 1000;
      const meta = {
        elapsed_seconds: elapsed,
        input_tokens: totalInput,
        output_tokens: totalOutput,
        tool_calls: toolCalls,
        iterations: iteration,
        model: MODEL,
        runner: "sdk-ts",
      };

      // Try parsing as JSON
      const parsed = tryParseJson(text);
      if (parsed) {
        emitResult(parsed, meta);
        return;
      } else {
        // Not JSON -- model ignored the instruction.
        // Append text as assistant, then do a structured output call.
        messages.push({ role: "assistant", content: response.content });
        messages.push({
          role: "user",
          content:
            "Voce gerou texto narrativo. Releia o system prompt: sua saida DEVE ser JSON puro no schema especificado. Consolide todos os resultados das buscas que voce fez e retorne APENAS o JSON.",
        });

        const fixup = await client.messages.create({
          model: MODEL,
          max_tokens: MAX_TOKENS,
          system: systemPrompt,
          messages,
        });

        totalInput += fixup.usage.input_tokens;
        totalOutput += fixup.usage.output_tokens;
        meta.elapsed_seconds = (Date.now() - startTime) / 1000;
        meta.input_tokens = totalInput;
        meta.output_tokens = totalOutput;
        meta.iterations = iteration + 1;

        const fixupText = fixup.content
          .filter((b): b is Anthropic.TextBlock => b.type === "text")
          .map((b) => b.text)
          .join("");

        const fixupParsed = tryParseJson(fixupText);
        if (fixupParsed) {
          emitResult(fixupParsed, meta);
        } else {
          emitResult(
            { error: "Model did not return valid JSON after retry", raw_output: fixupText.substring(0, 2000) },
            meta,
          );
        }
        return;
      }
    }

    // Process tool_use
    const toolUseBlocks = response.content.filter(
      (b): b is Anthropic.ToolUseBlock => b.type === "tool_use",
    );

    if (toolUseBlocks.length === 0) {
      emitResult(
        { error: "Unexpected stop_reason", stop_reason: response.stop_reason },
        { elapsed_seconds: (Date.now() - startTime) / 1000, tool_calls: toolCalls },
      );
      return;
    }

    messages.push({ role: "assistant", content: response.content });

    const toolResults: Anthropic.ToolResultBlockParam[] = [];
    for (const block of toolUseBlocks) {
      toolCalls++;
      const result = await executeTool(
        block.name,
        block.input as Record<string, unknown>,
      );
      toolResults.push({
        type: "tool_result",
        tool_use_id: block.id,
        content: result,
      });
    }

    messages.push({ role: "user", content: toolResults });
  }

  emitResult(
    { error: `Max iterations (${MAX_ITERATIONS}) reached` },
    {
      elapsed_seconds: (Date.now() - startTime) / 1000,
      input_tokens: totalInput,
      output_tokens: totalOutput,
      tool_calls: toolCalls,
    },
  );
}

main().catch((err) => {
  console.error(
    JSON.stringify({ error: err.message, type: err.constructor.name }),
  );
  process.exit(1);
});
