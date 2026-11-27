from agent_common.api.openai_api import ChatApi
from agent_common.config import (
    SYSTEM_PROMPT_MBPP,
    MAX_INPUT_TOKENS_MBPP,
    MAX_OUTPUT_TOKENS_MBPP,
    Provider,
    DEFAULT_PROVIDER,
)
from agent_common.models import MBPPTaskInput
from agent_common.utils import getTest

BLUE_LOG_STR = "\033[34m[LOG]\033[0m"


class ChatApiMbpp(ChatApi):
    MAX_INPUT_TOKENS = MAX_INPUT_TOKENS_MBPP
    MAX_OUTPUT_TOKENS = MAX_OUTPUT_TOKENS_MBPP

    def __init__(self, question: MBPPTaskInput, llm_provider: Provider):
        self.setProvider(llm_provider)
        self._setQuestion(question)
        self._setTools()

    def _setQuestion(self, question: MBPPTaskInput) -> None:
        super()._setQuestion()
        self.question = question
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT_MBPP},
            {
                "role": "user",
                "content": f"{self.question.task_definition}\n"
                f"Function Definition: '{self.question.function_definition}'\n"
                f"assert tests: {getTest(self.question)}"
            },
        ]

    def _getSandboxIntput(self, code) -> str:
        return "\n".join([*self.question.test_imports, code])


if __name__ == "__main__":
    import json

    with open("datasets/mbpp/task.json") as file:
        conetent = json.load(file)
        question = MBPPTaskInput.model_validate(conetent)

    chat = ChatApi(question, DEFAULT_PROVIDER)
    chat.printModelslst(chat._getClient())
