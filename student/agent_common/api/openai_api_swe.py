from typing import Any

from agent_common.api.openai_api import ChatApi
from agent_common.config import (
    SYSTEM_PROMPT_SWE,
    Provider,
    MAX_INPUT_TOKENS_SWE,
    MAX_OUTPUT_TOKENS_SWE,
)
from agent_common.models import SWEBenchTaskInput


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
                f"repository: {self.question.repo}\n"
                f"evaluation script: {self.question.eval_script}\n"
                "Use run_command with the repository root as workdir to run tests and the evaluation script.\n"
            },
        ]

    @staticmethod
    def extractCode(message: str) -> str:
        # SWE-bench uses native API tool calls, not sandboxed Python snippets.
        return ""

    def _getSandboxIntput(self, code: str) -> str:
        return code
