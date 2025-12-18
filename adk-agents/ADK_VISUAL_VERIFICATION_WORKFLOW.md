# ADK + Claude Visual Verification Workflow

> **Purpose**: Orchestrate ADK agents (Gemini) for frontend code generation with Claude Code visual verification via Playwright.

## Architecture

```
┌─────────────────┐    task + spec    ┌─────────────────┐
│  Claude Code    │ ────────────────► │   ADK Agent     │
│  (Orchestrator) │                   │   (Gemini)      │
└─────────────────┘                   └─────────────────┘
        │                                     │
        │ Playwright                          │ write_file()
        │ screenshot                          │
        ▼                                     ▼
┌─────────────────┐                   ┌─────────────────┐
│   Browser       │ ◄───── rebuild ───│   Frontend      │
│   Screenshot    │    (Vite HMR)     │   React/TS      │
└─────────────────┘                   └─────────────────┘
        │
        │ visual review
        ▼
┌─────────────────┐
│  Claude Code    │
│  (Validation)   │
└─────────────────┘
        │
        │ feedback loop
        ▼
   [Next Iteration or Done]
```

## Quick Start

```bash
# Navigate to adk-agents directory
cd ~/claude-work/repos/Claude-Code-Projetos/adk-agents

# Activate venv
source ../.venv/bin/activate

# Run with a task
python run_adk_with_verification.py --task "Make sidebars 20% width"

# Run with custom spec
python run_adk_with_verification.py --task "Apply layout spec" --spec layout_specs/my_spec.md

# Full auto mode (no manual review)
python run_adk_with_verification.py --task "..." --auto --max-iterations 5
```

## Components

### 1. `run_adk_with_verification.py`

Main orchestration script that:
- Loads layout specification
- Builds prompts for ADK agent
- Executes ADK agent via subprocess
- Waits for Vite hot reload
- Captures screenshots via Playwright
- Generates verification reports

### 2. Layout Specification

The spec defines the target design. Default spec included, or provide custom:

```markdown
# Layout Spec Example

## Visual Style
- Inspiration: VS Code, Obsidian
- Theme: Dark mode
- Style: Brutalism + Glassmorphism

## Color Palette
- Background: #1e1e2e
- Borders: #3f3f46 (1px)
- Text: #e4e4e7

## Layout Structure
- Columns: 20-60-20
- Sidebars: Collapsible, resizable
```

### 3. ADK Agent (`legal_tech_frontend_specialist`)

Gemini-powered agent specialized in:
- React/TypeScript
- Legal tech UIs
- Document annotation interfaces
- Tailwind CSS styling

Available tools:
- `read_file` / `write_file`
- `list_directory` / `get_directory_tree`
- `search_code`
- `run_command`

## Workflow Steps

### Step 1: Define Task

```bash
# Simple task
--task "Change sidebar width to 20%"

# Complex task
--task "Implement collapsible sidebar tabs with smooth animations"
```

### Step 2: Load/Create Spec

```bash
# Save default spec for editing
python run_adk_with_verification.py --save-spec

# Edit spec at: adk-agents/layout_specs/default_layout_spec.md
```

### Step 3: Execute

```bash
python run_adk_with_verification.py \
    --task "Apply dark mode with VS Code colors" \
    --spec layout_specs/my_spec.md
```

### Step 4: Review Screenshot

Screenshots saved to: `adk-agents/verification_screenshots/`

```
verification_screenshots/
├── iter_1_20231217_143022.png
├── iter_2_20231217_143145.png
└── report_20231217_143200.json
```

### Step 5: Provide Feedback (if needed)

If issues found, the loop continues with feedback:

```python
# In the report
"feedback": "Sidebar is 25% instead of 20%. Header still visible."
```

## Integration with Claude Code

### From Claude Code Session

```bash
# Direct execution
!python adk-agents/run_adk_with_verification.py --task "..."

# Or use Task tool with appropriate agent for complex orchestration
```

### Screenshot Review in Claude

After script runs:
1. Open screenshot in Claude Desktop or via `Read` tool
2. Analyze visual output
3. Provide feedback for next iteration

## Configuration

### Environment Variables

Required in `adk-agents/.env`:
```
GOOGLE_API_KEY=your_gemini_api_key
```

### Paths

| Path | Description |
|------|-------------|
| `adk-agents/layout_specs/` | Layout specification files |
| `adk-agents/verification_screenshots/` | Captured screenshots |
| `legal-workbench/frontend/src/` | React source code |

## Troubleshooting

### ADK Agent Fails

1. Check `GOOGLE_API_KEY` is set
2. Verify agent exists: `python run_agent.py --list`
3. Check agent output for errors

### Screenshot Fails

1. Ensure frontend is running: `http://localhost/app`
2. Install playwright: `npx playwright install chromium`
3. Check network connectivity

### Changes Not Reflected

1. Verify Vite is running with HMR
2. Increase wait time in script (default: 5s)
3. Check for build errors in terminal

## Best Practices

1. **Start Small**: Begin with isolated changes (single component)
2. **Use Spec**: Always define a clear spec for consistent results
3. **Review Each Iteration**: Don't skip visual review
4. **Save Good Specs**: Reuse specs that produce good results
5. **Document Deviations**: If deviating from North Star, document why

## Example Session

```bash
# 1. Ensure frontend is running
# (in another terminal)
cd legal-workbench/frontend && npm run dev

# 2. Run verification workflow
cd adk-agents
python run_adk_with_verification.py \
    --task "Implement VS Code dark theme with 20-60-20 columns" \
    --max-iterations 3

# 3. Review screenshots in Claude Code
# (screenshots appear in verification_screenshots/)

# 4. If issues, provide feedback for next iteration
# 5. Continue until satisfied
```

## Related Files

- `run_agent.py` - Universal ADK agent runner
- `legal_tech_frontend_specialist/agent.py` - Frontend specialist agent
- `shared/tools.py` - Shared ADK tools (read/write/search)

---

*Last updated: 2024-12-17*
