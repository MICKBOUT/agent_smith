import asyncio
from fastmcp import Client


async def main():
    async with Client("mcp_tools_swebench.py") as mcp:  # or "http://localhost:9000/mcp"
        tools = [{"type": "function", "function": {
            "name": t.name,
            "description": t.description or "",
            "parameters": t.inputSchema}} for t in await mcp.list_tools()]
    return tools

tools = asyncio.run(main())
print(repr(tools))
