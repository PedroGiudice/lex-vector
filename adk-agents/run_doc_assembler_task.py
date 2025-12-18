#!/usr/bin/env python3
"""
Run ADK agents for Doc Assembler Frontend task.

This script invokes the Gemini ADK agents:
- legal-tech-frontend-specialist: For React/TypeScript frontend

Usage:
    cd adk-agents
    source ../.venv/bin/activate
    python run_doc_assembler_task.py
"""
import os
import sys
import asyncio
from pathlib import Path
import uuid

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Verify API key
if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY not set in .env")
    sys.exit(1)

print("=" * 60)
print("ADK Agents - Doc Assembler Frontend Task")
print("=" * 60)

# Import ADK
try:
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    print("✓ Google ADK imported successfully")
except ImportError as e:
    print(f"ERROR: Failed to import google.adk: {e}")
    print("Run: pip install google-adk google-genai")
    sys.exit(1)

# Task prompt for the agents
TASK_PROMPT = """
# Task: Create Doc Assembler Template Builder Frontend

## Context
We are building a React frontend for the Doc Assembler service in legal-workbench.
The plan is documented at: /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-workbench/PLAN-doc-assembler-frontend.md

## Requirements
1. **Upload DOCX** - Users upload Word documents
2. **Text Selection** - Select text passages and mark them as Jinja fields
3. **Auto-detection** - Detect patterns (CPF, dates, names) automatically
4. **Save Template** - Generate DOCX with {{ placeholders }}
5. **Dark Mode** - VS Code/GitHub dark theme

## Technology Stack
- React 18 + TypeScript
- Vite for build
- Tailwind CSS (dark mode)
- Zustand for state
- Lucide React for icons

## Design Reference
- Dark mode (GitHub Dark palette)
- 3-panel layout: Sidebar | Document Viewer | Annotations
- Colors: bg-primary: #0d1117, text: #c9d1d9, accent: #58a6ff

## Output Location
Create the frontend at: /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-workbench/frontend/

## Key Components Needed
1. DropZone.tsx - File upload with drag & drop
2. DocumentViewer.tsx - Render text with selection support
3. TextSelection.tsx - Capture selection, name the field
4. AnnotationList.tsx - List of marked fields
5. useTextSelection.ts - Hook for window.getSelection()

Please generate production-ready React code following best practices.
Use read_file and write_file tools to create the actual files.
"""


async def run_frontend_specialist():
    """Run the legal-tech-frontend-specialist agent."""
    print("\n" + "-" * 60)
    print("Running: legal-tech-frontend-specialist")
    print("-" * 60)

    try:
        # Import agent - using frontend-commander which has file write tools
        agent_dir = PROJECT_ROOT / "frontend-commander"
        sys.path.insert(0, str(agent_dir))

        import importlib.util
        spec = importlib.util.spec_from_file_location("agent", agent_dir / "agent.py")
        agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_module)
        root_agent = agent_module.root_agent

        print(f"Agent: {root_agent.name}")
        print(f"Model: {root_agent.model}")

        # Create session service
        session_service = InMemorySessionService()

        # Create runner
        runner = Runner(
            agent=root_agent,
            app_name="doc_assembler_frontend",
            session_service=session_service
        )

        # Create session
        user_id = "claude_code_user"
        session_id = str(uuid.uuid4())

        # Create session first
        await session_service.create_session(
            app_name="doc_assembler_frontend",
            user_id=user_id,
            session_id=session_id
        )

        print(f"\nSession created: {session_id}")
        print("Sending task to agent...")

        # Create message content
        message = types.Content(
            role="user",
            parts=[types.Part(text=TASK_PROMPT)]
        )

        # Run and collect events
        events = []
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            events.append(event)
            # Print event type
            event_type = type(event).__name__
            if hasattr(event, 'content') and event.content:
                # Print text content
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"\n[{event_type}]: {part.text[:500]}...")

        print("\n" + "=" * 60)
        print("AGENT EXECUTION COMPLETE")
        print(f"Total events: {len(events)}")
        print("=" * 60)

        # Close runner
        await runner.close()

        return events

    except Exception as e:
        print(f"ERROR running legal-tech-frontend-specialist: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run the agent."""
    print("\nStarting ADK agent for Doc Assembler frontend...")
    print("This uses Gemini 3 Pro via Google ADK\n")

    result = await run_frontend_specialist()

    print("\n" + "=" * 60)
    print("Task Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
