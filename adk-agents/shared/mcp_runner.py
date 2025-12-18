"""
MCP-Enhanced Agent Runner

Runs ADK agents with support for MCP server tools.
Handles the execution loop, routing function calls to either ADK tools or MCP tools.
"""
import asyncio
import json
from typing import Optional, AsyncGenerator
from dataclasses import dataclass

from google.genai import Client
from google.genai import types

from .mcp_bridge import GeminiMCPBridge, ChromeDevToolsBridge


@dataclass
class AgentResponse:
    """Response from agent execution."""
    text: str
    tool_calls: list
    is_final: bool


class MCPAgentRunner:
    """
    Runner that executes ADK-style agents with MCP tool support.

    This handles:
    1. Combining ADK FunctionTools with MCP tools
    2. Routing function calls to the correct handler
    3. Managing the conversation loop
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        system_instruction: str = "",
        adk_tools: Optional[list] = None,
        mcp_bridges: Optional[list[GeminiMCPBridge]] = None,
        max_turns: int = 20,
        verbose: bool = True
    ):
        self.model = model
        self.system_instruction = system_instruction
        self.adk_tools = adk_tools or []
        self.mcp_bridges = mcp_bridges or []
        self.max_turns = max_turns
        self.verbose = verbose

        self.client = Client()
        self._mcp_tool_names: set = set()
        self._adk_tool_map: dict = {}
        self._combined_tools: list = []
        self._initialized = False

    async def initialize(self):
        """Initialize tools from all sources."""
        if self._initialized:
            return

        # Map ADK tools by name
        for tool in self.adk_tools:
            if hasattr(tool, 'func'):
                self._adk_tool_map[tool.func.__name__] = tool.func
            elif hasattr(tool, '__name__'):
                self._adk_tool_map[tool.__name__] = tool

        # Collect MCP tool names and convert to Gemini format
        mcp_tools_gemini = []
        for bridge in self.mcp_bridges:
            mcp_tools = await bridge.list_tools()
            for t in mcp_tools:
                self._mcp_tool_names.add(t.name)

            gemini_tools = await bridge.get_tools_for_gemini()
            mcp_tools_gemini.extend(gemini_tools)

        # Combine: ADK tools (as callables) + MCP tools (as declarations)
        self._combined_tools = list(self.adk_tools) + mcp_tools_gemini
        self._initialized = True

        if self.verbose:
            print(f"[MCPRunner] Initialized with {len(self.adk_tools)} ADK tools + {len(self._mcp_tool_names)} MCP tools")

    async def _execute_tool(self, name: str, args: dict) -> str:
        """Execute a tool, routing to ADK or MCP as appropriate."""

        # Check if it's an MCP tool
        if name in self._mcp_tool_names:
            for bridge in self.mcp_bridges:
                try:
                    result = await bridge.execute_tool(name, args)
                    return result
                except Exception as e:
                    continue
            return f"Error: MCP tool {name} not found in any bridge"

        # Check if it's an ADK tool
        if name in self._adk_tool_map:
            func = self._adk_tool_map[name]
            try:
                # ADK tools are sync functions
                result = func(**args)
                return result if isinstance(result, str) else json.dumps(result)
            except Exception as e:
                return f"Error executing {name}: {str(e)}"

        return f"Error: Unknown tool {name}"

    async def run(self, prompt: str) -> AsyncGenerator[AgentResponse, None]:
        """
        Run the agent with the given prompt.

        Yields AgentResponse objects for each turn.
        """
        await self.initialize()

        # Build conversation history
        contents = [types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )]

        for turn in range(self.max_turns):
            if self.verbose:
                print(f"\n[Turn {turn + 1}/{self.max_turns}]")

            # Generate response
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=self._combined_tools,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True  # We handle function calls manually
                    )
                )
            )

            # Check for function calls
            candidate = response.candidates[0]
            parts = candidate.content.parts

            function_calls = []
            text_parts = []

            for part in parts:
                if part.function_call:
                    function_calls.append(part.function_call)
                elif part.text:
                    text_parts.append(part.text)

            # If no function calls, we're done
            if not function_calls:
                final_text = "\n".join(text_parts)
                yield AgentResponse(text=final_text, tool_calls=[], is_final=True)
                return

            # Execute function calls
            tool_results = []
            for fc in function_calls:
                if self.verbose:
                    print(f"[TOOL] {fc.name}({json.dumps(dict(fc.args))[:100]}...)")

                result = await self._execute_tool(fc.name, dict(fc.args))

                if self.verbose:
                    print(f"[RESULT] {result[:200]}...")

                tool_results.append({
                    "name": fc.name,
                    "args": dict(fc.args),
                    "result": result
                })

            # Yield intermediate response
            yield AgentResponse(
                text="\n".join(text_parts),
                tool_calls=tool_results,
                is_final=False
            )

            # Add model response to history
            contents.append(candidate.content)

            # Add function responses to history
            function_response_parts = []
            for fc, tr in zip(function_calls, tool_results):
                function_response_parts.append(types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response={"result": tr["result"]}
                    )
                ))

            contents.append(types.Content(
                role="user",  # Function responses come from "user" role in Gemini
                parts=function_response_parts
            ))

        # Max turns reached
        yield AgentResponse(
            text="[Max turns reached]",
            tool_calls=[],
            is_final=True
        )

    async def run_sync(self, prompt: str) -> str:
        """
        Run the agent and return final text response.
        Convenience method for simple use cases.
        """
        final_response = ""
        async for response in self.run(prompt):
            if response.is_final:
                final_response = response.text
        return final_response


# =============================================================================
# Convenience function for quick setup
# =============================================================================

async def run_with_chrome_devtools(
    prompt: str,
    model: str = "gemini-2.5-flash",
    system_instruction: str = "",
    adk_tools: Optional[list] = None,
    verbose: bool = True
) -> str:
    """
    Run a prompt with Chrome DevTools MCP tools available.

    Example:
        result = await run_with_chrome_devtools(
            prompt="Navigate to http://localhost/app and take a screenshot",
            system_instruction="You are a web testing agent."
        )
    """
    async with ChromeDevToolsBridge() as bridge:
        runner = MCPAgentRunner(
            model=model,
            system_instruction=system_instruction,
            adk_tools=adk_tools or [],
            mcp_bridges=[bridge],
            verbose=verbose
        )

        return await runner.run_sync(prompt)


# =============================================================================
# CLI for testing
# =============================================================================

async def main():
    """Test the MCP runner with Chrome DevTools."""
    print("Testing MCP Runner with Chrome DevTools...")

    async with ChromeDevToolsBridge() as bridge:
        # List available tools
        tools = await bridge.list_tools()
        print(f"\nAvailable MCP tools ({len(tools)}):")
        for t in tools[:10]:
            print(f"  - {t.name}: {t.description[:60]}...")

        # Test simple execution
        runner = MCPAgentRunner(
            model="gemini-2.5-flash",
            system_instruction="You are a helpful web testing assistant.",
            mcp_bridges=[bridge],
            verbose=True
        )

        prompt = "List the pages open in Chrome using the list_pages tool."

        print(f"\n{'='*60}")
        print(f"Prompt: {prompt}")
        print('='*60)

        async for response in runner.run(prompt):
            if response.tool_calls:
                for tc in response.tool_calls:
                    print(f"\n[Tool Call] {tc['name']}")
                    print(f"[Result] {tc['result'][:500]}")
            if response.is_final:
                print(f"\n[Final Response]\n{response.text}")


if __name__ == "__main__":
    asyncio.run(main())
