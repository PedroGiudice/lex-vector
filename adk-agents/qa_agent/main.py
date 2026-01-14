import os
import sys
import argparse
from dotenv import load_dotenv
from google.genai.errors import ClientError

# Add the parent directory to sys.path to allow importing from the package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa_agent.agent import qa_agent

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Run QA Architect Agent")
    parser.add_argument("url", help="Target URL of the application to test")
    parser.add_argument("--repo", help="Path to the local repository (optional)", default=None)
    args = parser.parse_args()
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set.")
        sys.exit(1)
        
    print(f"--- QA Architect Agent Initialized ---")
    print(f"Target: {args.url}")
    if args.repo:
        print(f"Repo: {args.repo}")
        
    prompt = f"Conduct a QA assessment of the application at {args.url}."
    if args.repo:
        prompt += f" The source code is located at {args.repo}. Use 'scan_repo_for_routes' to discover paths."
        
    prompt += " Create and execute E2E tests for the main flows you discover. Report failures immediately."
    
    print("\nThinking and Executing... (This may take a minute)\n")
    
    try:
        # Use the generate_content method directly on the model
        response = qa_agent.model.generate_content(
            contents=prompt,
            config={'tools': qa_agent.tools}
        )
        
        print("\n--- QA REPORT ---\
")
        print(response.text)
        
        # Save report
        report_path = os.path.join(os.path.dirname(__file__), "reports", "latest_report.md")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"\nReport saved to: {report_path}")
        
    except Exception as e:
        print(f"\nError during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
