import asyncio
from typing import Any

from fastmcp import Client

from .openai_api import ChatApi
from ..config import SYSTEM_PROMPT_SWE
from ..models import SWEBenchTaskInput
from ..config import Provider


BLUE_LOG_STR = "\033[34m[LOG]\033[0m"


class ChatApiSwe(ChatApi):
    SYSTEM_PROMPT = SYSTEM_PROMPT_SWE

    def __init__(self, question: SWEBenchTaskInput, llm_provider: Provider, tools: list[dict[str, Any]]):
        self.setProvider(llm_provider)
        self._setQuestion(question)
        self._setTools(tools)

    def _setTools(self, tools: list[dict[str, Any]]) -> None:
        self.tools = tools

    def _setQuestion(self, question: SWEBenchTaskInput) -> None:
        ...


async def main():
    async with Client("mcp_tools_swebench.py") as mcp:  # or "http://localhost:9000/mcp"
        tools = [{"type": "function", "function": {
            "name": t.name,
            "description": t.description or "",
            "parameters": t.inputSchema}} for t in await mcp.list_tools()]
    return tools

if __name__ == "__main__":
    asyncio.run(main())
