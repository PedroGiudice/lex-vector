#!/usr/bin/env python3
"""Qwen2.5-72B-Instruct-AWQ decompositor de queries juridicas via vLLM HTTP no Modal.

72B real com 128K contexto, Hermes tool calling nativo, ~86% BFCL.
AWQ-Int4 = ~37GB VRAM weights, sobra bastante pra KV cache na H200.
Agentic loop completo no server: modelo gera tool calls, server executa buscas
na API Rust (via IP publico), devolve resultados pro modelo, repete.

Workflow:
    1. Deploy:  modal deploy modal/serve_decomposer.py
    2. Client:  python3 modal/test_decomposer.py "inaplicabilidade CDC software"

GPU: H200 (141GB). AWQ-Int4 ~37GB weights + ~100GB KV cache.
vLLM >= 0.15 necessario pra H200 (fix de CUDA graphs no kernel AWQ-Marlin).
"""

import json
import socket
import subprocess
import time

import modal

APP_NAME = "stj-decomposer"
app = modal.App(
    APP_NAME,
    tags={"project": "stj-vec", "model": "qwen2.5-72b-instruct-awq", "precision": "awq-int4"},
)

GPU_TYPE = "H200"
MINUTES = 60
VLLM_PORT = 8000
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct-AWQ"
MAX_ROUNDS = 2  # round 1 = decomposicao inicial, round 2 = refinamento. Rounds 3+ geram duplicatas.
STJ_API = "http://217.76.48.35:8421"

decomposer_image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12"
    )
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.16.0",
        "huggingface-hub==0.36.0",
        "requests",
    )
    .env({
        "HF_XET_HIGH_PERFORMANCE": "1",
        "VLLM_SERVER_DEV_MODE": "1",
        "TORCHINDUCTOR_COMPILE_THREADS": "1",
        "NCCL_DEBUG": "ERROR",
        "TORCH_NCCL_ENABLE_MONITORING": "0",
        "TORCH_CPP_LOG_LEVEL": "FATAL",
    })
)

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

with decomposer_image.imports():
    import requests as _requests


# --- vLLM lifecycle helpers ---

def _wait_ready(proc: subprocess.Popen, timeout: int = 20 * MINUTES) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            socket.create_connection(("localhost", VLLM_PORT), timeout=1).close()
            return
        except OSError:
            if proc.poll() is not None:
                raise RuntimeError(f"vLLM exited with {proc.returncode}")
            time.sleep(1)
    raise TimeoutError(f"vLLM not ready within {timeout}s")


def _warmup() -> None:
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 16,
    }
    for _ in range(3):
        _requests.post(
            f"http://localhost:{VLLM_PORT}/v1/chat/completions",
            json=payload, timeout=300,
        ).raise_for_status()


def _sleep(level: int = 1) -> None:
    _requests.post(f"http://localhost:{VLLM_PORT}/sleep?level={level}").raise_for_status()


def _wake_up() -> None:
    _requests.post(f"http://localhost:{VLLM_PORT}/wake_up").raise_for_status()


