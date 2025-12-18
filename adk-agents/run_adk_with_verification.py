#!/usr/bin/env python3
"""
ADK + Claude Visual Verification Workflow

Orchestrates the ADK agent to generate/modify frontend code,
then uses Playwright to capture snapshots/screenshots for verification.

Usage:
    # Interactive mode (recommended) - uses snapshot by default
    python run_adk_with_verification.py --task "Adjust sidebar width to 20%"

    # With visual screenshot for color/layout verification
    python run_adk_with_verification.py --task "..." --visual

    # With spec file
    python run_adk_with_verification.py --spec layout_spec.md --task "Apply layout spec"

    # Full auto mode (max iterations)
    python run_adk_with_verification.py --task "..." --max-iterations 5

Architecture:
    Claude Code (Orchestrator) → ADK Agent (Gemini)
           ↓                           ↓
       Playwright verify          write_file()
           ↓                           ↓
       Snapshot/Screenshot ←─ rebuild ←── Frontend React
"""
import os
import sys
import asyncio
import argparse
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Project paths
PROJECT_ROOT = Path(__file__).parent
FRONTEND_PATH = PROJECT_ROOT.parent / "legal-workbench" / "frontend"
SCREENSHOTS_DIR = PROJECT_ROOT / "verification_screenshots"
SPECS_DIR = PROJECT_ROOT / "layout_specs"

# Ensure directories exist
SCREENSHOTS_DIR.mkdir(exist_ok=True)
SPECS_DIR.mkdir(exist_ok=True)

# Load environment
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


class LayoutSpec:
    """Design specification for the layout."""

    DEFAULT_SPEC = """
# Doc Assembler Layout Specification

## Visual Style
- **Inspiration**: VS Code, Obsidian, Claude Desktop, GitHub
- **Theme**: Dark mode with subtle glass effects
- **Style Mix**: Brutalism (clean geometric forms, bold typography) + Glassmorphism (blur overlays, subtle transparency)
- **UX Priority**: Seamless, intuitive interaction - decorative elements welcome when they enhance usability

## Color Palette
- **Background (Main)**: #1e1e2e (VS Code dark)
- **Background (Sidebar)**: #181825 (slightly darker)
- **Background (Doc Viewer)**: #f5f5f5 or #ffffff (paper-like, toggleable)
- **Borders**: #3f3f46 (1px subtle dividers)
- **Text Primary**: #e4e4e7
- **Text Secondary**: #a1a1aa

## Layout Structure
- **Columns**: 20-60-20 (sidebars collapsible/resizable)
- **Header**: Minimal (icons only, no full header bar)
- **Sidebar Left**: Collapsible tabs (Upload, Templates, How to Use)
- **Main**: Document viewer with paper-like background
- **Sidebar Right**: Annotations panel

## Typography
- **UI Font**: Inter, system-ui
- **Document Font**: JetBrains Mono, Fira Code (monospace)
- **Headings**: Bold, geometric

## Interaction
- **Dividers**: 1px border with drag handle for resize
- **Annotations**: Vibrant highlight (yellow/cyan) for visibility
- **Hover**: Subtle brightness increase

## Responsive
- **Mobile**: Stack sidebars below main content
- **Tablet**: Collapse left sidebar to icons
"""

    def __init__(self, spec_text: Optional[str] = None):
        self.spec = spec_text or self.DEFAULT_SPEC

    @classmethod
    def from_file(cls, path: Path) -> "LayoutSpec":
        return cls(path.read_text())

    def to_prompt_context(self) -> str:
        return f"""
## LAYOUT SPECIFICATION (MUST FOLLOW)

{self.spec}

## IMPORTANT RULES
1. Follow the spec EXACTLY - colors, proportions, typography
2. Use Tailwind CSS classes where possible
3. Ensure dark mode is properly applied
4. Test responsiveness mentally before writing code
5. Preserve existing functionality - only change styling/layout
"""


async def run_adk_agent(prompt: str, timeout: int = 600) -> dict:
    """
    Execute the ADK agent with the given prompt.
    Returns execution result with modified files.
    """
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "run_agent.py"),
        "legal_tech_frontend_specialist",
        "--prompt", prompt,
        "--timeout", str(timeout)
    ]

    print("\n" + "=" * 70)
    print("ADK AGENT EXECUTION")
    print("=" * 70)
    print(f"Prompt preview: {prompt[:200]}...")
    print("-" * 70)

    start_time = time.time()

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(PROJECT_ROOT)
    )

    stdout, stderr = await asyncio.wait_for(
        process.communicate(),
        timeout=timeout + 30
    )

    elapsed = time.time() - start_time

    result = {
        "success": process.returncode == 0,
        "stdout": stdout.decode() if stdout else "",
        "stderr": stderr.decode() if stderr else "",
        "elapsed_seconds": round(elapsed, 2),
        "return_code": process.returncode
    }

    print(f"\nExecution completed in {elapsed:.1f}s")
    print(f"Return code: {process.returncode}")

    if result["stdout"]:
        # Show last 1000 chars of output
        output = result["stdout"]
        if len(output) > 1000:
            print(f"\n... [truncated {len(output) - 1000} chars] ...")
            print(output[-1000:])
        else:
            print(output)

    if result["stderr"]:
        print(f"\nSTDERR:\n{result['stderr'][:500]}")

    return result


