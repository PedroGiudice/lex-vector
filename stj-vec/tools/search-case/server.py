"""MCP server for semantic search in case knowledge databases.

JSON-RPC 2.0 with Content-Length framing. Zero external deps (stdlib + sqlite_vec).
"""
import json
import logging
import os
import sqlite3
import struct
import sys
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s: %(message)s")
log = logging.getLogger("search-case")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/embeddings")
EMBED_MODEL = "bge-m3"

SEARCH_TOOL = {
    "name": "search_case",
    "description": "Busca semantica nos documentos do caso juridico atual. Resolve knowledge.db pelo working directory.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Texto para busca semantica"},
            "limit": {"type": "integer", "default": 10},
            "threshold": {"type": "number", "default": 0.3},
        },
        "required": ["query"],
    },
}

SERVER_INFO = {
    "name": "search-case",
    "version": "0.1.0",
}


def find_knowledge_db() -> Path | None:
    """Walk up from CWD to find knowledge.db (max 4 levels)."""
    current = Path.cwd()
    for _ in range(5):  # current + 4 parents
        candidate = current / "knowledge.db"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def embed_query(text: str) -> list[float]:
    """Get embedding from Ollama bge-m3."""
    payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode()
    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["embedding"]


def search(db_path: Path, query_embedding: list[float], limit: int, threshold: float) -> list[dict]:
    """Run KNN search via sqlite-vec."""
    import sqlite_vec

    conn = sqlite3.connect(str(db_path))
    sqlite_vec.load(conn)
    conn.row_factory = sqlite3.Row

    blob = struct.pack(f"<{len(query_embedding)}f", *query_embedding)

    rows = conn.execute(
        """
        SELECT vc.chunk_id, vc.distance, c.content, c.doc_id, d.source_file
        FROM vec_chunks vc
        JOIN chunks c ON c.id = vc.chunk_id
        JOIN documents d ON d.id = c.doc_id
        WHERE vc.embedding MATCH ?1 AND k = ?2
        ORDER BY vc.distance
        """,
        (blob, limit),
    ).fetchall()
    conn.close()

    results = []
    for row in rows:
        score = 1.0 - row["distance"]
        if score >= threshold:
            results.append({
                "chunk_id": row["chunk_id"],
                "score": round(score, 3),
                "content": row["content"],
                "doc_id": row["doc_id"],
                "source_file": row["source_file"],
            })
    return results


def execute_search(args: dict) -> dict:
    """Orchestrate: find db, embed, search, format."""
    query = args["query"]
    limit = args.get("limit", 10)
    threshold = args.get("threshold", 0.3)

    db_path = find_knowledge_db()
    if db_path is None:
        return {"content": [{"type": "text", "text": "Erro: knowledge.db nao encontrado (buscou ate 4 niveis acima do CWD)."}]}

    try:
        embedding = embed_query(query)
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Erro ao gerar embedding: {e}"}]}

    try:
        results = search(db_path, embedding, limit, threshold)
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Erro na busca: {e}"}]}

    if not results:
        return {"content": [{"type": "text", "text": f"Nenhum resultado acima do threshold {threshold} para: {query}"}]}

    lines = [f"**{len(results)} resultados** (knowledge.db: {db_path})\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"### {i}. {r['source_file']} (score: {r['score']})")
        lines.append(r["content"])
        lines.append("")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


# --- MCP Protocol (JSON-RPC 2.0 + Content-Length framing) ---

def read_message() -> dict | None:
    """Read a Content-Length framed JSON-RPC message from stdin."""
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        line_str = line.decode("utf-8").strip()
        if line_str.startswith("Content-Length:"):
            length = int(line_str.split(":", 1)[1].strip())
            # Read blank line
            sys.stdin.buffer.readline()
            data = sys.stdin.buffer.read(length)
            return json.loads(data)
        # Skip other headers or blank lines


def write_message(msg: dict) -> None:
    """Write a Content-Length framed JSON-RPC message to stdout."""
    body = json.dumps(msg).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    sys.stdout.buffer.write(header + body)
    sys.stdout.buffer.flush()


def make_response(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle_request(msg: dict) -> dict | None:
    """Handle a JSON-RPC request. Returns response or None for notifications."""
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        return make_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })

    if method == "notifications/initialized":
        return None  # notification, no response

    if method == "tools/list":
        return make_response(req_id, {"tools": [SEARCH_TOOL]})

    if method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        if tool_name == "search_case":
            result = execute_search(arguments)
            return make_response(req_id, result)
        return make_error(req_id, -32601, f"Unknown tool: {tool_name}")

    if method.startswith("notifications/"):
        return None

    return make_error(req_id, -32601, f"Method not found: {method}")


def main() -> None:
    log.info("search-case MCP server started")
    while True:
        msg = read_message()
        if msg is None:
            break
        log.info("Received: %s", msg.get("method", "unknown"))
        response = handle_request(msg)
        if response is not None:
            write_message(response)
    log.info("search-case MCP server exiting")


if __name__ == "__main__":
    main()
