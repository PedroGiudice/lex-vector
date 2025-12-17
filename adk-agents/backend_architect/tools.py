"""
Custom tools for Backend Architect agent.

These tools enable the agent to:
- Read and analyze code files
- Write architecture documents and code
- Execute commands for validation
- Search and analyze codebases
"""
import subprocess
import json
from pathlib import Path
from typing import Optional
from google.adk.tools import tool


# Project paths
PROJECT_ROOT = Path("/home/user/Claude-Code-Projetos")


@tool
def read_file(file_path: str) -> str:
    """
    Read any file from the project. Use for code, configs, docs, or any text file.

    Args:
        file_path: Relative path from project root or absolute path.
                   Examples: "src/main.py", "docker-compose.yml", "ARCHITECTURE.md"

    Returns:
        File contents as string
    """
    # Try as relative to project root first
    path = PROJECT_ROOT / file_path
    if not path.exists():
        # Try as absolute
        path = Path(file_path)

    if not path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})

    try:
        return path.read_text()
    except Exception as e:
        return json.dumps({"error": f"Failed to read {file_path}: {e}"})


@tool
def write_file(file_path: str, content: str) -> str:
    """
    Write content to any file in the project.
    Creates parent directories if needed.

    Args:
        file_path: Relative path from project root.
                   Examples: "docs/architecture.md", "src/new_service.py"
        content: File contents to write

    Returns:
        Success message or error
    """
    path = PROJECT_ROOT / file_path

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return json.dumps({
            "success": True,
            "path": str(path.relative_to(PROJECT_ROOT)),
            "message": f"File written: {file_path}"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def list_directory(dir_path: str, pattern: str = "*") -> str:
    """
    List files in a directory with optional pattern matching.

    Args:
        dir_path: Directory path relative to project root or absolute
        pattern: Glob pattern to filter files (default: "*")
                 Examples: "*.py", "**/*.ts", "*.md"

    Returns:
        JSON list of file paths
    """
    path = PROJECT_ROOT / dir_path
    if not path.exists():
        path = Path(dir_path)

    if not path.exists():
        return json.dumps({"error": f"Directory not found: {dir_path}"})

    if not path.is_dir():
        return json.dumps({"error": f"Not a directory: {dir_path}"})

    try:
        files = []
        for f in path.glob(pattern):
            rel_path = str(f.relative_to(PROJECT_ROOT)) if f.is_relative_to(PROJECT_ROOT) else str(f)
            files.append({
                "path": rel_path,
                "type": "dir" if f.is_dir() else "file",
                "size": f.stat().st_size if f.is_file() else None
            })
        return json.dumps(files, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def search_code(pattern: str, file_pattern: str = "*.py", directory: str = ".") -> str:
    """
    Search for a pattern in code files using grep.

    Args:
        pattern: Text or regex pattern to search for
        file_pattern: Glob pattern for files to search (default: "*.py")
        directory: Directory to search in (relative to project root)

    Returns:
        JSON with matches: file, line number, content
    """
    search_path = PROJECT_ROOT / directory

    try:
        result = subprocess.run(
            ["grep", "-rn", "--include", file_pattern, pattern, str(search_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        matches = []
        for line in result.stdout.strip().split("\n"):
            if line and ":" in line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    matches.append({
                        "file": parts[0].replace(str(PROJECT_ROOT) + "/", ""),
                        "line": int(parts[1]) if parts[1].isdigit() else parts[1],
                        "content": parts[2].strip()[:200]
                    })

        return json.dumps(matches[:50], indent=2)  # Limit to 50 results
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Search timed out"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def run_command(command: str, working_dir: str = ".") -> str:
    """
    Execute a shell command and return output.
    Use for validation, testing, and analysis tasks.

    Args:
        command: Shell command to execute
        working_dir: Working directory (relative to project root)

    Returns:
        JSON with stdout, stderr, and return code
    """
    work_path = PROJECT_ROOT / working_dir

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(work_path),
            capture_output=True,
            text=True,
            timeout=60,
        )

        return json.dumps({
            "stdout": result.stdout[:10000],  # Limit output
            "stderr": result.stderr[:5000],
            "return_code": result.returncode,
            "success": result.returncode == 0
        }, indent=2)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Command timed out (60s limit)"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def analyze_python_structure(file_path: str) -> str:
    """
    Analyze Python file structure: classes, functions, imports.

    Args:
        file_path: Path to Python file

    Returns:
        JSON with classes, functions, imports found in the file
    """
    import re

    content = read_file(file_path)
    if "error" in content:
        return content

    try:
        result = {
            "file": file_path,
            "imports": [],
            "classes": [],
            "functions": [],
            "async_functions": []
        }

        # Find imports
        import_pattern = r'^(?:from\s+[\w.]+\s+)?import\s+.+$'
        result["imports"] = re.findall(import_pattern, content, re.MULTILINE)

        # Find classes
        class_pattern = r'^class\s+(\w+)(?:\([^)]*\))?:'
        result["classes"] = re.findall(class_pattern, content, re.MULTILINE)

        # Find functions
        func_pattern = r'^def\s+(\w+)\s*\([^)]*\)'
        result["functions"] = re.findall(func_pattern, content, re.MULTILINE)

        # Find async functions
        async_pattern = r'^async\s+def\s+(\w+)\s*\([^)]*\)'
        result["async_functions"] = re.findall(async_pattern, content, re.MULTILINE)

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_directory_tree(dir_path: str, max_depth: int = 3) -> str:
    """
    Get a tree view of directory structure.

    Args:
        dir_path: Directory path to analyze
        max_depth: Maximum depth to traverse (default: 3)

    Returns:
        Tree-like string representation of directory structure
    """
    path = PROJECT_ROOT / dir_path
    if not path.exists():
        path = Path(dir_path)

    if not path.exists():
        return json.dumps({"error": f"Directory not found: {dir_path}"})

    def build_tree(current_path: Path, prefix: str = "", depth: int = 0) -> list:
        if depth > max_depth:
            return []

        items = []
        try:
            entries = sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name))
            # Filter out common noise
            entries = [e for e in entries if e.name not in [
                "__pycache__", ".git", "node_modules", ".venv", "venv",
                ".pytest_cache", ".mypy_cache", "__init__.py"
            ]]

            for i, entry in enumerate(entries[:30]):  # Limit entries
                is_last = i == len(entries) - 1
                connector = "\\u2514\\u2500\\u2500 " if is_last else "\\u251c\\u2500\\u2500 "

                if entry.is_dir():
                    items.append(f"{prefix}{connector}{entry.name}/")
                    extension = "    " if is_last else "\\u2502   "
                    items.extend(build_tree(entry, prefix + extension, depth + 1))
                else:
                    items.append(f"{prefix}{connector}{entry.name}")

        except PermissionError:
            items.append(f"{prefix}[Permission Denied]")

        return items

    tree = [f"{path.name}/"]
    tree.extend(build_tree(path))
    return "\n".join(tree)


@tool
def read_multiple_files(file_paths: str) -> str:
    """
    Read multiple files at once. Useful for analyzing related code.

    Args:
        file_paths: Comma-separated list of file paths
                    Example: "src/main.py,src/utils.py,config.yaml"

    Returns:
        Combined content with file markers
    """
    paths = [p.strip() for p in file_paths.split(",")]
    results = []

    for file_path in paths:
        content = read_file(file_path)
        if "error" not in content:
            results.append(f"\n### FILE: {file_path}\n```\n{content}\n```\n")
        else:
            results.append(f"\n### FILE: {file_path}\n[ERROR: Could not read file]\n")

    return "\n".join(results)
