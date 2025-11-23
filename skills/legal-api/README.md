# Legal-API Skill

Expert guidance for working with the Legal-API DJEN ecosystem (Brazilian legal data systems).

## Overview

This skill provides comprehensive knowledge for:
- **API DJEN integration** with known limitations and workarounds
- **Three specialized agents** (djen-tracker, jurisprudencia-collector, legal-lens)
- **MCP server** (djen-mcp-server) for Claude Desktop
- **Database schema** (SQLite with FTS5 + RAG)
- **Performance optimization** (535x speedup via batch commits, 4.8x via adaptive rate limiting)
- **Common pitfalls** and debugging strategies

## When to Use

Use this skill when:
- Working with DJEN API endpoints
- Debugging rate limiting or performance issues
- Implementing legal data download systems
- Building jurisprudence databases
- Creating RAG systems for legal documents
- Troubleshooting any of the DJEN agents or MCP server

## Key Features

### Critical Known Issues
- ❌ **OAB filter does NOT work** - API ignores `numeroOab` parameter
- ⚠️ **Rate limiting**: 21 req/5s sliding window
- ✅ **Hash-based deduplication** required (API IDs unreliable)
- ✅ **Case-insensitive normalization** for type filtering

### Performance Best Practices
- **Adaptive rate limiting**: 144 req/min sustainable (12 req/5s buffer)
- **Batch commits**: 535x speedup (100 records/batch)
- **Exponential backoff**: Retry with 2^n seconds delay
- **Real gains**: 6-month download reduced from ~100h to ~21h

### Agent Architecture
1. **djen-tracker**: Download cadernos (65 tribunals), OAB filtering, parallel processing
2. **jurisprudencia-collector**: API processing, ementa extraction, SQLite storage, RAG
3. **legal-lens**: RAG semantic search, 13 legal themes, ChromaDB

## Resources

### References
- `known-issues.md` - Complete list of API quirks (MUST READ before coding)
- `schema.md` - SQLite database schema with FTS5 and RAG tables
- `api-reference.md` - DJEN API documentation and examples

### Scripts
- `diagnostic.py` - Performance profiling and bottleneck analysis
- `example_download.py` - Complete integration example with all best practices
- `example_rag.py` - RAG implementation for semantic search

## Quick Start

### Check for Known Issues
```python
# ALWAYS consult references/known-issues.md first
# Common mistake: using offset parameter (doesn't exist!)

# ❌ WRONG
publicacoes = downloader.baixar_api(..., offset=100)  # TypeError!

# ✅ CORRECT
publicacoes = downloader.baixar_api(..., max_pages=10)
```

### Run Performance Diagnostic
```bash
python skills/legal-api/scripts/diagnostic.py \
    --tribunal STJ \
    --data 2025-11-20 \
    --profile
```

### Example Integration
```bash
python skills/legal-api/scripts/example_download.py \
    --tribunal STJ \
    --data 2025-11-20 \
    --output results.db
```

## Troubleshooting Checklist

- [ ] Read `references/known-issues.md`
- [ ] No `offset` parameter (doesn't exist)
- [ ] Rate limiting enabled (`adaptive_rate_limit=True`)
- [ ] Batch commits (`BATCH_SIZE = 100`)
- [ ] Normalizing types (case-insensitive, no accents)
- [ ] Hash deduplication (not API ID)
- [ ] Recent test dates (<30 days)

## Installation

This is a Claude Code skill. To use:

1. **Extract** the skill to your skills directory:
   ```bash
   cp -r legal-api ~/claude-work/repos/Claude-Code-Projetos/skills/
   ```

2. **Claude Code will automatically detect** the skill based on SKILL.md

3. **Trigger the skill** by mentioning DJEN, legal-api, or asking about:
   - API integration issues
   - Performance problems
   - Agent architecture
   - Database schema
   - RAG implementation

## License

MIT License - Part of Claude-Code-Projetos

---

**Created:** 2025-11-23
**Version:** 1.0.0
**Status:** ✅ Production Ready
