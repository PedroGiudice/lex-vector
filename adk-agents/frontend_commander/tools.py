"""
Custom tools for Frontend Commander agent.

These tools enable the agent to:
- Detect and inspect Docker containers
- Read backend source code
- Generate and write frontend code
- Integrate with legal-workbench structure
"""
import subprocess
import json
from pathlib import Path
from typing import Optional
from google.adk.tools import tool


# Project paths
PROJECT_ROOT = Path("/home/user/Claude-Code-Projetos")
LEGAL_WORKBENCH = PROJECT_ROOT / "legal-workbench"
FERRAMENTAS_DIR = LEGAL_WORKBENCH / "ferramentas"
MODULES_DIR = LEGAL_WORKBENCH / "modules"
DOCKER_DIR = LEGAL_WORKBENCH / "docker"


@tool
def list_docker_containers() -> str:
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


@tool
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


@tool
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


@tool
def write_file(file_path: str, content: str) -> str:
    """
    Write content to any file in the project.
    Creates parent directories if needed.

    Args:
        file_path: Relative path from project root.
                   Examples: "legal-workbench/docker-compose.yml", "hub/main.py"
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
def read_backend_code(service_name: str) -> str:
    """
    Read all Python source code from a backend service.

    Searches in:
    - legal-workbench/ferramentas/{service_name}/
    - legal-workbench/docker/services/{service_name}/

    Args:
        service_name: Name of the backend service (e.g., 'stj-api', 'text-extractor')

    Returns:
        Concatenated source code with file markers
    """
    possible_paths = [
        FERRAMENTAS_DIR / service_name,
        DOCKER_DIR / "services" / service_name,
    ]

    code_content = []

    for base_path in possible_paths:
        if not base_path.exists():
            continue

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
        return json.dumps({"error": f"No code found for service: {service_name}"})

    return "\n".join(code_content)


@tool
def read_openapi_spec(service_name: str) -> str:
    """
    Read OpenAPI/Swagger specification from a backend service.

    Args:
        service_name: Name of the backend service

    Returns:
        OpenAPI spec as JSON/YAML string, or error if not found
    """
    possible_paths = [
        FERRAMENTAS_DIR / service_name,
        DOCKER_DIR / "services" / service_name,
    ]

    spec_filenames = ["openapi.json", "openapi.yaml", "swagger.json", "swagger.yaml", "api.json"]

    for base_path in possible_paths:
        if not base_path.exists():
            continue

        for filename in spec_filenames:
            spec_file = base_path / filename
            if spec_file.exists():
                try:
                    return spec_file.read_text()
                except Exception as e:
                    return json.dumps({"error": f"Failed to read {spec_file}: {e}"})

    return json.dumps({"error": f"No OpenAPI spec found for service: {service_name}"})


@tool
def list_existing_modules() -> str:
    """
    List existing UI modules in legal-workbench/modules/.

    Returns:
        JSON with module names and their descriptions
    """
    modules = []

    if MODULES_DIR.exists():
        for py_file in MODULES_DIR.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            module_info = {
                "name": py_file.stem,
                "file": str(py_file.relative_to(LEGAL_WORKBENCH)),
            }

            # Try to extract description from first docstring
            try:
                content = py_file.read_text()
                if '"""' in content:
                    start = content.index('"""') + 3
                    end = content.index('"""', start)
                    module_info["description"] = content[start:end].strip()[:200]
            except:
                pass

            modules.append(module_info)

    return json.dumps(modules, indent=2)


@tool
def write_frontend_module(
    module_name: str,
    code: str,
    module_type: str = "fasthtml",
) -> str:
    """
    Write a new frontend module to legal-workbench.

    Args:
        module_name: Name of the module (e.g., 'stj_viewer')
        code: Complete module code (Python/FastHTML)
        module_type: Type of module ('fasthtml', 'streamlit', 'react')

    Returns:
        Success message with file path, or error
    """
    # Determine target directory based on type
    if module_type == "fasthtml":
        target_dir = LEGAL_WORKBENCH / "poc-fasthtml-stj" / "components"
    elif module_type == "streamlit":
        target_dir = MODULES_DIR
    elif module_type == "react":
        target_dir = LEGAL_WORKBENCH / "poc-react-stj" / "src" / "components"
    else:
        return json.dumps({"error": f"Unknown module_type: {module_type}"})

    # Ensure directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Determine file extension
    ext = ".tsx" if module_type == "react" else ".py"
    target_file = target_dir / f"{module_name}{ext}"

    try:
        target_file.write_text(code)
        return json.dumps({
            "success": True,
            "path": str(target_file.relative_to(PROJECT_ROOT)),
            "message": f"Module {module_name} created successfully",
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


@tool
def get_service_endpoints(service_name: str) -> str:
    """
    Extract API endpoints from a backend service by analyzing its code.

    Looks for Flask/FastAPI route decorators.

    Args:
        service_name: Name of the backend service

    Returns:
        JSON with detected endpoints: method, path, function name
    """
    import re

    code = read_backend_code(service_name)
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
