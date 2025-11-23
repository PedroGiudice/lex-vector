# Claude Code CLI Configuration

This guide explains how to configure the Trello MCP Server for **Claude Code CLI**.

## Prerequisites

1. **Claude Code CLI installed** (version 2.0+)
2. **uv package manager** installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
3. **Trello credentials** (API Key + Token from https://trello.com/power-ups/admin)

---

## Installation Steps

### 1. Navigate to Project Directory

```bash
cd /path/to/trello-mcp
```

### 2. Install Dependencies with uv

```bash
# Create virtual environment and install dependencies
uv sync

# Or manually:
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
uv pip install -e .
```

### 3. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit with your credentials
nano .env  # or vim, code, etc.
```

Fill in:
```env
TRELLO_API_KEY=your_actual_api_key
TRELLO_API_TOKEN=your_actual_token
```

### 4. Validate Setup

```bash
# Run validation script
uv run python verify_setup.py
```

You should see:
```
✓ ALL CHECKS PASSED
Your Trello MCP server is ready to use!
```

---

## Option A: Register Server (User Scope - Recommended)

This makes the server available across all projects for your user.

```bash
claude mcp add trello \
  "uv --directory $(pwd) run python -m src.server" \
  TRELLO_API_KEY=$TRELLO_API_KEY \
  TRELLO_API_TOKEN=$TRELLO_API_TOKEN \
  -s user
```

**Explanation:**
- `trello`: Server name (you'll see this in Claude)
- `uv --directory $(pwd) run python -m src.server`: Command to run server
- Environment variables passed inline
- `-s user`: Install for current user (not project-specific)

### Verify Registration

```bash
claude mcp list
```

Output should include:
```
trello - connected ✓
```

---

## Option B: Register Server (Project Scope)

If you only want this server for a specific project:

```bash
# Navigate to your project directory
cd /path/to/your/project

# Add server for this project only
claude mcp add trello \
  "uv --directory /absolute/path/to/trello-mcp run python -m src.server" \
  TRELLO_API_KEY=$TRELLO_API_KEY \
  TRELLO_API_TOKEN=$TRELLO_API_TOKEN \
  -s project
```

**Note:** You must use **absolute paths** when using project scope.

---

## Option C: Manual Configuration (Advanced)

If you prefer manual configuration, edit:

**User scope:**
```bash
~/.config/claude/config.json
```

**Project scope:**
```bash
your-project/.claude/config.json
```

Add this to the `mcpServers` section:

```json
{
  "mcpServers": {
    "trello": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/trello-mcp",
        "run",
        "python",
        "-m",
        "src.server"
      ],
      "env": {
        "TRELLO_API_KEY": "your_api_key_here",
        "TRELLO_API_TOKEN": "your_token_here",
        "LOG_LEVEL": "INFO",
        "RATE_LIMIT_PER_10_SECONDS": "90"
      }
    }
  }
}
```

---

## Usage Examples

Once configured, use Claude Code CLI like this:

### List Available Tools

```bash
claude
> /mcp
```

You should see:
- `trello_get_board_structure`
- `trello_create_card`
- `trello_move_card`

### Example Workflow

```bash
claude
> Get the structure of my Trello board with ID abc123
> Create a new card in the "Backlog" list titled "Fix login bug"
> Move card xyz789 to the "Done" list
```

---

## Troubleshooting

### Server Not Connecting

1. **Check logs:**
   ```bash
   # Server logs go to stderr
   claude mcp logs trello
   ```

2. **Verify credentials:**
   ```bash
   uv run python verify_setup.py
   ```

3. **Check MCP status:**
   ```bash
   claude mcp list
   ```

### Environment Variables Not Loading

If using `.env` file doesn't work, pass variables explicitly:

```bash
export TRELLO_API_KEY="your_key"
export TRELLO_API_TOKEN="your_token"

claude mcp add trello \
  "uv --directory $(pwd) run python -m src.server" \
  TRELLO_API_KEY=$TRELLO_API_KEY \
  TRELLO_API_TOKEN=$TRELLO_API_TOKEN \
  -s user
```

### "Command not found: uv"

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Add to PATH:
```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

---

## Security Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Set token to "never expire"** when generating in Trello
3. **Use environment variables** instead of hardcoding credentials
4. **Restrict token scope** if possible (read/write to specific boards only)

---

## Updating the Server

```bash
cd /path/to/trello-mcp
git pull  # If using version control
uv sync   # Update dependencies
```

No need to re-register with `claude mcp add` unless you change the command.

---

## Removing the Server

```bash
# User scope
claude mcp remove trello -s user

# Project scope
claude mcp remove trello -s project
```

---

## Next Steps

- Read the main [README.md](../README.md) for detailed API documentation
- Check [examples/workflows.md](../examples/workflows.md) for advanced usage patterns
- Report issues at your project's issue tracker
