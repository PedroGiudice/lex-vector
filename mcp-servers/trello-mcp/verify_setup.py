#!/usr/bin/env python3
"""
Standalone validation script to test Trello connection BEFORE hooking up to Claude.

This script:
1. Validates environment variables
2. Tests Trello API authentication
3. Attempts to fetch user boards
4. Reports success/failure with actionable feedback

Run this BEFORE configuring Claude to ensure credentials work.

Usage:
    python verify_setup.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models import EnvironmentSettings
from src.trello_client import TrelloClient, TrelloAuthError, TrelloAPIError
from pydantic import ValidationError


async def main() -> int:
    """
    Main validation logic.

    Returns:
        0 on success, 1 on failure
    """
    print("=" * 70)
    print("Trello MCP Server - Setup Validation")
    print("=" * 70)
    print()

    # Step 1: Validate environment variables
    print("Step 1: Validating environment variables...")
    try:
        settings = EnvironmentSettings()
        print("✓ Environment variables loaded successfully")
        print(f"  - API Key: {settings.trello_api_key[:8]}...{settings.trello_api_key[-4:]}")
        print(f"  - Token:   {settings.trello_api_token[:8]}...{settings.trello_api_token[-4:]}")
        print(f"  - Log Level: {settings.log_level}")
        print(f"  - Rate Limit: {settings.rate_limit_per_10_seconds} req/10s")
        print()
    except ValidationError as e:
        print("✗ Environment validation failed!")
        print()
        print("Missing or invalid environment variables:")
        for error in e.errors():
            field = error["loc"][0]
            msg = error["msg"]
            print(f"  - {field}: {msg}")
        print()
        print("Action required:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in your Trello credentials from https://trello.com/power-ups/admin")
        print("  3. Run this script again")
        return 1

    # Step 2: Test API connection
    print("Step 2: Testing Trello API connection...")
    try:
        async with TrelloClient(settings) as client:
            user_info = await client.validate_credentials()
            print("✓ Authentication successful!")
            print(f"  - User ID: {user_info.get('id')}")
            print(f"  - Username: @{user_info.get('username')}")
            print(f"  - Full Name: {user_info.get('fullName')}")
            print()

            # Step 3: Fetch user boards (optional but helpful)
            print("Step 3: Fetching your Trello boards...")
            try:
                # This is a bonus check - list available boards
                boards_data = await client._request("GET", "/members/me/boards?fields=id,name,url")
                print(f"✓ Found {len(boards_data)} board(s):")
                for board in boards_data[:5]:  # Show first 5
                    print(f"  - {board['name']} (ID: {board['id']})")
                    print(f"    URL: {board['url']}")
                if len(boards_data) > 5:
                    print(f"  ... and {len(boards_data) - 5} more")
                print()
            except TrelloAPIError as e:
                print(f"⚠ Could not fetch boards (non-critical): {e}")
                print()

    except TrelloAuthError as e:
        print("✗ Authentication failed!")
        print(f"  Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Verify your API Key at https://trello.com/power-ups/admin")
        print("  2. Regenerate your Token (ensure it's set to 'never expire')")
        print("  3. Check that .env file has correct TRELLO_API_KEY and TRELLO_API_TOKEN")
        return 1

    except TrelloAPIError as e:
        print("✗ API connection failed!")
        print(f"  Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check your internet connection")
        print("  2. Verify Trello API is accessible (try visiting https://api.trello.com/1/)")
        print("  3. Check if your organization has firewall rules blocking Trello")
        return 1

    except Exception as e:
        print("✗ Unexpected error!")
        print(f"  Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1

    # Success!
    print("=" * 70)
    print("✓ ALL CHECKS PASSED")
    print("=" * 70)
    print()
    print("Your Trello MCP server is ready to use!")
    print()
    print("Next steps:")
    print("  1. Configure Claude Desktop (see configs/claude_desktop_config.json)")
    print("  2. Or configure Claude Code CLI (see configs/claude_code_cli_setup.md)")
    print("  3. Restart Claude")
    print("  4. Test with: 'List my Trello boards'")
    print()
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
