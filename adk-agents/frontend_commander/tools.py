"""
Custom tools for Frontend Commander agent.

These tools enable the agent to:
- Detect and inspect Docker containers
- Read backend source code
- Generate and write frontend code
- Integrate with project structure
- Run npm/bun commands for frontend tooling
- Test APIs and fetch resources
- Analyze and format code
"""
import subprocess
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional
from google.adk.tools.function_tool import FunctionTool


# Project paths - configurable base
PROJECT_ROOT = Path("/home/cmr-auto/claude-work/repos/Claude-Code-Projetos")


def _list_docker_containers() -> str:
    """
    List all running Docker containers with their details.

    Returns:
        JSON string with container info: name, image, ports, status
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return json.dumps({"error": result.stderr})

        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:
                containers.append(json.loads(line))

        return json.dumps(containers, indent=2)

    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Docker command timed out"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def inspect_container(container_name: str) -> str:
    """
    Get detailed information about a specific container.

    Args:
        container_name: Name or ID of the Docker container

    Returns:
        JSON with container configuration, environment, ports, volumes
    """
    try:
        result = subprocess.run(
            ["docker", "inspect", container_name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return json.dumps({"error": result.stderr})

        return result.stdout

    except Exception as e:
        return json.dumps({"error": str(e)})


def read_file(file_path: str) -> str:
    """
    Read any file from the project. Use for docs, plans, configs, or code.

    Args:
        file_path: Relative path from project root or absolute path.
                   Examples: "docs/plans/architecture.md", "docker-compose.yml"

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


def write_file(file_path: str, content: str) -> str:
    """
    Write content to any file in the project.
    Creates parent directories if needed.

    Args:
        file_path: Relative path from project root.
                   Examples: "src/components/MyComponent.tsx", "docker-compose.yml"
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


def read_backend_code(directory: str) -> str:
    """
    Read all Python source code from a directory.

    Args:
        directory: Path to the directory containing backend code

    Returns:
        Concatenated source code with file markers
    """
    base_path = PROJECT_ROOT / directory
    if not base_path.exists():
        base_path = Path(directory)

    if not base_path.exists():
        return json.dumps({"error": f"Directory not found: {directory}"})

    code_content = []

    # Read Python files
    for py_file in base_path.rglob("*.py"):
        # Skip __pycache__ and venv
        if "__pycache__" in str(py_file) or ".venv" in str(py_file):
            continue

        try:
            content = py_file.read_text()
            relative_path = py_file.relative_to(base_path)
            code_content.append(f"### FILE: {relative_path}\n```python\n{content}\n```\n")
        except Exception as e:
            code_content.append(f"### FILE: {py_file} (ERROR: {e})\n")

    # Read requirements.txt if exists
    req_file = base_path / "requirements.txt"
    if req_file.exists():
        try:
            content = req_file.read_text()
            code_content.append(f"### FILE: requirements.txt\n```\n{content}\n```\n")
        except:
            pass

    # Read Dockerfile if exists
    dockerfile = base_path / "Dockerfile"
    if dockerfile.exists():
        try:
            content = dockerfile.read_text()
            code_content.append(f"### FILE: Dockerfile\n```dockerfile\n{content}\n```\n")
        except:
            pass

    if not code_content:
        return json.dumps({"error": f"No code found in: {directory}"})

    return "\n".join(code_content)


def read_openapi_spec(directory: str) -> str:
    """
    Read OpenAPI/Swagger specification from a directory.

    Args:
        directory: Path to the directory containing the spec

    Returns:
        OpenAPI spec as JSON/YAML string, or error if not found
    """
    base_path = PROJECT_ROOT / directory
    if not base_path.exists():
        base_path = Path(directory)

    if not base_path.exists():
        return json.dumps({"error": f"Directory not found: {directory}"})

    spec_filenames = ["openapi.json", "openapi.yaml", "swagger.json", "swagger.yaml", "api.json"]

    for filename in spec_filenames:
        spec_file = base_path / filename
        if spec_file.exists():
            try:
                return spec_file.read_text()
            except Exception as e:
                return json.dumps({"error": f"Failed to read {spec_file}: {e}"})

    return json.dumps({"error": f"No OpenAPI spec found in: {directory}"})


def list_existing_modules(directory: str = "src/components") -> str:
    """
    List existing UI modules/components in a directory.

    Args:
        directory: Path to the directory containing modules (default: src/components)

    Returns:
        JSON with module names and their descriptions
    """
    modules_dir = PROJECT_ROOT / directory
    if not modules_dir.exists():
        return json.dumps({"error": f"Directory not found: {directory}", "modules": []})

    modules = []

    for file in modules_dir.glob("*.*"):
        if file.name.startswith("_") or file.name.startswith("."):
            continue

        module_info = {
            "name": file.stem,
            "file": str(file.relative_to(PROJECT_ROOT)),
            "type": file.suffix,
        }

        # Try to extract description from first docstring/comment
        try:
            content = file.read_text()
            if '"""' in content:
                start = content.index('"""') + 3
                end = content.index('"""', start)
                module_info["description"] = content[start:end].strip()[:200]
            elif "/*" in content:
                start = content.index("/*") + 2
                end = content.index("*/", start)
                module_info["description"] = content[start:end].strip()[:200]
        except:
            pass

        modules.append(module_info)

    return json.dumps(modules, indent=2)


