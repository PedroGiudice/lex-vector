#!/usr/bin/env python3
"""
Run ADK agent to finalize Doc Assembler Frontend (Phases 5-7).
"""
import os
import sys
import asyncio
from pathlib import Path
import uuid

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY not set")
    sys.exit(1)

print("=" * 60)
print("ADK Agent - Frontend Finalization (Phases 5-7)")
print("=" * 60)

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

TASK_PROMPT = """
# Task: Finalize Doc Assembler Frontend (Phases 5, 6, 7)

## Current State
The frontend is partially implemented at:
`/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-workbench/frontend/`

Working features:
- DropZone for file upload
- Document viewer layout
- Basic annotation list
- Dark mode (GitHub theme)

## Remaining Work

### Phase 5: Pattern Detection UI (1-2h)
Files to modify/create:
- `src/components/document/PatternList.tsx` - Show detected patterns
- `src/components/document/PatternItem.tsx` - Accept/reject pattern
- Update `DocumentViewer.tsx` to highlight patterns in yellow
- Update `documentStore.ts` to manage pattern state

Features:
- Call `/api/doc/api/v1/builder/patterns` after upload
- Show detected patterns (CPF, dates, etc) in sidebar
- Each pattern has "Accept" button to convert to annotation
- Toggle to show/hide patterns in document

### Phase 6: Save Template Modal (2h)
Files to modify/create:
- `src/components/templates/SaveTemplateModal.tsx` - Modal form
- `src/components/templates/TemplateList.tsx` - List saved templates
- `src/components/templates/TemplateCard.tsx` - Template preview card
- Update `Sidebar.tsx` to show template list

Features:
- Modal with name + description inputs
- Validation before save
- Call `/api/doc/api/v1/builder/save` API
- Show success toast
- Template list shows saved templates
- Click template to load it

### Phase 7: Polish (2h)
Files to modify:
- Add loading spinners during API calls
- Add error boundaries
- Improve empty states
- Add keyboard shortcuts (Escape to cancel selection)
- Fix any TypeScript errors

## Design Guidelines (MUST FOLLOW)
```css
/* GitHub Dark Theme - DO NOT CHANGE */
--bg-primary: #0d1117;
--bg-secondary: #161b22;
--bg-tertiary: #21262d;
--text-primary: #c9d1d9;
--text-secondary: #8b949e;
--accent-primary: #58a6ff;
--accent-success: #3fb950;
--accent-danger: #f85149;
--border-default: #30363d;
```

## API Endpoints (Already Implemented)
- POST `/api/doc/api/v1/builder/upload` - Upload DOCX
- POST `/api/doc/api/v1/builder/patterns` - Detect patterns
- POST `/api/doc/api/v1/builder/save` - Save template
- GET `/api/doc/api/v1/builder/templates` - List templates

## Instructions
1. Use `read_file` to see existing code
2. Use `write_file` to create/modify files
3. Maintain TypeScript strict mode
4. Follow existing code patterns
5. Test that files have no syntax errors

START IMPLEMENTATION NOW.
"""

async def main():
    from legal_tech_frontend_specialist.agent import root_agent

    print(f"\nAgent: {root_agent.name}")
    print(f"Model: {root_agent.model}")
    print(f"Tools: {len(root_agent.tools)}")

    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="frontend_finalization",
        session_service=session_service
    )

    user_id = "claude_code"
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name="frontend_finalization",
        user_id=user_id,
        session_id=session_id
    )

    print(f"\nSession: {session_id}")
    print("Sending task to agent...")
    print("-" * 60)

    message = types.Content(
        role="user",
        parts=[types.Part(text=TASK_PROMPT)]
    )

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(part.text[:2000])
                if hasattr(part, 'function_call') and part.function_call:
                    print(f"\n[TOOL] {part.function_call.name}({str(part.function_call.args)[:100]})")
                if hasattr(part, 'function_response') and part.function_response:
                    print(f"[RESULT] {str(part.function_response)[:300]}...")

    await runner.close()
    print("\n" + "=" * 60)
    print("Agent execution complete!")

if __name__ == "__main__":
    asyncio.run(main())
