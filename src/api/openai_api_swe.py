import asyncio
from typing import Any

from fastmcp import Client

from .openai_api import ChatApi
from ..config import SYSTEM_PROMPT_SWE
from ..models import SWEBenchTaskInput
from ..config import Provider, MAX_INPUT_TOKENS_SWE, MAX_OUTPUT_TOKENS_SWE


BLUE_LOG_STR = "\033[34m[LOG]\033[0m"
INPUT_TOKEN = 300000
OUTPUT_TOKENS = 10000
TIMOUT = 900


class ChatApiSwe(ChatApi):
    MAX_INPUT_TOKENS = MAX_INPUT_TOKENS_SWE
    MAX_OUTPUT_TOKENS = MAX_OUTPUT_TOKENS_SWE

    def __init__(self, question: SWEBenchTaskInput, llm_provider: Provider, tools: list[dict[str, Any]]):
        self.setProvider(llm_provider)
        self._setQuestion(question)
        self._setTools(tools)

    def _setTools(self, tools: list[dict[str, Any]]) -> None:
        self.tools = tools

    def _setQuestion(self, question: SWEBenchTaskInput) -> None:
        super()._setQuestion()
        self.question = question
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT_SWE},
            {
                "role": "user",
                "content": f"hints text: {self.question.hints_text}\n"
                f"problem statement: {self.question.problem_statement}\n"
            },
        ]

    def GetSandboxIntput(self, code) -> str:
        return code


async def main():
    async with Client("mcp_tools_swebench.py") as mcp:  # or "http://localhost:9000/mcp"
        tools = [{"type": "function", "function": {
            "name": t.name,
            "description": t.description or "",
            "parameters": t.inputSchema}} for t in await mcp.list_tools()]
    return tools

if __name__ == "__main__":
    asyncio.run(main())
