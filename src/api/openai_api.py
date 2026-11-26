from typing import cast, Optional
from abc import ABC, abstractmethod

import tiktoken
import openai

from ..config import (
    DEFAULT_TEMPERATURE,
    DEFAULT_REQUEST_TIMEOUT,

    SYSTEM_SUCCES_MESSAGE,
    SYSTEM_ERROR_MESSAGE,
)
from ..models import NoCodeBlockFound, NoneMessageError, LLmGenerationOutput
from ..utils import getAPIkey, createProgram
from ..config import Provider


BLUE_LOG_STR = "\033[34m[LOG]\033[0m"


class ChatApi(ABC):
    MAX_INPUT_TOKENS = 10000
    MAX_OUTPUT_TOKENS = 10000

    def __init__(self, llm_provider: Provider):
        self.setProvider(llm_provider)
        self._setQuestion()
        self._setTools()

    def _setTools(self) -> None:
        self.tools = {}

    @abstractmethod
    def _setQuestion(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.messages = []

    def setProvider(self, llm_provider: Provider) -> None:
        self.llm_provider = llm_provider

    def GetSandboxIntput(self) -> str:
        pass

    def _getClient(self, timeout: float = DEFAULT_REQUEST_TIMEOUT) -> openai.OpenAI:
        return openai.OpenAI(
            base_url=self.llm_provider.URL,
            api_key=getAPIkey(self.llm_provider),
            max_retries=0,
            timeout=timeout
        )

    def printModelslst(self, client: openai.OpenAI) -> None:
        models = [m.id for m in client.models.list()]
        for model in models:
            print(model)

    def _countMessageTokens(self, messages: list[dict[str, str]]) -> int:
        try:
            encoding = tiktoken.encoding_for_model(
                self.llm_provider.MODEL_NAME
            )
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        token_count = 2
        for message in messages:
            token_count += 4
            token_count += len(encoding.encode(message["role"]))
            token_count += len(encoding.encode(message["content"]))
        return token_count

    def _getRequestMessages(self) -> list[dict[str, str]]:
        base_messages = self.messages[:2]
        if self._countMessageTokens(base_messages) > self.MAX_INPUT_TOKENS:
            raise ValueError(f"The system prompt and task exceed {self.MAX_INPUT_TOKENS} input tokens")

        recent_messages: list[dict[str, str]] = []
        for message in reversed(self.messages[2:]):
            candidate = base_messages + [message] + recent_messages
            if self._countMessageTokens(candidate) > self.MAX_INPUT_TOKENS:
                break
            recent_messages.insert(0, message)

        return base_messages + recent_messages

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

    def _genCode(self, client: openai.OpenAI) -> LLmGenerationOutput:
        try:
            request_messages = self._getRequestMessages()
            response = client.chat.completions.create(
                model=self.llm_provider.MODEL_NAME,
                messages=cast(list[openai.types.chat.ChatCompletionMessageParam], request_messages),
                stop=["<end_code>"],
                max_tokens=self.MAX_OUTPUT_TOKENS,
                temperature=DEFAULT_TEMPERATURE
            )

            choices = getattr(response, "choices", None)
            if not choices:
                raise NoneMessageError("The model returned no response choices")

            message = choices[0].message.content

            if not isinstance(message, str):
                raise NoneMessageError

            usage = getattr(response, "usage", None)
            input_tokens, output_tokens = 0, 0
            if usage is not None:
                input_tokens, output_tokens = usage.prompt_tokens or 0, usage.completion_tokens or 0
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            code = self.extractCode(message)
            return LLmGenerationOutput(
                response=message,
                code=code,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                sandbox_input=self.GetSandboxIntput(code)
            )

        except (openai.RateLimitError, openai.BadRequestError, openai.InternalServerError, openai.APITimeoutError) as e:
            print(BLUE_LOG_STR, self.llm_provider.NAME, type(e).__name__, flush=True)
            raise
        except NoneMessageError:
            print(BLUE_LOG_STR, self.llm_provider.NAME, "None Message RETRY", flush=True)
            raise
        except NoCodeBlockFound:
            print(BLUE_LOG_STR, self.llm_provider.NAME, "No CodeBlock Found\n", flush=True)
            print(message, flush=True)
            raise
        return ""

    def addLogSandboxError(self, message: str) -> None:
        self.messages.append({"role": "system", "content": message})
        self.messages.append({"role": "user", "content": SYSTEM_ERROR_MESSAGE})

    def addLogDefaultError(self, message: str) -> None:
        self.messages.append({"role": "system", "content": message})

    def addLogSucces(self, message: Optional[str] = None) -> None:
        self.messages.append({
            "role": "user",
            "content": f"Sandbox observation: {message}\n{SYSTEM_SUCCES_MESSAGE}",
        })
