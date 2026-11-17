import openai
import tiktoken

from ..config import (
    SYSTEM_PROMPT, DEFAULT_TEMPERATURE,
    DEFAULT_REQUEST_TIMEOUT, DEFAULT_MAX_TOKEN, MAX_INPUT_TOKENS
)
from ..models import NoCodeBlockFound, NoneMessageError, MBPPTaskInput, LLmGenerationOutput
from ..utils import getTest, getAPIkey, createProgram
from ..config import Provider, DEFAULT_PROVIDER


BLUE_LOG_STR = "\033[34m[LOG]\033[0m"


class ChatApi():
    def __init__(self, question: MBPPTaskInput, llm_provider: Provider):
        self.setProvider(llm_provider)
        self.setQuestion(question)

    def setQuestion(self, question: MBPPTaskInput) -> None:
        "Change the question and reset the conversation"
        self.question = question
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{self.question.task_definition}\n"
                f"Function Definition: '{self.question.function_definition}'\n"
                f"assert tests: {getTest(self.question)}"
            },
        ]
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def setProvider(self, llm_provider: Provider) -> None:
        self.llm_provider = llm_provider

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
        if self._countMessageTokens(base_messages) > MAX_INPUT_TOKENS:
            raise ValueError("The system prompt and task exceed 6000 input tokens")

        recent_messages: list[dict[str, str]] = []
        for message in reversed(self.messages[2:]):
            candidate = base_messages + [message] + recent_messages
            if self._countMessageTokens(candidate) > MAX_INPUT_TOKENS:
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
                messages=request_messages,
                stop=["<end_code>"],
                max_tokens=DEFAULT_MAX_TOKEN,
                temperature=DEFAULT_TEMPERATURE
            )

            choices = getattr(response, "choices", None)
            if not choices:
                raise NoneMessageError("The model returned no response choices")

            message = choices[0].message.content

            if not isinstance(message, str):
                raise NoneMessageError

            usage = getattr(response, "usage", None)
            if usage is not None:
                self.total_input_tokens += usage.prompt_tokens or 0
                self.total_output_tokens += usage.completion_tokens or 0
            code = self.extractCode(message)
            return LLmGenerationOutput(
                response=message,
                code=code,
                input_tokens=usage.prompt_tokens or 0,
                output_tokens=usage.completion_tokens or 0,
                sandbox_input=createProgram(code, self.question.test_list, self.question.test_imports),
            )

        except (openai.RateLimitError, openai.BadRequestError, openai.InternalServerError) as e:
            print(BLUE_LOG_STR, type(e).__name__, flush=True)
            raise
        except NoneMessageError:
            print(BLUE_LOG_STR, "None Message RETRY", flush=True)
            raise
        except NoCodeBlockFound as e:
            print(BLUE_LOG_STR, "No CodeBlock Found\n", flush=True)
            self.messages.append({"role": "assistant", "content": message})
            self.messages.append({
                "role": "user",
                "content": f"Your answer was invalid ({e}). Reply again with the code in a ```python block.",
            })
            raise
        return ""

    def generateSandboxCode(self, timeout: float = DEFAULT_REQUEST_TIMEOUT) -> LLmGenerationOutput:
        # client http so regenerate each time for connection timeout issue
        request_timeout = min(timeout, DEFAULT_REQUEST_TIMEOUT)
        with self._getClient(request_timeout) as client:
            output = self._genCode(client)
        return output

    def addLog(self, message: str) -> None:
        self.messages.append({"role": "system", "content": message})
        self.messages.append({"role": "user", "content": "the test fail in the sandbox, send a new code that is complient to the test and pass the assert."})


if __name__ == "__main__":
    from ..utils import getRandoMBPP
    chat = ChatApi(getRandoMBPP(), DEFAULT_PROVIDER)
    chat.printModelslst(chat._getClient())
