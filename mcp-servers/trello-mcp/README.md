# Trello MCP Server

**Production-grade Model Context Protocol server for Trello integration with Claude.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Protocol](https://img.shields.io/badge/MCP-2025--06--18-green.svg)](https://modelcontextprotocol.io/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Features

✅ **Full Read/Write Access** - List boards, create cards, move cards between lists
✅ **Production-Grade Architecture** - Pydantic schemas, async httpx, exponential backoff
✅ **Rate Limit Handling** - Intelligent throttling (90 req/10s default, configurable)
✅ **Protocol Compliance** - Strict MCP 2025-06-18 specification adherence
✅ **Zero Hardcoding** - Environment-based configuration (12-factor app principles)
✅ **Fail-Fast Validation** - Startup checks prevent runtime authentication errors
✅ **Works With Both** - Claude Desktop AND Claude Code CLI

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **uv** package manager ([install](https://astral.sh/uv))
- **Trello API credentials** (see below)
- **Claude Desktop** or **Claude Code CLI**

### 1. Get Trello API Credentials

**🛑 STOP HERE FIRST - You need these credentials before proceeding.**

1. Go to [https://trello.com/power-ups/admin](https://trello.com/power-ups/admin)
2. Click **"New"** → Enter name (e.g., "Claude MCP") and your email
3. Copy the **API Key** shown
4. Click the **Token** link → Authorize → Copy the **Token**
5. ⚠️ **Recommended:** Set token to **"never expire"** to avoid re-authentication

**Keep these credentials safe - you'll need them in the next step.**

---

### 2. Installation

```bash
# Clone or download this repository
cd /path/to/trello-mcp

# Install dependencies with uv
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or vim, code, etc.
```

**Edit `.env` file:**
```env
TRELLO_API_KEY=your_api_key_from_step_1
TRELLO_API_TOKEN=your_token_from_step_1
```

---

### 3. Validate Setup

**CRITICAL:** Run this validation script BEFORE configuring Claude.

```bash
uv run python verify_setup.py
```

**Expected output:**
```
✓ Environment variables loaded successfully
✓ Authentication successful!
✓ Found 5 board(s):
  - My Project Board (ID: abc123...)
✓ ALL CHECKS PASSED
```

If you see errors, fix them before proceeding. Common issues:
- Missing `.env` file → Copy `.env.example` to `.env`
- Invalid credentials → Regenerate at https://trello.com/power-ups/admin
- Network issues → Check firewall/proxy settings

---

### 4. Configure Claude

Choose your platform:

#### Option A: Claude Desktop

1. Open Claude Desktop settings
2. Navigate to **Developer → Model Context Protocol**
3. Click **"Add Server"**
4. Use configuration from `configs/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "trello": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/trello-mcp",
        "run",
        "python",
        "-m",
        "src.server"
      ],
      "env": {
        "TRELLO_API_KEY": "your_api_key_here",
        "TRELLO_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

**Replace:**
- `/ABSOLUTE/PATH/TO/trello-mcp` → Your actual path (e.g., `/Users/you/projects/trello-mcp`)
- `your_api_key_here` → Your actual API key
- `your_token_here` → Your actual token

5. **Restart Claude Desktop**

#### Option B: Claude Code CLI

See detailed guide: **[configs/claude_code_cli_setup.md](configs/claude_code_cli_setup.md)**

**Quick version:**
```bash
cd /path/to/trello-mcp

# Export credentials
export TRELLO_API_KEY="your_api_key"
export TRELLO_API_TOKEN="your_token"

# Register server (user scope)
claude mcp add trello \
  "uv --directory $(pwd) run python -m src.server" \
  TRELLO_API_KEY=$TRELLO_API_KEY \
  TRELLO_API_TOKEN=$TRELLO_API_TOKEN \
  -s user

# Verify
claude mcp list
# Should show: trello - connected ✓
```

---

## 📚 Usage

### Available Tools

Once configured, Claude has access to three tools:

#### 1. `trello_get_board_structure`

**Get complete board structure (lists + cards).**

```
Get the structure of board abc123
```

**Returns:**
- Board name, URL, description
- All lists with their IDs
- All cards currently on the board

**⚠️ IMPORTANT:** You MUST call this first to discover list IDs before creating/moving cards.

---

#### 2. `trello_create_card`

**Create a new card in a specific list.**

```
Create a card in list xyz789 titled "Fix login bug" with description "Users can't log in with SSO"
```

**Parameters:**
- `list_id` (required): 24-character list ID from `get_board_structure`
- `name` (required): Card title (max 16,384 chars)
- `desc` (optional): Card description (supports Markdown)
- `due` (optional): Due date (ISO 8601: `2025-12-31T23:59:59Z`)

---

#### 3. `trello_move_card`

**Move a card to a different list.**

```
Move card abc123 to list xyz789
```

**Parameters:**
- `card_id` (required): 24-character card ID
- `target_list_id` (required): 24-character destination list ID

---

### Example Workflows

#### Workflow 1: Create a Task from Code Review

```
1. Get the structure of my "Development" board
2. Create a card in the "To Do" list:
   - Title: "Refactor authentication module"
   - Description: "Current implementation uses deprecated crypto library.
                   Need to migrate to modern standard."
3. Confirm the card was created
```

#### Workflow 2: Automate Bug Reporting

```
Analyze the file src/auth.js and identify the bug causing the login failure.
Then create a Trello card in my "Bugs" list with:
- Title: Specific error description
- Description: Code snippet showing the bug + suggested fix
```

#### Workflow 3: Project Management Automation

```
Get my "Sprint Board" structure.
For each card in the "In Progress" list that hasn't been updated in 7 days,
move it back to "Backlog" and add a comment explaining it's been deprioritized.
```

---

## 🏗️ Architecture

### Technology Stack

- **MCP SDK** (`mcp>=1.0.0`) - Official Model Context Protocol implementation
- **httpx** (`>=0.27.0`) - Modern async HTTP client
- **Pydantic** (`>=2.0.0`) - Data validation and settings management
- **backoff** (`>=2.2.0`) - Exponential backoff for retry logic

### Design Principles

1. **No Hardcoding:** All configuration via environment variables
2. **No Absolute Paths:** Runtime detection of project location
3. **Protocol Hygiene:** Application logs → `stderr`, MCP messages → `stdout`
4. **Async First:** Non-blocking I/O with `httpx.AsyncClient`
5. **Strong Schemas:** Pydantic models for all data (fail-fast validation)

### Rate Limiting Strategy

- **Default:** 90 requests / 10 seconds (conservative)
- **Trello Limits:** 100 req/10s per token, 300 req/10s per API key
- **Implementation:** Proactive throttling + exponential backoff on 429 errors
- **Configurable:** Set `RATE_LIMIT_PER_10_SECONDS` in `.env`

### Error Handling

All errors are returned inside `CallToolResult` with `isError=True` (per MCP spec):

- **Auth Errors (401/403):** Don't retry, return immediately
- **Rate Limits (429):** Retry with exponential backoff (max 5 attempts)
- **Network Errors:** Retry with jitter
- **Validation Errors:** Return detailed Pydantic error messages

---

## 🛠️ Development

### Running Tests

```bash
# Install dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

### Project Structure

```
trello-mcp/
├── src/
│   ├── __init__.py
│   ├── models.py          # Pydantic schemas
│   ├── trello_client.py   # Trello API client
│   └── server.py          # MCP server implementation
├── tests/
│   └── (test files)
├── configs/
│   ├── claude_desktop_config.json
│   └── claude_code_cli_setup.md
├── .env.example           # Environment template
├── pyproject.toml         # Project dependencies
├── verify_setup.py        # Validation script
└── README.md              # This file
```

### Adding New Tools

1. Define Pydantic input schema in `src/models.py`
2. Add API method in `src/trello_client.py`
3. Define MCP `Tool` in `src/server.py`
4. Register handler in `TrelloMCPServer._register_handlers()`
5. Add tests in `tests/`

---

## 📖 API Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TRELLO_API_KEY` | ✅ | - | API key from Power-Up admin |
| `TRELLO_API_TOKEN` | ✅ | - | Auth token with read/write scope |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `RATE_LIMIT_PER_10_SECONDS` | ❌ | `90` | Max requests per 10-second window |

### Trello API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/members/me` | GET | Validate credentials |
| `/boards/{id}` | GET | Get board metadata |
| `/boards/{id}/lists` | GET | Get all lists in board |
| `/boards/{id}/cards` | GET | Get all cards in board (nested resource) |
| `/cards` | POST | Create new card |
| `/cards/{id}` | PUT | Update card (move to list) |

---

## 🔒 Security

### Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use token expiration wisely:**
   - Production: "never expire" (convenient but less secure)
   - Development: 30 days (more secure, requires renewal)
3. **Restrict token scope** if possible (board-specific access)
4. **Rotate credentials** if compromised
5. **Use project-scope MCP servers** for sensitive workflows

### Credential Storage

- Claude Desktop: Credentials in config file (`~/.config/claude/config.json`)
- Claude Code CLI: Passed as environment variables (not stored)
- Server: Loaded from `.env` file (never logged or transmitted)

---

## 🐛 Troubleshooting

### "Authentication failed"

**Symptoms:** `✗ Authentication failed: 401 Unauthorized`

**Solutions:**
1. Verify credentials at https://trello.com/power-ups/admin
2. Regenerate token (ensure "never expire" is selected)
3. Check `.env` file has correct `TRELLO_API_KEY` and `TRELLO_API_TOKEN`
4. Run `uv run python verify_setup.py` to diagnose

---

### "Rate limit exceeded"

**Symptoms:** `429 Too Many Requests` or `Rate limit of 90 req/10s reached`

**Solutions:**
1. Reduce `RATE_LIMIT_PER_10_SECONDS` in `.env` (try 50)
2. Wait 10 seconds for rate limit window to reset
3. Check if multiple Claude instances are using same token

---

### "Server not connecting" (Claude Desktop)

**Symptoms:** Server shows "disconnected" or no tools available

**Solutions:**
1. **Check absolute path** in config (no `~` or `$HOME`, use full path)
2. **Verify uv is in PATH:**
   ```bash
   which uv
   # If not found: curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **Check Claude Desktop logs:**
   - Mac: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\logs\`
   - Linux: `~/.config/Claude/logs/`
4. **Test server manually:**
   ```bash
   cd /path/to/trello-mcp
   uv run python -m src.server
   # Should NOT crash immediately
   ```

---

### "Server not connecting" (Claude Code CLI)

**Symptoms:** `claude mcp list` shows server as "disconnected"

**Solutions:**
1. **Check registration:**
   ```bash
   claude mcp list
   # Verify "trello" appears
   ```
2. **View logs:**
   ```bash
   claude mcp logs trello
   ```
3. **Re-register with explicit env vars:**
   ```bash
   claude mcp remove trello -s user
   claude mcp add trello \
     "uv --directory $(pwd) run python -m src.server" \
     TRELLO_API_KEY=$TRELLO_API_KEY \
     TRELLO_API_TOKEN=$TRELLO_API_TOKEN \
     -s user
   ```

---

### "Module not found" errors

**Symptoms:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:**
```bash
cd /path/to/trello-mcp
uv sync
```

If using system Python instead of uv:
```bash
pip install -e .
```

---

## 📝 Changelog

### v1.0.0 (2025-11-23)

- ✅ Initial production release
- ✅ Full MCP 2025-06-18 specification compliance
- ✅ Three core tools: get_board_structure, create_card, move_card
- ✅ Exponential backoff with jitter for rate limiting
- ✅ Pydantic schemas for strict type safety
- ✅ Support for both Claude Desktop and Claude Code CLI
- ✅ Comprehensive validation script
- ✅ Production-grade error handling

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Run validation before committing:**
   ```bash
   uv run pytest
   uv run mypy src/
   uv run ruff check src/
   ```

2. **Add tests for new features**
3. **Update documentation** (README, docstrings, CHANGELOG)
4. **Follow architectural constraints** (no hardcoding, async-first, Pydantic schemas)

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) - Model Context Protocol specification
- [Trello/Atlassian](https://trello.com) - Trello API
- [Astral](https://astral.sh) - uv package manager and Ruff linter

---

## 📞 Support

- **Issues:** Open an issue in this repository
- **Trello API Docs:** https://developer.atlassian.com/cloud/trello/
- **MCP Specification:** https://modelcontextprotocol.io/
- **Claude Documentation:** https://docs.anthropic.com/

---

**Built with ❤️ for the Claude + Trello community**
