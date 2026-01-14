import os
import re

def scan_repo_for_routes(repo_path: str) -> list[str]:
    """
    Scans a React repository for potential route definitions.
    
    Args:
        repo_path: Path to the root of the React project.
        
    Returns:
        list[str]: A list of potential route paths found (e.g., ["/login", "/users/:id"])
    """
    routes = set()
    
    if not os.path.exists(repo_path):
        return ["Error: Repo path does not exist."]
        
    # Regex patterns for common React Router definitions
    patterns = [
        r'path=["\"]([^"\"]+)["\"]',       # <Route path="/login" ... />
        r'path:\s*["\"]([^"\"]+)["\"]',    # path: "/login" (in objects)
    ]
    
    try:
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Basic check if it looks like a router file
                            if 'Router' in content or 'Route' in content:
                                for pattern in patterns:
                                    matches = re.findall(pattern, content)
                                    for match in matches:
                                        # Filter out non-path strings
                                        if match.startswith('/') and not match.startswith('//') and len(match) > 1:
                                            routes.add(match)
                    except Exception:
                        continue
    except Exception as e:
        return [f"Error scanning repo: {str(e)}"]
        
    return sorted(list(routes))