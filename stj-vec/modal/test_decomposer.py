#!/usr/bin/env python3
"""Client para o decompositor DEPLOYED no Modal.

O server faz tudo: inference + buscas + consolidacao de resultados.
Este client dispara e mostra progresso + resultados finais.

Prerequisito:
    modal deploy modal/serve_decomposer.py

Uso:
    python3 modal/test_decomposer.py "inaplicabilidade CDC software"
    python3 modal/test_decomposer.py "dano moral bancario inscricao indevida"
"""

import json
import sys
import time
from pathlib import Path

import modal

APP_NAME = "stj-decomposer"
DECOMPOSER_PROMPT_PATH = Path(__file__).parent.parent / "agent" / "prompts" / "decomposer.md"


def load_system_prompt() -> str:
    if DECOMPOSER_PROMPT_PATH.exists():
        return DECOMPOSER_PROMPT_PATH.read_text()
    return ""


def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "inaplicabilidade CDC contrato licenciamento software entre empresas"
    system_prompt = load_system_prompt()

    print(f"Query: {query}")
    print(f"System prompt: {'decomposer.md' if system_prompt else 'inline'} ({len(system_prompt)} chars)")
    print("Connecting to deployed app...", flush=True)

    t0 = time.time()

    ServiceCls = modal.Cls.from_name(APP_NAME, "DecomposerService")
    service = ServiceCls()

    final_result = None

    for msg in service.decompose.remote_gen(query, system_prompt or ""):
        if msg["type"] == "round":
            tc = msg.get("tool_calls", [])
            print(f"\n--- Round {msg['round']} ---")
            print(f"  Inference: {msg['inference_time']}s | Search: {msg.get('search_time', 0)}s")
            print(f"  Tokens: {msg['usage'].get('prompt_tokens', 0)} in / {msg['usage'].get('completion_tokens', 0)} out")
            print(f"  Tool calls: {len(tc)} | Results this round: {msg.get('search_results_count', 0)} | Unique docs total: {msg.get('unique_docs_so_far', 0)}")

            content = msg.get("content", "")
            if content and "<think>" in content:
                think_start = content.find("<think>") + len("<think>")
                think_end = content.find("</think>")
                if think_end > think_start:
                    thinking = content[think_start:think_end].strip()
                    print(f"  [Thinking] {thinking[:200]}...")

            for i, t in enumerate(tc, 1):
                print(f"    {i:2d}. {t['arguments'].get('query', '')}")

        elif msg["type"] == "done":
            final_result = msg

    total_time = time.time() - t0

    if not final_result:
        print("\nERRO: nenhum resultado final recebido")
        return

    # --- Resultado final ---
    decomp = final_result["decomposition"]
    usage = final_result["usage"]
    results = final_result["results"]

    print(f"\n{'=' * 70}")
    print(f"RESULTADOS")
    print(f"{'=' * 70}")
    print(f"Tempo total: {total_time:.1f}s | Inferencia: {usage['inference_time']}s")
    print(f"Tokens: {usage['prompt_tokens']} in / {usage['completion_tokens']} out")
    print(f"Rounds: {decomp['rounds']} | Queries: {decomp['total_tool_calls']} | Docs unicos: {final_result['total_unique_docs']} | Top resultados: {final_result['total_results']}")
    print(f"Model: {final_result['model']}")
    print()

    for i, r in enumerate(results, 1):
        doc_id = r.get("doc_id", "?")
        processo = r.get("processo", "")
        classe = r.get("classe", "")
        tipo = r.get("tipo", "")
        rrf = r.get("rrf_score", 0)
        preview = r.get("content_preview", "")[:120]
        found_via = r.get("found_via", "")

        print(f"  {i:2d}. [{rrf:.4f}] {processo or doc_id}")
        if classe or tipo:
            print(f"      {classe} | {tipo}")
        if preview:
            print(f"      {preview}...")
        print(f"      via: {found_via}")
        print()

    # Dump
    debug_path = Path("/tmp/decomposer_last_response.json")
    debug_path.write_text(json.dumps(final_result, indent=2, ensure_ascii=False))
    print(f"Response completa: {debug_path}")


if __name__ == "__main__":
    main()
