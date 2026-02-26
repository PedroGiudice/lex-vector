"""MCP server for hybrid search (dense + sparse) in case knowledge databases.

JSON-RPC 2.0 with Content-Length framing. Deps: sqlite_vec.
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

TEI_URL = os.environ.get("TEI_URL", "http://127.0.0.1:8080/embed")
RRF_K = 60  # Reciprocal Rank Fusion constant
RRF_THRESHOLD = 0.005  # Minimum RRF score to include in results

SEARCH_TOOL = {
    "name": "search_case",
    "description": (
        "Busca hibrida (semantica + lexical) nos documentos do caso juridico atual. "
        "Resolve knowledge.db pelo working directory."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Texto para busca"},
            "limit": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
}

SERVER_INFO = {
    "name": "search-case",
    "version": "0.3.0",
}


def find_knowledge_db() -> Path | None:
    """Walk up from CWD to find knowledge.db (max 4 levels)."""
    current = Path.cwd()
    for _ in range(5):
        candidate = current / "knowledge.db"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def embed_query(text: str) -> list[float]:
    """Get dense embedding from TEI (BGE-M3)."""
    payload = json.dumps({"inputs": [text]}).encode()
    req = urllib.request.Request(
        TEI_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data[0]


def has_fts5(conn: sqlite3.Connection) -> bool:
    """Check if chunks_fts table exists."""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks_fts'"
    ).fetchone()
    return row is not None


def search_dense(conn: sqlite3.Connection, query_embedding: list[float], limit: int) -> list[tuple[str, float]]:
    """KNN search via sqlite-vec. Returns [(chunk_id, distance)]."""
    blob = struct.pack(f"<{len(query_embedding)}f", *query_embedding)
    rows = conn.execute(
        """
        SELECT chunk_id, distance
        FROM vec_chunks
        WHERE embedding MATCH ?1 AND k = ?2
        ORDER BY distance
        """,
        (blob, limit),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def search_fts5(conn: sqlite3.Connection, query: str, limit: int) -> list[tuple[str, float]]:
    """FTS5 BM25 search. Returns [(chunk_id, bm25_score)] sorted by relevance."""
    # Sanitize: keep alphanumeric, whitespace, and hyphens (important for legal terms)
    safe = "".join(c for c in query if c.isalnum() or c.isspace() or c == "-")
    safe = safe.strip()
    if not safe:
        return []
    try:
        rows = conn.execute(
            """
            SELECT chunk_id, bm25(chunks_fts) as rank
            FROM chunks_fts
            WHERE chunks_fts MATCH ?1
            ORDER BY rank
            LIMIT ?2
            """,
            (safe, limit),
        ).fetchall()
        return [(r[0], r[1]) for r in rows]
    except sqlite3.OperationalError as e:
        log.warning("FTS5 search failed: %s", e)
        return []


def reciprocal_rank_fusion(
    dense_results: list[tuple[str, float]],
    sparse_results: list[tuple[str, float]],
    limit: int,
) -> list[tuple[str, float, float, float]]:
    """Pure RRF fusion of dense and sparse rankings.

    Returns [(chunk_id, rrf_score, dense_rank, sparse_bm25)] sorted by rrf_score desc.
    """
    scores: dict[str, dict] = {}

    for rank, (cid, dist) in enumerate(dense_results):
        scores.setdefault(cid, {"dense": 0.0, "sparse": 0.0, "dense_rank": 0, "sparse_raw": 0.0})
        scores[cid]["dense"] = 1.0 / (RRF_K + rank + 1)
        scores[cid]["dense_rank"] = rank + 1

    for rank, (cid, bm25) in enumerate(sparse_results):
        scores.setdefault(cid, {"dense": 0.0, "sparse": 0.0, "dense_rank": 0, "sparse_raw": 0.0})
        scores[cid]["sparse"] = 1.0 / (RRF_K + rank + 1)
        scores[cid]["sparse_raw"] = bm25

    fused = []
    for cid, s in scores.items():
        rrf = s["dense"] + s["sparse"]  # Pure RRF (no weighting)
        if rrf >= RRF_THRESHOLD:
            fused.append((cid, rrf, s["dense_rank"], s["sparse_raw"]))

    fused.sort(key=lambda x: x[1], reverse=True)
    return fused[:limit]


def execute_search(args: dict) -> dict:
    """Orchestrate hybrid search: find db, embed, search, fuse, format."""
    query = args["query"]
    limit = args.get("limit", 10)

    db_path = find_knowledge_db()
    if db_path is None:
        return {"content": [{"type": "text", "text": "Erro: knowledge.db nao encontrado (buscou ate 4 niveis acima do CWD)."}]}

    import sqlite_vec

    conn = sqlite3.connect(str(db_path))
    sqlite_vec.load(conn)

    # Dense embedding via TEI
    try:
        query_emb = embed_query(query)
    except Exception as e:
        conn.close()
        return {"content": [{"type": "text", "text": f"Erro ao gerar embedding via TEI: {e}"}]}

    # Dense search
    dense_results = search_dense(conn, query_emb, limit * 2)

    # Sparse search via FTS5
    fts5_available = has_fts5(conn)
    sparse_results = []
    if fts5_available:
        sparse_results = search_fts5(conn, query, limit * 3)

    # Fusion or dense-only
    if sparse_results:
        fused = reciprocal_rank_fusion(dense_results, sparse_results, limit)
    else:
        fused = [
            (cid, 1.0 / (RRF_K + rank + 1), rank + 1, 0.0)
            for rank, (cid, dist) in enumerate(dense_results[:limit])
            if 1.0 / (RRF_K + rank + 1) >= RRF_THRESHOLD
        ]

    if not fused:
        conn.close()
        return {"content": [{"type": "text", "text": f"Nenhum resultado para: {query}"}]}

    # Fetch chunk content
    lines = []
    mode = "hybrid (dense + FTS5)" if sparse_results else "dense only"
    lines.append(f"**{len(fused)} resultados** | modo: {mode} | db: {db_path}\n")

    for i, (cid, rrf, dense_rank, sparse_s) in enumerate(fused, 1):
        row = conn.execute(
            """SELECT c.content, d.source_file
               FROM chunks c
               JOIN documents d ON d.id = c.doc_id
               WHERE c.id = ?""",
            (cid,),
        ).fetchone()
        if row:
            content, source = row
            dense_info = f"D#{dense_rank}" if dense_rank > 0 else "D:--"
            sparse_info = f"S:{sparse_s:.2f}" if sparse_s != 0 else "S:--"
            lines.append(f"### {i}. {source} [RRF:{rrf:.4f} {dense_info} {sparse_info}]")
            lines.append(content)
            lines.append("")

    conn.close()
    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


# --- MCP Protocol (JSON-RPC 2.0 + Content-Length framing) ---

def read_message() -> dict | None:
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        line_str = line.decode("utf-8").strip()
        if line_str.startswith("Content-Length:"):
            length = int(line_str.split(":", 1)[1].strip())
            sys.stdin.buffer.readline()
            data = sys.stdin.buffer.read(length)
            return json.loads(data)


def write_message(msg: dict) -> None:
    body = json.dumps(msg).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    sys.stdout.buffer.write(header + body)
    sys.stdout.buffer.flush()


def make_response(req_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle_request(msg: dict) -> dict | None:
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
        return None

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
    log.info("search-case MCP server started (v0.3.0 hybrid TEI+FTS5)")
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
