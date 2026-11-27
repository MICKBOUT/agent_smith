from typing import Any, cast, Optional
from abc import ABC, abstractmethod
import json

import tiktoken
import openai

from agent_common.config import (
    DEFAULT_TEMPERATURE,
    DEFAULT_REQUEST_TIMEOUT,

    SYSTEM_SUCCES_MESSAGE,
    SYSTEM_ERROR_MESSAGE,
)
from agent_common.models import NoCodeBlockFound, NoneMessageError, LLmGenerationOutput
from agent_common.utils import getAPIkey
from agent_common.config import Provider


BLUE_LOG_STR = "\033[34m[LOG]\033[0m"


class ChatApi(ABC):
    MAX_INPUT_TOKENS = 10000
    MAX_OUTPUT_TOKENS = 10000

    def __init__(self, llm_provider: Provider):
        self.setProvider(llm_provider)
        self._setQuestion()
        self._setTools()

    def _setTools(self) -> None:
        self.tools = None

    @abstractmethod
    def _setQuestion(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.messages = []

    def setProvider(self, llm_provider: Provider) -> None:
        self.llm_provider = llm_provider

    @abstractmethod
    def _getSandboxIntput(self, code: str) -> str:
        return code

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
            token_count += len(encoding.encode(message.get("content") or ""))
            if message.get("tool_calls"):
                token_count += len(encoding.encode(json.dumps(message["tool_calls"])))
        return token_count

    def _getRequestMessages(self) -> list[dict[str, Any]]:
        base_messages = self.messages[:2]
        if self._countMessageTokens(base_messages) > self.MAX_INPUT_TOKENS:
            raise ValueError(f"The system prompt and task exceed {self.MAX_INPUT_TOKENS} input tokens")

        # Keep an assistant tool call and its matching tool results together.
        history = self.messages[2:]
        groups: list[list[dict[str, Any]]] = []
        index = 0
        while index < len(history):
            message = history[index]
            group = [message]
            if message.get("tool_calls"):
                pending_ids = {
                    call.get("id") for call in message["tool_calls"]
                }
                cursor = index + 1
                while cursor < len(history) and history[cursor].get("role") == "tool":
                    if history[cursor].get("tool_call_id") in pending_ids:
                        group.append(history[cursor])
                    cursor += 1
                    if not pending_ids.difference(
                        item.get("tool_call_id") for item in group[1:]
                    ):
                        break
                index = cursor
            else:
                index += 1
            groups.append(group)

        recent_messages: list[dict[str, Any]] = []
        for group in reversed(groups):
            candidate = base_messages + group + recent_messages
            if self._countMessageTokens(candidate) > self.MAX_INPUT_TOKENS:
                break
            recent_messages = group + recent_messages

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
            request = dict(
                model=self.llm_provider.MODEL_NAME,
                messages=cast(list[openai.types.chat.ChatCompletionMessageParam], request_messages),
                stop=["<end_code>"],
                max_tokens=self.MAX_OUTPUT_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
            )
            if self.tools:
                request["tools"] = self.tools
            response = client.chat.completions.create(**request)

            choices = getattr(response, "choices", None)
            if not choices:
                raise NoneMessageError("The model returned no response choices")

            message_obj = choices[0].message
            message = message_obj.content
            tool_calls = [call.model_dump() for call in (message_obj.tool_calls or [])]

            if not isinstance(message, str) and not tool_calls:
                raise NoneMessageError

            usage = getattr(response, "usage", None)
            input_tokens, output_tokens = 0, 0
            if usage is not None:
                input_tokens, output_tokens = usage.prompt_tokens or 0, usage.completion_tokens or 0
            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            response_text = message or ""
            code = self.extractCode(response_text) if not tool_calls else ""
            return LLmGenerationOutput(
                response=response_text,
                code=code,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                sandbox_input=self._getSandboxIntput(code),
                tool_calls=tool_calls,
            )

        except (openai.RateLimitError, openai.BadRequestError, openai.InternalServerError, openai.APITimeoutError) as e:
            print(BLUE_LOG_STR, self.llm_provider.NAME, type(e).__name__, flush=True)
            raise
        except NoneMessageError:
            print(BLUE_LOG_STR, self.llm_provider.NAME, "None Message RETRY", flush=True)
            raise
        except NoCodeBlockFound:
            print(BLUE_LOG_STR, self.llm_provider.NAME, "No CodeBlock Found\n", flush=True)
            print(message if "message" in locals() else "", flush=True)
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

    def generateSandboxCode(self, timeout: float = DEFAULT_REQUEST_TIMEOUT) -> LLmGenerationOutput:
        # client http so regenerate each time for connection timeout issue
        request_timeout = min(timeout, DEFAULT_REQUEST_TIMEOUT)
        with self._getClient(request_timeout) as client:
            output = self._genCode(client)
        return output
