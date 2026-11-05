import os
from functools import lru_cache

import openai

from ..config import (
    SYSTEM_PROMPT_v0, DEFAULT_TEMPERATURE, DEFAULT_MAX_TRY,
    DEFAULT_REQUEST_TIMEOUT, DEFAULT_MAX_TOKEN
)
from ..utils.enum import LLMProvider
from ..utils.misc import getTest
from ..models.exception import NoCodeBlockFound, NoneMessageError, MaxTryReachError
from ..models.models_public import MBPPTaskInput


@lru_cache(maxsize=1)
def _load_dotenv() -> None:
    from dotenv import load_dotenv
    load_dotenv()


def getAPIkey(provider: LLMProvider) -> str:
    _load_dotenv()
    API_KEY = os.getenv(provider.value.API_KEY_NAME)
    if API_KEY is None:
        raise ValueError(f"{provider.value.API_KEY_NAME} is not set as env variable")
    return API_KEY


class ChatApi():
    def __init__(self, question: MBPPTaskInput, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        self.setQuestion(question)

    def setQuestion(self, question: MBPPTaskInput) -> None:
        "Change the question and reset the conversation"
        self.question = question
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT_v0},
            {
                "role": "user",
                "content": f"{self.question.task_definition}\n"
                f"Function Definition: '{self.question.function_definition}'\n"
                f"assert tests: {getTest(self.question)}"
            },
        ]
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _getClient(self) -> openai.OpenAI:
        return openai.OpenAI(
            base_url=self.llm_provider.value.URL,
            api_key=getAPIkey(self.llm_provider),
            max_retries=0,
            # max_tokens=1500,
            timeout=DEFAULT_REQUEST_TIMEOUT
        )

    def printModelslst(self, client: openai.OpenAI) -> None:
        models = [m.id for m in client.models.list()]
        for model in models:
            print(model)

    @staticmethod
    def extractCode(message: str) -> str:
        start = message.find("```python")
        if start < 0:
            raise NoCodeBlockFound("no ```python block")
        start += len("```python")
        end = message.find("```", start)
        if end < 0:
            raise NoCodeBlockFound("unclosed code block")
        return message[start:end].strip()

    def _genCode(self, client: openai.OpenAI, max_try) -> str:
        for attempt in range(max_try):
            try:
                response = client.chat.completions.create(
                    model=self.llm_provider.value.DEFAULT_MODEL,
                    messages=self.messages,
                    stop=["<end_code>"],
                    max_tokens=DEFAULT_MAX_TOKEN,
                    temperature=DEFAULT_TEMPERATURE
                )
            except openai.RateLimitError:
                print("\033[34m[LOG]\033[0m Change Model")
                raise 

            message = response.choices[0].message.content
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens
            try:
                if not isinstance(message, str):
                    raise NoneMessageError
                extracted_message = self.extractCode(message)
                return extracted_message

            except NoneMessageError:
                print("\033[34m[LOG]\033[0m None Message RETRY", message, flush=True)
            except NoCodeBlockFound as e:
                print("\033[34m[LOG]\033[0m No CodeBlock Found\n", message, flush=True)
                self.messages.append({"role": "assistant", "content": message})
                self.messages.append({
                    "role": "user",
                    "content": f"Your answer was invalid ({e}). Reply again with the code in a ```python block.",
                })
        raise MaxTryReachError

    def generateSandboxCode(self, max_try: int = DEFAULT_MAX_TRY) -> tuple[openai.OpenAI.ChatCompletion, str]:
        # client http so regenerate each time for connection timeout issue
        with self._getClient() as client:
            llm_code = self._genCode(client, max_try=max_try)
        return llm_code

    def addLog(self, message: str) -> None:
        self.messages.append({"role": "system", "content": message})
        self.messages.append({"role": "user", "content": "the test fail in the sandbox, send a new code that is complient to the test and pass the assert."})


if __name__ == "__main__":
    from ..utils.random_question import getRandoMBPP
    chat = ChatApi(getRandoMBPP())
    chat.printModelslst(chat._getClient())
