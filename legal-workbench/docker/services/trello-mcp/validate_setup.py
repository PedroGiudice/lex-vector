#!/usr/bin/env python3
"""
Validation script for Trello MCP API setup.

Checks:
1. Environment variables
2. File structure
3. Dependencies
4. Trello API connectivity
5. Docker configuration
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# ANSI colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


class ValidationError(Exception):
    """Validation error."""
    pass


class Validator:
    """Setup validation orchestrator."""

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checks_passed = 0
        self.checks_failed = 0

    def check(self, name: str, func) -> bool:
        """Run a validation check."""
        try:
            print(f"Checking: {name} ... ", end="", flush=True)
            func()
            print(f"{GREEN}✓ PASSED{NC}")
            self.checks_passed += 1
            return True
        except ValidationError as e:
            print(f"{RED}✗ FAILED{NC}")
            self.errors.append(f"{name}: {str(e)}")
            self.checks_failed += 1
            return False
        except Exception as e:
            print(f"{RED}✗ ERROR{NC}")
            self.errors.append(f"{name}: Unexpected error - {str(e)}")
            self.checks_failed += 1
            return False

    def warn(self, message: str):
        """Add a warning."""
        self.warnings.append(message)

    def summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Passed:   {GREEN}{self.checks_passed}{NC}")
        print(f"Failed:   {RED}{self.checks_failed}{NC}")
        print(f"Warnings: {YELLOW}{len(self.warnings)}{NC}")
        print(f"Total:    {self.checks_passed + self.checks_failed}")

        if self.warnings:
            print(f"\n{YELLOW}Warnings:{NC}")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        if self.errors:
            print(f"\n{RED}Errors:{NC}")
            for error in self.errors:
                print(f"  ✗ {error}")

        print()

        if self.checks_failed == 0:
            print(f"{GREEN}✓ All checks passed! Ready to deploy.{NC}")
            return 0
        else:
            print(f"{RED}✗ {self.checks_failed} check(s) failed. Fix errors before deploying.{NC}")
            return 1


def check_python_version():
    """Check Python version is 3.11+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        raise ValidationError(f"Python 3.11+ required, found {version.major}.{version.minor}")


def check_project_structure():
    """Check required files and directories exist."""
    base_dir = Path(__file__).parent

    required_files = [
        "api/__init__.py",
        "api/main.py",
        "api/models.py",
        "Dockerfile",
        "requirements.txt",
        "README.md",
    ]

    missing = []
    for file in required_files:
        if not (base_dir / file).exists():
            missing.append(file)

    if missing:
        raise ValidationError(f"Missing files: {', '.join(missing)}")


def check_env_variables():
    """Check required environment variables."""
    # Try to load from .env file
    env_file = Path(__file__).parent.parent.parent / ".env"

    if not env_file.exists():
        raise ValidationError(
            f".env file not found at {env_file}. "
            "Copy .env.example to .env and configure."
        )

    # Parse .env file
    env_vars = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

    # Check required variables
    required = ["TRELLO_API_KEY", "TRELLO_API_TOKEN"]
    missing = [var for var in required if not env_vars.get(var)]

    if missing:
        raise ValidationError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    # Validate format
    api_key = env_vars.get("TRELLO_API_KEY", "")
    if len(api_key) < 32:
        raise ValidationError("TRELLO_API_KEY seems too short (expected 32+ chars)")

    api_token = env_vars.get("TRELLO_API_TOKEN", "")
    if len(api_token) < 64:
        raise ValidationError("TRELLO_API_TOKEN seems too short (expected 64+ chars)")


def check_dependencies():
    """Check Python dependencies are installable."""
    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        raise ValidationError("requirements.txt not found")

    # Read requirements
    with open(requirements_file) as f:
        packages = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

    if len(packages) < 5:
        raise ValidationError(
            f"Expected at least 5 dependencies, found {len(packages)}"
        )

    # Check critical packages
    critical = ["fastapi", "uvicorn", "pydantic", "httpx", "slowapi"]
    requirements_text = " ".join(packages)

    missing = [pkg for pkg in critical if pkg not in requirements_text]
    if missing:
        raise ValidationError(f"Critical packages missing: {', '.join(missing)}")


