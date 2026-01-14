import os
import subprocess
import sys

def run_api_script(script_name: str, script_code: str) -> dict:
    """
    Saves and executes a Python API test script (using requests/pytest).
    
    Args:
        script_name: Name of the script (e.g., 'test_api_users').
        script_code: The full Python code.
        
    Returns:
        dict: {
            "status": "success" | "error",
            "output": str,
            "error": str,
            "script_path": str
        }
    """
    # Define paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "tests_generated", "api")
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure script_name ends with .py
    if not script_name.endswith(".py"):
        script_name += ".py"
        
    script_path = os.path.join(output_dir, script_name)
    
    # Write the script
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_code)
        
    # Execute the script
    try:
        # Run with the current python interpreter
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30  # 30s timeout for API tests
        )
        
        status = "success" if result.returncode == 0 else "error"
        
        return {
            "status": status,
            "output": result.stdout,
            "error": result.stderr,
            "script_path": script_path
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "output": "",
            "error": "Script execution timed out after 30 seconds.",
            "script_path": script_path
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "error": str(e),
            "script_path": script_path
        }
