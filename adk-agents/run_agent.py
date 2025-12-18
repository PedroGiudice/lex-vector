#!/usr/bin/env python3
"""
Universal ADK Agent Runner.

Usage:
    python run_agent.py <agent_module> [--prompt "your prompt"] [--file prompt.md] [--model MODEL]

Examples:
    # Run with inline prompt
    python run_agent.py legal_tech_frontend_specialist --prompt "Create a login form"

    # Run with prompt from file
    python run_agent.py legal_tech_frontend_specialist --file prompts/frontend_task.md

    # Override model
    python run_agent.py legal_tech_frontend_specialist --prompt "..." --model gemini-3-pro-preview

Available Models:
    - gemini-3-pro-preview  (best reasoning, limited tools)
    - gemini-2.5-flash      (best for agents with tools) [DEFAULT]
    - gemini-2.5-pro        (best for large context + reasoning)
"""
import os
import sys
import asyncio
import argparse
import importlib
from pathlib import Path
import uuid

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY not set")
    print("Get one at: https://aistudio.google.com/apikey")
    sys.exit(1)


def load_agent(module_name: str, model_override: str = None):
    """Dynamically load an agent from its module."""
    try:
        module = importlib.import_module(f"{module_name}.agent")
        agent = module.root_agent

        # Override model if specified
        if model_override:
            from google.adk.agents import Agent
            agent = Agent(
                name=agent.name,
                model=model_override,
                instruction=agent.instruction,
                description=agent.description,
                tools=agent.tools,
            )
            print(f"Model override: {model_override}")

        return agent
    except ModuleNotFoundError as e:
        print(f"ERROR: Agent module '{module_name}' not found")
        print(f"Available agents: {list_agents()}")
        sys.exit(1)


def list_agents() -> list[str]:
    """List available agent modules."""
    agents = []
    for item in PROJECT_ROOT.iterdir():
        if item.is_dir() and (item / "agent.py").exists():
            agents.append(item.name)
    return agents


async def run_agent(agent, prompt: str, timeout: int = 600):
    """Run an agent with the given prompt."""
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    print("=" * 70)
    print(f"ADK Agent Runner")
    print("=" * 70)
    print(f"Agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"Tools: {len(agent.tools)}")
    print("-" * 70)

    session_service = InMemorySessionService()
    app_name = f"run_{agent.name}"

    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service
    )

    user_id = "claude_code"
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id
    )

    print(f"Session: {session_id}")
    print(f"Timeout: {timeout}s")
    print("-" * 70)
    print("PROMPT:")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    print("-" * 70)
    print("EXECUTION:")
    print()

    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message
        ):
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        # Print text output (truncated for readability)
                        text = part.text
                        if len(text) > 3000:
                            print(text[:3000])
                            print(f"\n... [truncated {len(text) - 3000} chars]")
                        else:
                            print(text)
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        args_str = str(fc.args)[:100] + "..." if len(str(fc.args)) > 100 else str(fc.args)
                        print(f"\n[TOOL] {fc.name}({args_str})")
                    if hasattr(part, 'function_response') and part.function_response:
                        resp = str(part.function_response)
                        if len(resp) > 300:
                            print(f"[RESULT] {resp[:300]}...")
                        else:
                            print(f"[RESULT] {resp}")

    except asyncio.TimeoutError:
        print(f"\nERROR: Agent execution timed out after {timeout}s")
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
    finally:
        await runner.close()

    print()
    print("=" * 70)
    print("Agent execution complete!")


def main():
    parser = argparse.ArgumentParser(
        description="Run ADK agents with custom prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "agent",
        nargs="?",  # Make optional when using --list
        help="Agent module name (e.g., legal_tech_frontend_specialist)"
    )

    parser.add_argument(
        "--prompt", "-p",
        help="Inline prompt text"
    )

    parser.add_argument(
        "--file", "-f",
        help="Path to prompt file (.md or .txt)"
    )

    parser.add_argument(
        "--model", "-m",
        choices=["gemini-3-pro-preview", "gemini-2.5-flash", "gemini-2.5-pro"],
        help="Override the agent's default model"
    )

    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=600,
        help="Execution timeout in seconds (default: 600)"
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available agents and exit"
    )

    args = parser.parse_args()

    # List agents
    if args.list:
        print("Available agents:")
        for agent in list_agents():
            print(f"  - {agent}")
        return

    # Require agent for non-list operations
    if not args.agent:
        print("ERROR: Must provide agent module name")
        parser.print_help()
        sys.exit(1)

    # Get prompt
    prompt = None
    if args.prompt:
        prompt = args.prompt
    elif args.file:
        prompt_file = Path(args.file)
        if not prompt_file.exists():
            print(f"ERROR: Prompt file not found: {args.file}")
            sys.exit(1)
        prompt = prompt_file.read_text()
    else:
        print("ERROR: Must provide --prompt or --file")
        parser.print_help()
        sys.exit(1)

    # Load and run agent
    agent = load_agent(args.agent, args.model)
    asyncio.run(run_agent(agent, prompt, args.timeout))


if __name__ == "__main__":
    main()