def write_frontend_module(
    file_path: str,
    code: str,
) -> str:
    """
    Write a new frontend module/component to the project.

    Args:
        file_path: Full path where to save the file (e.g., 'src/components/Dashboard.tsx')
        code: Complete module code

    Returns:
        Success message with file path, or error
    """
    target_file = PROJECT_ROOT / file_path

    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(code)
        return json.dumps({
            "success": True,
            "path": str(target_file.relative_to(PROJECT_ROOT)),
            "message": f"Module created: {file_path}",
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_service_endpoints(directory: str) -> str:
    """
    Extract API endpoints from a backend service by analyzing its code.

    Looks for Flask/FastAPI route decorators.

    Args:
        directory: Path to the directory containing backend code

    Returns:
        JSON with detected endpoints: method, path, framework
    """
    code = read_backend_code(directory)
    if "error" in code:
        return code

    endpoints = []

    # FastAPI patterns
    fastapi_pattern = r'@(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
    for match in re.finditer(fastapi_pattern, code, re.IGNORECASE):
        endpoints.append({
            "method": match.group(1).upper(),
            "path": match.group(2),
            "framework": "fastapi",
        })

    # Flask patterns
    flask_pattern = r'@(?:app|bp|blueprint)\.(route|get|post|put|delete)\(["\']([^"\']+)["\']'
    for match in re.finditer(flask_pattern, code, re.IGNORECASE):
        endpoints.append({
            "method": match.group(1).upper() if match.group(1) != "route" else "GET",
            "path": match.group(2),
            "framework": "flask",
        })

    return json.dumps(endpoints, indent=2)


# =============================================================================
# ADVANCED FRONTEND TOOLS
# =============================================================================

def run_npm_command(command: str, working_dir: str = ".") -> str:
    """
    Execute npm, bun, or yarn commands for frontend tooling.

    Args:
        command: The package manager command (e.g., "npm install", "bun add react", "yarn build")
        working_dir: Directory to run the command in (relative to project root)

    Returns:
        JSON with stdout, stderr, and success status
    """
    work_path = PROJECT_ROOT / working_dir

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(work_path),
            capture_output=True,
            text=True,
            timeout=120,  # 2 min timeout for installs
        )

        return json.dumps({
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
            "return_code": result.returncode,
            "success": result.returncode == 0
        }, indent=2)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Command timed out (120s limit)"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def fetch_api(url: str, method: str = "GET", headers: str = "{}", body: str = "") -> str:
    """
    Make HTTP requests to test APIs or fetch resources.

    Args:
        url: The URL to fetch
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: JSON string of headers (e.g., '{"Authorization": "Bearer xxx"}')
        body: Request body for POST/PUT requests

    Returns:
        JSON with status code, headers, and response body
    """
    try:
        headers_dict = json.loads(headers) if headers else {}

        req = urllib.request.Request(url, method=method)
        for key, value in headers_dict.items():
            req.add_header(key, value)

        if body and method in ["POST", "PUT", "PATCH"]:
            req.data = body.encode('utf-8')

        with urllib.request.urlopen(req, timeout=30) as response:
            return json.dumps({
                "status_code": response.status,
                "headers": dict(response.headers),
                "body": response.read().decode('utf-8')[:10000],
                "success": True
            }, indent=2)

    except urllib.error.HTTPError as e:
        return json.dumps({
            "status_code": e.code,
            "error": str(e.reason),
            "body": e.read().decode('utf-8')[:5000] if e.fp else "",
            "success": False
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "success": False})


def run_typescript_check(directory: str = ".") -> str:
    """
    Run TypeScript type checking on a directory.

    Args:
        directory: Directory containing TypeScript files

    Returns:
        JSON with type errors or success message
    """
    work_path = PROJECT_ROOT / directory

    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "--pretty"],
            cwd=str(work_path),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return json.dumps({"success": True, "message": "No type errors found"})
        else:
            return json.dumps({
                "success": False,
                "errors": result.stdout[:5000] + result.stderr[:2000]
            })
    except Exception as e:
        return json.dumps({"error": str(e)})