# --- Tool execution (against STJ API via public IP) ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "stj_search",
            "description": "Busca vetorial hibrida (dense + sparse + RRF) na base de jurisprudencia do STJ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query de busca (5-10 palavras, vocabulario juridico brasileiro)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Numero maximo de resultados (default 10)",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def _execute_search(query: str, limit: int = 10) -> tuple[dict, list]:
    """Executa busca na API Rust via IP publico.

    Returns:
        (summary_for_model, full_results): summary truncado pro modelo, resultados completos pra consolidacao.
    """
    payload = {
        "query": query,
        "limit": limit,
        "filters": {"tipo": "ACORDAO"},
    }
    try:
        resp = _requests.post(f"{STJ_API}/api/search", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        # Resumo pro modelo (cabe no contexto)
        summary = {
            "total": len(results),
            "results": [
                {
                    "doc_id": r.get("doc_id", ""),
                    "processo": r.get("processo", ""),
                    "classe": r.get("classe", ""),
                    "tipo": r.get("tipo", ""),
                    "content_preview": (r.get("content", "") or "")[:150],
                    "rrf_score": r.get("scores", {}).get("rrf", 0),
                }
                for r in results[:5]
            ],
        }
        # Resultados completos pra consolidacao
        full = [
            {
                "doc_id": r.get("doc_id", ""),
                "processo": r.get("processo", ""),
                "classe": r.get("classe", ""),
                "ministro": r.get("ministro", ""),
                "data_publicacao": r.get("data_publicacao", ""),
                "tipo": r.get("tipo", ""),
                "orgao_julgador": r.get("orgao_julgador", ""),
                "content_preview": (r.get("content", "") or "")[:300],
                "scores": r.get("scores", {}),
            }
            for r in results
        ]
        return summary, full
    except Exception as e:
        return {"error": str(e), "results": [], "total": 0}, []


def _execute_tool_calls(tool_calls: list) -> tuple[list[dict], list[dict]]:
    """Executa tool calls.

    Returns:
        (tool_result_messages, full_results_with_query): messages pro modelo, resultados completos com query de origem.
    """
    tool_msgs = []
    full_collected = []
    for tc in tool_calls:
        fn = tc["function"]
        args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]

        if fn["name"] == "stj_search":
            search_query = args.get("query", "")
            summary, full = _execute_search(
                query=search_query,
                limit=args.get("limit", 10),
            )
            tool_msgs.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(summary),
            })
            for r in full:
                r["_found_via"] = search_query
            full_collected.extend(full)
        else:
            tool_msgs.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps({"error": f"Unknown tool: {fn['name']}"}),
            })
    return tool_msgs, full_collected


# --- Service ---