def check_docker():
    """Check Docker is installed and running."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        if "Docker version" not in result.stdout:
            raise ValidationError("Docker not properly installed")
    except FileNotFoundError:
        raise ValidationError("Docker not found in PATH")
    except subprocess.CalledProcessError as e:
        raise ValidationError(f"Docker error: {e.stderr}")


def check_docker_compose():
    """Check Docker Compose is available."""
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        if "docker-compose version" not in result.stdout.lower():
            raise ValidationError("Docker Compose not properly installed")
    except FileNotFoundError:
        raise ValidationError("Docker Compose not found in PATH")
    except subprocess.CalledProcessError as e:
        raise ValidationError(f"Docker Compose error: {e.stderr}")


def check_port_availability():
    """Check if port 8004 is available."""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 8004))
        sock.close()

        if result == 0:
            raise ValidationError(
                "Port 8004 is already in use. Stop the conflicting service."
            )
    except socket.error as e:
        # Port is available (connection refused is expected)
        if "Connection refused" not in str(e):
            raise ValidationError(f"Socket error: {e}")


def check_trello_connectivity():
    """Check Trello API connectivity (optional - requires credentials)."""
    env_file = Path(__file__).parent.parent.parent / ".env"

    if not env_file.exists():
        raise ValidationError("Cannot test connectivity without .env file")

    # Parse credentials
    env_vars = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    api_key = env_vars.get("TRELLO_API_KEY")
    api_token = env_vars.get("TRELLO_API_TOKEN")

    if not api_key or not api_token:
        raise ValidationError("Credentials not configured in .env")

    # Test API call
    try:
        import httpx

        url = f"https://api.trello.com/1/members/me?key={api_key}&token={api_token}"
        response = httpx.get(url, timeout=10)

        if response.status_code == 401:
            raise ValidationError("Invalid Trello credentials (401 Unauthorized)")
        elif response.status_code == 403:
            raise ValidationError("Trello access forbidden (403)")
        elif response.status_code != 200:
            raise ValidationError(f"Trello API error (HTTP {response.status_code})")

        user_data = response.json()
        print(f"    (Authenticated as: {user_data.get('fullName', 'Unknown')})", end=" ")

    except httpx.RequestError as e:
        raise ValidationError(f"Network error: {e}")
    except ImportError:
        # httpx not installed yet - skip this check
        print(f"{YELLOW}SKIPPED{NC} (httpx not installed)")
        return


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("TRELLO MCP API - SETUP VALIDATION")
    print("=" * 60)
    print()

    validator = Validator()

    # Environment checks
    print(f"{BLUE}1. ENVIRONMENT CHECKS{NC}")
    print("-" * 60)
    validator.check("Python version", check_python_version)
    validator.check("Project structure", check_project_structure)
    validator.check("Environment variables", check_env_variables)
    print()

    # Dependency checks
    print(f"{BLUE}2. DEPENDENCY CHECKS{NC}")
    print("-" * 60)
    validator.check("Dependencies list", check_dependencies)
    print()

    # Docker checks
    print(f"{BLUE}3. DOCKER CHECKS{NC}")
    print("-" * 60)
    validator.check("Docker installed", check_docker)
    validator.check("Docker Compose installed", check_docker_compose)
    validator.check("Port 8004 available", check_port_availability)
    print()

    # Connectivity checks
    print(f"{BLUE}4. CONNECTIVITY CHECKS{NC}")
    print("-" * 60)
    validator.check("Trello API connectivity", check_trello_connectivity)
    print()

    # Summary
    exit_code = validator.summary()

    if exit_code == 0:
        print(f"\n{GREEN}Next steps:{NC}")
        print("  1. Build the Docker image:  make build")
        print("  2. Start the service:       make up")
        print("  3. Run tests:               make test")
        print("  4. Open API docs:           http://localhost:8004/docs")
        print()

    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Validation interrupted{NC}")
        sys.exit(130)
