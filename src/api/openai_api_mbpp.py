from .openai_api import ChatApi
from ..config import SYSTEM_PROMPT_MBPP, DEFAULT_REQUEST_TIMEOUT, MAX_INPUT_TOKENS_MBPP, MAX_OUTPUT_TOKENS_MBPP
from ..models import MBPPTaskInput, LLmGenerationOutput
from ..config import Provider, DEFAULT_PROVIDER
from ..utils import getTest, createProgram

BLUE_LOG_STR = "\033[34m[LOG]\033[0m"


class ChatApiMbpp(ChatApi):
    MAX_INPUT_TOKENS = MAX_INPUT_TOKENS_MBPP
    MAX_OUTPUT_TOKENS = MAX_OUTPUT_TOKENS_MBPP

    def __init__(self, question: MBPPTaskInput, llm_provider: Provider):
        self.setProvider(llm_provider)
        self._setQuestion(question)

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

    def GetSandboxIntput(self, code) -> str:
        return createProgram(code, self.question.test_list, self.question.test_imports)

    def generateSandboxCode(self, timeout: float = DEFAULT_REQUEST_TIMEOUT) -> LLmGenerationOutput:
        # client http so regenerate each time for connection timeout issue
        request_timeout = min(timeout, DEFAULT_REQUEST_TIMEOUT)
        with self._getClient(request_timeout) as client:
            output = self._genCode(client)
        return output


if __name__ == "__main__":
    import json

    with open("datasets/mbpp/task.json") as file:
        conetent = json.load(file)
        question = MBPPTaskInput.model_validate(conetent)

    chat = ChatApi(question, DEFAULT_PROVIDER)
    chat.printModelslst(chat._getClient())