def capture_snapshot_sync(url: str, output_path: Path, wait_seconds: int = 3) -> tuple[bool, str]:
    """
    Capture accessibility snapshot using playwright (for debugging).
    Returns (success, snapshot_text).
    """
    # Use playwright to get accessibility tree via script
    script = f"""
const {{ chromium }} = require('playwright');
(async () => {{
    const browser = await chromium.launch();
    const page = await browser.newPage();
    await page.goto('{url}');
    await page.waitForTimeout({wait_seconds * 1000});
    const snapshot = await page.accessibility.snapshot();
    console.log(JSON.stringify(snapshot, null, 2));
    await browser.close();
}})();
"""

    try:
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT.parent)
        )

        if result.returncode == 0 and result.stdout:
            output_path.write_text(result.stdout)
            print(f"Snapshot saved: {output_path}")
            return True, result.stdout
        else:
            # Fallback: just save page info
            print(f"Snapshot via node failed, using simple fetch")
            return False, ""

    except Exception as e:
        print(f"Snapshot error: {e}")
        return False, ""


def capture_screenshot_sync(url: str, output_path: Path, wait_seconds: int = 3) -> bool:
    """
    Capture screenshot using playwright CLI (for visual verification).
    """
    cmd = [
        "npx", "playwright", "screenshot",
        "--browser", "chromium",
        "--full-page",
        "--wait-for-timeout", str(wait_seconds * 1000),
        url,
        str(output_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(PROJECT_ROOT.parent)
        )

        if result.returncode == 0 and output_path.exists():
            print(f"Screenshot saved: {output_path}")
            return True
        else:
            print(f"Screenshot failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("Screenshot timed out")
        return False
    except Exception as e:
        print(f"Screenshot error: {e}")
        return False


def build_adk_prompt(task: str, spec: LayoutSpec, iteration: int, previous_feedback: Optional[str] = None) -> str:
    """
    Build a prompt for the ADK agent including spec and context.
    """
    context = f"""
# Frontend Layout Task (Iteration {iteration})

## Project Context
- Framework: React 18 + TypeScript + Vite
- Styling: Tailwind CSS
- State: Zustand
- Location: legal-workbench/frontend/src/

## Current Task
{task}

{spec.to_prompt_context()}
"""

    if previous_feedback:
        context += f"""

## Previous Iteration Feedback
The following issues were identified in the previous iteration:
{previous_feedback}

Please address ALL issues listed above.
"""

    context += """

## Instructions
1. Read the relevant component files first
2. Make targeted changes following the spec
3. Preserve existing functionality
4. Write clean, maintainable code
5. Use semantic HTML and accessibility attributes

## Expected Output
Modify the necessary files to implement the layout changes.
After modifications, summarize what was changed.
"""

    return context


def wait_for_rebuild(seconds: int = 5):
    """Wait for Vite hot reload to complete."""
    print(f"\nWaiting {seconds}s for Vite hot reload...")
    time.sleep(seconds)


def generate_verification_report(
    task: str,
    iteration: int,
    screenshot_path: Path,
    adk_result: dict
) -> dict:
    """
    Generate a report for Claude to review.
    """
    return {
        "task": task,
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "screenshot": str(screenshot_path),
        "adk_success": adk_result["success"],
        "adk_elapsed": adk_result["elapsed_seconds"],
        "output_preview": adk_result["stdout"][-500:] if adk_result["stdout"] else "",
        "review_prompt": f"""
## Visual Verification Required

Screenshot captured: {screenshot_path}

Task: {task}
Iteration: {iteration}

Please review the screenshot and provide feedback:
1. Does the layout match the specification?
2. Are colors correct (dark mode, proper contrast)?
3. Are proportions correct (20-60-20 columns)?
4. Is typography correct (monospace for doc, clean UI fonts)?
5. Any visual issues or bugs?

If issues found, describe them clearly for the next iteration.
If everything looks good, confirm completion.
"""
    }


async def run_verification_loop(
    task: str,
    spec: LayoutSpec,
    url: str = "http://localhost/app",
    max_iterations: int = 3,
    auto_mode: bool = False,
    visual_mode: bool = False
) -> dict:
    """
    Main verification loop:
    1. Run ADK agent
    2. Wait for rebuild
    3. Capture screenshot
    4. Generate report (for Claude review)
    5. Loop if needed
    """
    results = []

    for iteration in range(1, max_iterations + 1):
        print(f"\n{'=' * 70}")
        print(f"ITERATION {iteration} of {max_iterations}")
        print("=" * 70)

        # Get feedback from previous iteration
        previous_feedback = results[-1].get("feedback") if results else None

        # Build prompt
        prompt = build_adk_prompt(task, spec, iteration, previous_feedback)

        # Run ADK agent
        adk_result = await run_adk_agent(prompt)

        if not adk_result["success"]:
            print("\nADK agent failed. Check output above.")
            results.append({
                "iteration": iteration,
                "status": "adk_failed",
                "adk_result": adk_result
            })
            break

        # Wait for rebuild
        wait_for_rebuild(5)

        # Capture snapshot (default) or screenshot (--visual)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if visual_mode:
            # Screenshot for visual verification
            capture_path = SCREENSHOTS_DIR / f"iter_{iteration}_{timestamp}.png"
            capture_success = capture_screenshot_sync(url, capture_path)
            snapshot_text = ""
        else:
            # Snapshot for debugging (default)
            capture_path = SCREENSHOTS_DIR / f"iter_{iteration}_{timestamp}_snapshot.json"
            capture_success, snapshot_text = capture_snapshot_sync(url, capture_path)

        if not capture_success:
            print(f"\n{'Screenshot' if visual_mode else 'Snapshot'} capture failed.")
            results.append({
                "iteration": iteration,
                "status": "capture_failed",
                "adk_result": adk_result
            })
            continue

        # Generate report
        report = generate_verification_report(task, iteration, capture_path, adk_result)
        if snapshot_text:
            report["snapshot_preview"] = snapshot_text[:2000]  # First 2k chars for quick review

        print("\n" + "-" * 70)
        print("VERIFICATION REPORT")
        print("-" * 70)
        print(report["review_prompt"])

        results.append({
            "iteration": iteration,
            "status": "completed",
            "report": report,
            "capture_path": str(capture_path),
            "mode": "visual" if visual_mode else "snapshot"
        })

        if auto_mode and iteration < max_iterations:
            # In auto mode, continue unless last iteration
            continue
        else:
            # Interactive mode: stop for review
            print("\n" + "=" * 70)
            print("REVIEW REQUIRED")
            print("=" * 70)
            print(f"Capture: {capture_path}")
            mode_hint = "Review screenshot visually" if visual_mode else "Review snapshot structure"
            print(f"\n{mode_hint} in Claude Code.")
            print("The loop will pause here for manual verification.")
            break

    return {
        "task": task,
        "total_iterations": len(results),
        "results": results,
        "final_capture": results[-1].get("capture_path") if results else None,
        "mode": "visual" if visual_mode else "snapshot"
    }


def main():
    parser = argparse.ArgumentParser(
        description="ADK + Visual Verification Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--task", "-t",
        required=True,
        help="Layout task to execute (e.g., 'Adjust sidebar to 20%')"
    )

    parser.add_argument(
        "--spec", "-s",
        help="Path to layout spec file (uses default if not provided)"
    )

    parser.add_argument(
        "--url", "-u",
        default="http://localhost/app",
        help="Frontend URL to capture (default: http://localhost/app)"
    )

    parser.add_argument(
        "--max-iterations", "-i",
        type=int,
        default=3,
        help="Maximum verification iterations (default: 3)"
    )

    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto mode: run all iterations without stopping for review"
    )

    parser.add_argument(
        "--visual",
        action="store_true",
        help="Use screenshot instead of snapshot (for color/layout verification)"
    )

    parser.add_argument(
        "--save-spec",
        action="store_true",
        help="Save the default spec to a file and exit"
    )

    args = parser.parse_args()

    # Save default spec if requested
    if args.save_spec:
        spec_path = SPECS_DIR / "default_layout_spec.md"
        spec_path.write_text(LayoutSpec.DEFAULT_SPEC)
        print(f"Default spec saved to: {spec_path}")
        return

    # Load spec
    if args.spec:
        spec_path = Path(args.spec)
        if not spec_path.exists():
            print(f"ERROR: Spec file not found: {args.spec}")
            sys.exit(1)
        spec = LayoutSpec.from_file(spec_path)
    else:
        spec = LayoutSpec()

    # Run verification loop
    print("\n" + "=" * 70)
    print("ADK + VERIFICATION WORKFLOW")
    print("=" * 70)
    print(f"Task: {args.task}")
    print(f"URL: {args.url}")
    print(f"Max iterations: {args.max_iterations}")
    print(f"Mode: {'Visual (screenshot)' if args.visual else 'Debug (snapshot)'}")
    print(f"Auto mode: {args.auto}")

    result = asyncio.run(run_verification_loop(
        task=args.task,
        spec=spec,
        url=args.url,
        max_iterations=args.max_iterations,
        auto_mode=args.auto,
        visual_mode=args.visual
    ))

    # Save final report
    report_path = SCREENSHOTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(result, indent=2))
    print(f"\nFinal report saved: {report_path}")

    if result["final_capture"]:
        print(f"Final capture: {result['final_capture']}")


if __name__ == "__main__":
    main()