@app.cls(
    image=decomposer_image,
    gpu=GPU_TYPE,
    memory=32768,
    timeout=30 * MINUTES,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
    secrets=[modal.Secret.from_name("huggingface-secret")],
    enable_memory_snapshot=True,
    experimental_options={"enable_gpu_snapshot": True},
    scaledown_window=2,
)
@modal.concurrent(max_inputs=4)
class DecomposerService:
    @modal.enter(snap=True)
    def start(self):
        import logging

        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("decomposer")
        self.logger.info("Starting vLLM for %s (AWQ-Int4)...", MODEL_NAME)

        cmd = [
            "vllm", "serve", MODEL_NAME,
            "--dtype", "auto",
            "--host", "0.0.0.0",
            "--port", str(VLLM_PORT),
            "--gpu-memory-utilization", "0.90",  # AWQ-Int4 ~37GB, sobra bastante na H200
            "--enable-sleep-mode",
            "--enable-auto-tool-choice",
            "--tool-call-parser", "hermes",
            "--max-num-seqs", "16",
            "--max-model-len", "32768",
            "--uvicorn-log-level", "error",
            "--disable-uvicorn-access-log",
            "--disable-log-requests",
        ]

        self.vllm_proc = subprocess.Popen(cmd)  # logs em tempo real no Modal dashboard

        _wait_ready(self.vllm_proc)

        self.logger.info("vLLM ready on port %d", VLLM_PORT)
        self.logger.info("Running warm-up...")
        _warmup()
        self.logger.info("Warm-up done, sleeping for snapshot...")
        _sleep()
        self.logger.info("vLLM sleeping -- snapshot point")

    @modal.enter(snap=False)
    def restore(self):
        import logging

        try:
            import torch.distributed as dist
            if dist.is_initialized():
                dist.destroy_process_group()
        except Exception:
            pass

        if not hasattr(self, "logger"):
            logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
            self.logger = logging.getLogger("decomposer")

        self.logger.info("Waking vLLM...")
        _wake_up()
        _wait_ready(self.vllm_proc, timeout=MINUTES)
        self.logger.info("vLLM awake on port %d", VLLM_PORT)

    @modal.exit()
    def stop(self):
        if hasattr(self, "vllm_proc") and self.vllm_proc.poll() is None:
            self.vllm_proc.terminate()
            try:
                self.vllm_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.vllm_proc.kill()

    @modal.method(is_generator=True)
    def decompose(self, query: str, system_prompt: str):
        """Agentic loop completo: inference + tool execution + multi-turno.

        Yield progress pra cada round. Yield final com resultados consolidados
        (deduplicados por doc_id, rankeados por RRF score).
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        all_tool_calls = []
        # Coleta todos os resultados de busca: {doc_id -> {result, found_via}}
        all_results = {}
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_inference_time = 0

        for round_num in range(1, MAX_ROUNDS + 1):
            payload = {
                "model": MODEL_NAME,
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto",
                "max_tokens": 4096,
                "temperature": 0.6,
            }

            t0 = time.time()
            resp = _requests.post(
                f"http://localhost:{VLLM_PORT}/v1/chat/completions",
                json=payload, timeout=300,
            )
            if resp.status_code != 200:
                self.logger.error("vLLM returned %d: %s", resp.status_code, resp.text[:2000])
                resp.raise_for_status()
            data = resp.json()
            inference_time = time.time() - t0

            choice = data["choices"][0]
            message = choice["message"]
            usage = data.get("usage", {})
            finish_reason = choice.get("finish_reason", "")

            total_prompt_tokens += usage.get("prompt_tokens", 0)
            total_completion_tokens += usage.get("completion_tokens", 0)
            total_inference_time += inference_time

            tool_calls = message.get("tool_calls", [])

            if not tool_calls or finish_reason == "stop":
                yield {
                    "type": "round",
                    "round": round_num,
                    "tool_calls": [],
                    "search_results": [],
                    "content": message.get("content", ""),
                    "finish_reason": finish_reason,
                    "inference_time": round(inference_time, 2),
                    "usage": usage,
                }
                break

            all_tool_calls.extend(tool_calls)

            # Execute searches
            self.logger.info("Round %d: executing %d searches...", round_num, len(tool_calls))
            t_search = time.time()
            tool_msgs, full_results = _execute_tool_calls(tool_calls)
            search_time = time.time() - t_search
            self.logger.info("Searches done in %.1fs (%d results)", search_time, len(full_results))

            # Dedup into all_results by doc_id, keeping highest RRF
            for r in full_results:
                doc_id = r.get("doc_id", "")
                if not doc_id:
                    continue
                rrf = r.get("scores", {}).get("rrf", 0)
                existing = all_results.get(doc_id)
                if not existing or rrf > existing.get("scores", {}).get("rrf", 0):
                    all_results[doc_id] = r

            # Yield round progress com resultados
            yield {
                "type": "round",
                "round": round_num,
                "tool_calls": [
                    {
                        "name": tc["function"]["name"],
                        "arguments": json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"],
                    }
                    for tc in tool_calls
                ],
                "search_results_count": len(full_results),
                "unique_docs_so_far": len(all_results),
                "content": message.get("content", ""),
                "finish_reason": finish_reason,
                "inference_time": round(inference_time, 2),
                "search_time": round(search_time, 2),
                "usage": usage,
            }

            # Build next turn messages
            assistant_msg = {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"] if isinstance(tc["function"]["arguments"], str) else json.dumps(tc["function"]["arguments"]),
                        },
                    }
                    for tc in tool_calls
                ],
            }
            messages.append(assistant_msg)
            messages.extend(tool_msgs)

        # --- Consolidate results (dedup by doc_id, rank by RRF) ---
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x.get("scores", {}).get("rrf", 0),
            reverse=True,
        )[:50]  # max 50

        yield {
            "type": "done",
            "query": query,
            "results": sorted_results,
            "total_results": len(sorted_results),
            "total_unique_docs": len(all_results),
            "decomposition": {
                "total_tool_calls": len(all_tool_calls),
                "queries": [
                    {
                        "name": tc["function"]["name"],
                        "arguments": json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"],
                    }
                    for tc in all_tool_calls
                ],
                "rounds": round_num,
            },
            "usage": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "inference_time": round(total_inference_time, 2),
            },
            "model": MODEL_NAME,
        }
