import asyncio
import sys
import json
import os
from typing import Optional
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

load_dotenv()  # Load environment variables from .env

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        self.openai = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server"""
        if not server_script_path.endswith((".py", ".js")):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if server_script_path.endswith(".py") else "node"
        server_params = StdioServerParameters(command=command, args=[server_script_path])
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant who can use tools when needed."},
            {"role": "user", "content": query}
        ]

        response = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            } for tool in response.tools
        ]

        # Initial OpenAI API call
        response = await self.openai.chat.completions.create(
            model="gpt-4o",  # Or gpt-4, gpt-3.5-turbo, etc.
            messages=messages,
            temperature=0.7,
            tools=available_tools if available_tools else None,
            tool_choice="auto" if available_tools else None
        )

        tool_results = []
        final_text = []

        choice = response.choices[0]
        message = choice.message

        if message.content:
            final_text.append(message.content)

        # Handle tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # Execute tool
                result = await self.session.call_tool(tool_name, tool_args)
                tool_results.append({"tool": tool_name, "result": result})
                messages.append({"role": "assistant", "content": None, "tool_calls": [tool_call]})
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result.content})

            # Get final OpenAI response after tool use
            followup = await self.openai.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7
            )

            final_reply = followup.choices[0].message
            if final_reply.content:
                final_text.append(final_reply.content)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.process_query(query)
                print("\n" + response)
            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

