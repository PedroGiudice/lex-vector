#!/usr/bin/env python3
"""
Test script for Frontend Commander agent.

Validates:
1. Model configuration is correct (per Pyrules)
2. Module structure is valid Python
3. Tool definitions exist

Usage:
    cd adk-agents
    python run_test.py
"""
import sys
import ast
import re
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent


def test_model_names_in_config():
    """Test that config.py has correct model names per Pyrules."""
    print("Testing shared/config.py model names...")

    config_path = PROJECT_ROOT / "shared" / "config.py"
    content = config_path.read_text()

    # Check for correct model name (per Pyrules Dec 2025)
    # Should be gemini-3-pro-preview, NOT gemini-3-pro
    if 'GEMINI_3_PRO = "gemini-3-pro-preview"' in content:
        print("  ✓ GEMINI_3_PRO = 'gemini-3-pro-preview' (correct)")
    elif 'GEMINI_3_PRO = "gemini-3-pro"' in content:
        raise AssertionError(
            "GEMINI_3_PRO should be 'gemini-3-pro-preview', not 'gemini-3-pro'"
        )
    else:
        raise AssertionError("GEMINI_3_PRO not found in config.py")

    # Verify other models are present
    assert 'GEMINI_25_PRO = "gemini-2.5-pro"' in content, "Missing GEMINI_25_PRO"
    assert 'GEMINI_25_FLASH = "gemini-2.5-flash"' in content, "Missing GEMINI_25_FLASH"

    print("  ✓ All model names correct per Pyrules")


def test_requirements_uses_correct_sdk():
    """Test that requirements.txt uses google-genai, not deprecated google-generativeai."""
    print("Testing requirements.txt SDK package...")

    req_path = PROJECT_ROOT / "requirements.txt"
    content = req_path.read_text()

    # Should use google-genai (current SDK per Pyrules)
    if "google-genai" in content:
        print("  ✓ Uses google-genai (current SDK)")
    else:
        raise AssertionError("requirements.txt should include google-genai")

    # Should NOT use deprecated google-generativeai
    if "google-generativeai" in content:
        raise AssertionError(
            "requirements.txt should not use deprecated google-generativeai"
        )

    print("  ✓ No deprecated packages")


def test_agent_module_valid_python():
    """Test that agent.py is valid Python syntax."""
    print("Testing frontend-commander/agent.py syntax...")

    agent_path = PROJECT_ROOT / "frontend-commander" / "agent.py"
    content = agent_path.read_text()

    # Parse as AST to verify syntax
    try:
        ast.parse(content)
        print("  ✓ Valid Python syntax")
    except SyntaxError as e:
        raise AssertionError(f"Syntax error in agent.py: {e}")

    # Verify it uses Config.MODELS.GEMINI_3_PRO (not hardcoded)
    if "Config.MODELS.GEMINI_3_PRO" in content:
        print("  ✓ Uses Config.MODELS.GEMINI_3_PRO (not hardcoded)")
    elif '"gemini-3-pro"' in content or "'gemini-3-pro'" in content:
        # Check if it's in a comment or docstring
        lines_with_model = [l for l in content.split('\n')
                          if 'gemini-3-pro' in l and not l.strip().startswith('#')]
        if any('model=' in l for l in lines_with_model):
            raise AssertionError("agent.py should use Config.MODELS, not hardcoded model")


def test_tools_module_valid_python():
    """Test that tools.py is valid Python and has expected functions."""
    print("Testing frontend-commander/tools.py...")

    tools_path = PROJECT_ROOT / "frontend-commander" / "tools.py"
    content = tools_path.read_text()

    # Parse as AST
    try:
        tree = ast.parse(content)
        print("  ✓ Valid Python syntax")
    except SyntaxError as e:
        raise AssertionError(f"Syntax error in tools.py: {e}")

    # Find all function definitions
    functions = [node.name for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)]

    expected_tools = [
        "list_docker_containers",
        "inspect_container",
        "read_backend_code",
        "read_openapi_spec",
        "list_existing_modules",
        "write_frontend_module",
        "get_service_endpoints",
    ]

    for tool in expected_tools:
        if tool in functions:
            print(f"  ✓ Found tool: {tool}")
        else:
            raise AssertionError(f"Missing tool function: {tool}")


def test_watcher_module_valid_python():
    """Test that watcher.py is valid Python."""
    print("Testing frontend-commander/watcher.py...")

    watcher_path = PROJECT_ROOT / "frontend-commander" / "watcher.py"
    content = watcher_path.read_text()

    try:
        tree = ast.parse(content)
        print("  ✓ Valid Python syntax")
    except SyntaxError as e:
        raise AssertionError(f"Syntax error in watcher.py: {e}")

    # Check for key components
    classes = [node.name for node in ast.walk(tree)
               if isinstance(node, ast.ClassDef)]
    functions = [node.name for node in ast.walk(tree)
                 if isinstance(node, ast.FunctionDef)]

    assert "ContainerState" in classes, "Missing ContainerState class"
    assert "watch_once" in functions, "Missing watch_once function"
    assert "main" in functions, "Missing main function"

    print("  ✓ All key components present")


def test_readme_model_names():
    """Test that README files have correct model names."""
    print("Testing README model names...")

    # Main README
    readme_path = PROJECT_ROOT / "README.md"
    content = readme_path.read_text()

    if "gemini-3-pro-preview" in content:
        print("  ✓ Main README uses gemini-3-pro-preview")
    elif "gemini-3-pro" in content and "gemini-3-pro-preview" not in content:
        raise AssertionError("Main README should use gemini-3-pro-preview")

    # Frontend Commander README
    fc_readme_path = PROJECT_ROOT / "frontend-commander" / "README.md"
    fc_content = fc_readme_path.read_text()

    if "gemini-3-pro-preview" in fc_content:
        print("  ✓ Frontend Commander README uses gemini-3-pro-preview")
    elif "gemini-3-pro" in fc_content and "gemini-3-pro-preview" not in fc_content:
        raise AssertionError("Frontend Commander README should use gemini-3-pro-preview")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Frontend Commander Agent - Test Suite")
    print("="*60)
    print("Validating fixes per Pyrules (Dec 2025)")
    print("="*60 + "\n")

    tests = [
        test_model_names_in_config,
        test_requirements_uses_correct_sdk,
        test_agent_module_valid_python,
        test_tools_module_valid_python,
        test_watcher_module_valid_python,
        test_readme_model_names,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {type(e).__name__}: {e}")
            failed += 1
        print()

    print("="*60)
    if failed == 0:
        print(f"✅ ALL TESTS PASSED ({passed}/{passed})")
    else:
        print(f"❌ {failed} FAILED, {passed} passed")
    print("="*60 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