def format_code(file_path: str, formatter: str = "prettier") -> str:
    """
    Format code using Prettier, ESLint, or Black.

    Args:
        file_path: Path to file to format
        formatter: Which formatter to use (prettier, eslint, black)

    Returns:
        Success message or error
    """
    full_path = PROJECT_ROOT / file_path

    if not full_path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})

    commands = {
        "prettier": ["npx", "prettier", "--write", str(full_path)],
        "eslint": ["npx", "eslint", "--fix", str(full_path)],
        "black": ["python", "-m", "black", str(full_path)],
    }

    cmd = commands.get(formatter)
    if not cmd:
        return json.dumps({"error": f"Unknown formatter: {formatter}"})

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.dumps({
            "success": result.returncode == 0,
            "output": result.stdout[:1000] + result.stderr[:1000]
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def analyze_package_json(directory: str = ".") -> str:
    """
    Analyze package.json to understand project dependencies and scripts.

    Args:
        directory: Directory containing package.json

    Returns:
        JSON with dependencies, devDependencies, and available scripts
    """
    pkg_path = PROJECT_ROOT / directory / "package.json"

    if not pkg_path.exists():
        return json.dumps({"error": "package.json not found", "path": str(pkg_path)})

    try:
        pkg = json.loads(pkg_path.read_text())
        return json.dumps({
            "name": pkg.get("name"),
            "version": pkg.get("version"),
            "scripts": pkg.get("scripts", {}),
            "dependencies": pkg.get("dependencies", {}),
            "devDependencies": pkg.get("devDependencies", {}),
            "type": pkg.get("type", "commonjs"),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def search_npm_packages(query: str, limit: int = 5) -> str:
    """
    Search npm registry for packages.

    Args:
        query: Search query (e.g., "react datepicker")
        limit: Maximum number of results

    Returns:
        JSON with package names, descriptions, and versions
    """
    try:
        url = f"https://registry.npmjs.org/-/v1/search?text={query}&size={limit}"
        req = urllib.request.Request(url)

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            packages = []
            for obj in data.get("objects", []):
                pkg = obj.get("package", {})
                packages.append({
                    "name": pkg.get("name"),
                    "version": pkg.get("version"),
                    "description": pkg.get("description", "")[:200],
                    "keywords": pkg.get("keywords", [])[:5],
                })

            return json.dumps(packages, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def run_linter(directory: str = ".", linter: str = "eslint") -> str:
    """
    Run linting on frontend code.

    Args:
        directory: Directory to lint
        linter: Which linter to use (eslint, biome, stylelint)

    Returns:
        JSON with linting results
    """
    work_path = PROJECT_ROOT / directory

    commands = {
        "eslint": ["npx", "eslint", ".", "--format", "json"],
        "biome": ["npx", "@biomejs/biome", "check", "."],
        "stylelint": ["npx", "stylelint", "**/*.css", "--formatter", "json"],
    }

    cmd = commands.get(linter)
    if not cmd:
        return json.dumps({"error": f"Unknown linter: {linter}"})

    try:
        result = subprocess.run(
            cmd,
            cwd=str(work_path),
            capture_output=True,
            text=True,
            timeout=60,
        )

        return json.dumps({
            "success": result.returncode == 0,
            "output": result.stdout[:8000] if result.stdout else result.stderr[:4000]
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def git_operations(operation: str, args: str = "") -> str:
    """
    Execute git operations for version control.

    Args:
        operation: Git operation (status, diff, add, commit, log, branch)
        args: Additional arguments for the operation

    Returns:
        Git command output
    """
    allowed_ops = ["status", "diff", "add", "log", "branch", "show", "stash"]

    if operation not in allowed_ops:
        return json.dumps({"error": f"Operation not allowed: {operation}. Allowed: {allowed_ops}"})

    try:
        cmd = ["git", operation]
        if args:
            cmd.extend(args.split())

        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )

        return json.dumps({
            "success": result.returncode == 0,
            "output": result.stdout[:10000] if result.stdout else result.stderr[:5000]
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_directory_tree(directory: str = ".", max_depth: int = 3, pattern: str = "*") -> str:
    """
    List directory structure with filtering.

    Args:
        directory: Starting directory
        max_depth: Maximum depth to traverse
        pattern: Glob pattern to filter (e.g., "*.tsx", "*.css")

    Returns:
        Tree structure of matching files
    """
    base_path = PROJECT_ROOT / directory

    if not base_path.exists():
        return json.dumps({"error": f"Directory not found: {directory}"})

    def build_tree(path: Path, depth: int = 0) -> list:
        if depth > max_depth:
            return []

        items = []
        try:
            # Filter out noise
            skip_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".next", "dist", "build"}

            for entry in sorted(path.iterdir()):
                if entry.name in skip_dirs or entry.name.startswith("."):
                    continue

                if entry.is_dir():
                    children = build_tree(entry, depth + 1)
                    if children or pattern == "*":
                        items.append({"name": entry.name + "/", "children": children})
                elif entry.match(pattern):
                    items.append({"name": entry.name, "size": entry.stat().st_size})
        except PermissionError:
            pass

        return items[:50]  # Limit entries

    tree = build_tree(base_path)
    return json.dumps({"root": directory, "tree": tree}, indent=2)


def analyze_component_structure(file_path: str) -> str:
    """
    Analyze a React/Vue/Svelte component structure.

    Args:
        file_path: Path to component file (.tsx, .jsx, .vue, .svelte)

    Returns:
        JSON with imports, exports, props, hooks used, etc.
    """
    full_path = PROJECT_ROOT / file_path

    if not full_path.exists():
        return json.dumps({"error": f"File not found: {file_path}"})

    try:
        content = full_path.read_text()

        analysis = {
            "file": file_path,
            "imports": [],
            "exports": [],
            "hooks": [],
            "components": [],
            "props_interface": None,
        }

        # Find imports
        import_pattern = r"import\s+(?:{[^}]+}|\w+)\s+from\s+['\"]([^'\"]+)['\"]"
        analysis["imports"] = re.findall(import_pattern, content)

        # Find React hooks
        hooks_pattern = r"use[A-Z]\w+(?=\s*\()"
        analysis["hooks"] = list(set(re.findall(hooks_pattern, content)))

        # Find component definitions
        component_pattern = r"(?:function|const)\s+([A-Z]\w+)\s*(?:=|:|\()"
        analysis["components"] = re.findall(component_pattern, content)

        # Find Props interface/type
        props_pattern = r"(?:interface|type)\s+(\w*Props)\s*[={]"
        props_match = re.search(props_pattern, content)
        if props_match:
            analysis["props_interface"] = props_match.group(1)

        # Find exports
        export_pattern = r"export\s+(?:default\s+)?(?:function|const|class)\s+(\w+)"
        analysis["exports"] = re.findall(export_pattern, content)

        return json.dumps(analysis, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# FunctionTool Wrappers
# =============================================================================

list_docker_containers = FunctionTool(func=_list_docker_containers)
inspect_container = FunctionTool(func=inspect_container)
read_file = FunctionTool(func=read_file)
write_file = FunctionTool(func=write_file)
read_backend_code = FunctionTool(func=read_backend_code)
read_openapi_spec = FunctionTool(func=read_openapi_spec)
list_existing_modules = FunctionTool(func=list_existing_modules)
write_frontend_module = FunctionTool(func=write_frontend_module)
get_service_endpoints = FunctionTool(func=get_service_endpoints)
run_npm_command = FunctionTool(func=run_npm_command)
fetch_api = FunctionTool(func=fetch_api)
run_typescript_check = FunctionTool(func=run_typescript_check)
format_code = FunctionTool(func=format_code)
analyze_package_json = FunctionTool(func=analyze_package_json)
search_npm_packages = FunctionTool(func=search_npm_packages)
run_linter = FunctionTool(func=run_linter)
git_operations = FunctionTool(func=git_operations)
list_directory_tree = FunctionTool(func=list_directory_tree)
analyze_component_structure = FunctionTool(func=analyze_component_structure)


__all__ = [
    "list_docker_containers",
    "inspect_container",
    "read_file",
    "write_file",
    "read_backend_code",
    "read_openapi_spec",
    "list_existing_modules",
    "write_frontend_module",
    "get_service_endpoints",
    "run_npm_command",
    "fetch_api",
    "run_typescript_check",
    "format_code",
    "analyze_package_json",
    "search_npm_packages",
    "run_linter",
    "git_operations",
    "list_directory_tree",
    "analyze_component_structure",
]
