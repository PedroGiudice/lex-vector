"""
MCP Bridge for ADK Agents

Allows ADK agents to use MCP server tools (like Chrome DevTools, Playwright, etc.)
by bridging MCP protocol to Gemini function calling format.

Usage:
    async with GeminiMCPBridge(command="npx", args=["@anthropic/mcp-server-chrome-devtools"]) as bridge:
        tools = await bridge.get_tools_for_gemini()
        # Pass tools to Gemini agent
        # When Gemini returns function_call, execute with bridge.execute_tool()
"""
import asyncio
import json
from typing import Optional, Any
from contextlib import asynccontextmanager

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: mcp package not installed. Run: pip install mcp")

from google.genai import types


class GeminiMCPBridge:
    """Bridge between MCP servers and Gemini function calling."""

    def __init__(self, command: str = "npx", args: Optional[list] = None, env: Optional[dict] = None):
        """
        Initialize the MCP bridge.

        Args:
            command: The command to start the MCP server (e.g., "npx", "node")
            args: Arguments for the command (e.g., ["chrome-devtools-mcp"])
            env: Environment variables for the server process
        """
        if not MCP_AVAILABLE:
            raise ImportError("mcp package required. Install with: pip install mcp")

        self.server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env
        )
        self.session: Optional[ClientSession] = None
        self._stdio_context = None
        self._session_context = None
        self._tools_cache = None

    async def connect(self):
        """Connect to the MCP server."""
        # Create and enter stdio context
        self._stdio_context = stdio_client(self.server_params)
        read, write = await self._stdio_context.__aenter__()

        # Create and enter session context
        self.session = ClientSession(read, write)
        self._session_context = self.session
        await self.session.__aenter__()
        await self.session.initialize()
        return self

    async def disconnect(self):
        """Disconnect from the MCP server."""
        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
        except:
            pass
        try:
            if self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)
        except:
            pass

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def list_tools(self) -> list:
        """List available tools from the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected. Use 'async with' or call connect() first.")

        result = await self.session.list_tools()
        return result.tools

    async def get_tools_for_gemini(self) -> list[types.Tool]:
        """
        Get MCP tools converted to Gemini FunctionDeclaration format.

        Returns:
            List of types.Tool objects ready for Gemini
        """
        if self._tools_cache:
            return self._tools_cache

        mcp_tools = await self.list_tools()
        gemini_tools = []

        for tool in mcp_tools:
            # Convert MCP inputSchema to Gemini parameters format
            parameters = self._convert_schema(tool.inputSchema) if tool.inputSchema else None

            func_decl = types.FunctionDeclaration(
                name=tool.name,
                description=tool.description or f"MCP tool: {tool.name}",
                parameters=parameters
            )

            gemini_tools.append(types.Tool(function_declarations=[func_decl]))

        self._tools_cache = gemini_tools
        return gemini_tools

    def _convert_schema(self, schema: dict) -> dict:
        """
        Convert JSON Schema to Gemini parameter format.
        Gemini expects a specific subset of JSON Schema.
        """
        if not schema:
            return None

        return self._convert_property(schema)

    def _convert_property(self, prop: dict) -> dict:
        """Recursively convert a JSON Schema property."""
        if not prop:
            return {"type": "string"}

        prop_type = prop.get("type", "string")

        # Handle arrays - Gemini requires 'items' for arrays
        if prop_type == "array":
            items = prop.get("items", {"type": "string"})
            return {
                "type": "array",
                "items": self._convert_property(items),
                "description": prop.get("description", "")
            }

        # Handle objects
        if prop_type == "object":
            converted = {
                "type": "object",
                "description": prop.get("description", "")
            }

            if "properties" in prop:
                converted["properties"] = {}
                for name, p in prop["properties"].items():
                    converted["properties"][name] = self._convert_property(p)

            if "required" in prop:
                converted["required"] = prop["required"]

            return converted

        # Handle primitives (string, number, integer, boolean)
        return {
            "type": prop_type,
            "description": prop.get("description", "")
        }

    async def execute_tool(self, tool_name: str, args: dict) -> str:
        """
        Execute an MCP tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            args: Arguments for the tool

        Returns:
            Tool result as string
        """
        if not self.session:
            raise RuntimeError("Not connected. Use 'async with' or call connect() first.")

        try:
            result = await self.session.call_tool(tool_name, arguments=args)

            # Extract text content from result
            if result.content:
                # MCP returns content as a list of content blocks
                texts = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        texts.append(content.text)
                    elif hasattr(content, 'data'):
                        # Binary data (like screenshots) - return base64 or path
                        texts.append(f"[Binary data: {len(content.data)} bytes]")
                return "\n".join(texts) if texts else "Tool executed successfully"
            return "Tool executed successfully (no output)"

        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"

    async def handle_function_call(self, function_call) -> str:
        """
        Handle a Gemini function call by executing the corresponding MCP tool.

        Args:
            function_call: The FunctionCall object from Gemini response

        Returns:
            Tool result as string
        """
        tool_name = function_call.name
        args = dict(function_call.args) if function_call.args else {}
        return await self.execute_tool(tool_name, args)


# =============================================================================
# Pre-configured bridges for common MCP servers
# =============================================================================

class ChromeDevToolsBridge(GeminiMCPBridge):
    """Pre-configured bridge for Chrome DevTools MCP server."""

    def __init__(self):
        super().__init__(
            command="npx",
            args=["chrome-devtools-mcp"]  # npm package: chrome-devtools-mcp
        )


class PlaywrightBridge(GeminiMCPBridge):
    """Pre-configured bridge for Playwright MCP server."""

    def __init__(self):
        super().__init__(
            command="npx",
            args=["@anthropic/mcp-server-playwright"]  # Official Anthropic package
        )


class FileSystemBridge(GeminiMCPBridge):
    """Pre-configured bridge for filesystem MCP server."""

    def __init__(self, allowed_paths: list[str]):
        super().__init__(
            command="npx",
            args=["@anthropic/mcp-server-filesystem"] + allowed_paths
        )


# =============================================================================
# Helper function for ADK agent integration
# =============================================================================

async def create_mcp_enhanced_agent_tools(
    base_tools: list,
    mcp_bridges: list[GeminiMCPBridge]
) -> tuple[list, list[GeminiMCPBridge]]:
    """
    Combine base ADK tools with MCP tools.

    Args:
        base_tools: List of FunctionTool objects from ADK
        mcp_bridges: List of connected MCP bridges

    Returns:
        Tuple of (combined_tools, bridges) for use in agent execution
    """
    combined = list(base_tools)

    for bridge in mcp_bridges:
        mcp_tools = await bridge.get_tools_for_gemini()
        combined.extend(mcp_tools)

    return combined, mcp_bridges


# =============================================================================
# Agent execution helper with MCP support
# =============================================================================

async def run_agent_with_mcp(
    agent,
    prompt: str,
    mcp_bridges: list[GeminiMCPBridge],
    max_turns: int = 10
):
    """
    Run an ADK agent with MCP tool support.

    This handles the execution loop, routing function calls to either
    ADK tools or MCP tools as appropriate.

    Args:
        agent: The ADK agent
        prompt: User prompt
        mcp_bridges: Connected MCP bridges
        max_turns: Maximum conversation turns

    Returns:
        Final agent response
    """
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService

    # Get MCP tool names for routing
    mcp_tool_names = set()
    for bridge in mcp_bridges:
        tools = await bridge.list_tools()
        mcp_tool_names.update(t.name for t in tools)

    # Create runner with combined tools
    # Note: This is a simplified version - full integration would need
    # custom Runner implementation for MCP tool routing

    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        session_service=session_service
    )

    session = await session_service.create_session(
        agent_name=agent.name,
        user_id="mcp_user"
    )

    # Run with custom tool execution for MCP
    async for event in runner.run_async(session.id, prompt):
        if hasattr(event, 'function_call'):
            fc = event.function_call
            if fc.name in mcp_tool_names:
                # Route to MCP
                for bridge in mcp_bridges:
                    try:
                        result = await bridge.execute_tool(fc.name, dict(fc.args))
                        # Feed result back to agent
                        # (This would need proper ADK integration)
                        print(f"[MCP] {fc.name}: {result[:200]}...")
                        break
                    except:
                        continue

        yield event
