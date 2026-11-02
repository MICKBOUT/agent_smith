import os
from functools import lru_cache

from openai import OpenAI

from ..config import (
    DEFAULT_REQUEST_TIMEOUT, DEFAULT_MAX_TOKEN,
    DEFAULT_PROVIDER, DEFAULT_MAX_TRY,
    SYSTEM_PROMPT_v0
)
from ..utils.enum import LLMProvider
from ..utils.misc import getTest
from ..models.exception import NoCodeBlockFound, NoneMessageError
from ..models.models_public import MBPPTaskInput


@lru_cache(maxsize=1)
def _load_dotenv() -> None:
    from dotenv import load_dotenv
    load_dotenv()


def getAPIkey(provider: LLMProvider) -> str:
    _load_dotenv()
    API_KEY = os.getenv(provider.value.API_KEY_NAME)
    if API_KEY is None:
        raise ValueError(f"{provider.value.API_KEY_NAME} must be set as env variable")
    return API_KEY


def getClient(provider: LLMProvider = DEFAULT_PROVIDER) -> OpenAI:
    return OpenAI(
        base_url=provider.value.URL,
        api_key=getAPIkey(provider),
        max_retries=0,
        timeout=DEFAULT_REQUEST_TIMEOUT
    )


def printModelslst(client: OpenAI = getClient()) -> None:
    models = [m.id for m in client.models.list()]
    for model in models:
        print(model)


def extractCode(message: str) -> str:
    start = message.find("```python")
    if start < 0:
        raise NoCodeBlockFound("no ```python block")
    start += len("```python")
    end = message.find("```", start)
    if end < 0:
        raise NoCodeBlockFound("unclosed code block")
    return message[start:end].strip()


def genCode(client: OpenAI, llm_provider: LLMProvider, question: MBPPTaskInput, max_try) -> tuple[OpenAI.ChatCompletion, str]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_v0},
        {
            "role": "user",
            "content": f"{question.task_definition}\n"
            f"Function Definition: '{question.function_definition}'\n"
            f"assert tests: {getTest(question)}"
        },
    ]
    for attempt in range(max_try):
        chat_completion = client.chat.completions.create(
            model=llm_provider.value.DEFAULT_MODEL,
            messages=messages,
            stop=["<end_code>"],
            max_tokens=DEFAULT_MAX_TOKEN,
            temperature=0.2
        )
        message = chat_completion.choices[0].message.content

        try:
            if not isinstance(message, str):
                raise NoneMessageError
            extracted_message = extractCode(message)
            return chat_completion, extracted_message

        except NoneMessageError:
            print("[LOG] None Message RETRY", flush=True)
            if attempt == max_try:
                raise
        except NoCodeBlockFound as e:
            print("[LOG] No CodeBlock Found", flush=True)
            if attempt == max_try:
                raise
            messages.append({"role": "assistant", "content": message})
            messages.append({
                "role": "user",
                "content": f"Your answer was invalid ({e}). Reply again with the code in a ```python block.",
            })
            print(message)


def generateSandboxReadyCode(question: MBPPTaskInput, llm_provider: LLMProvider = DEFAULT_PROVIDER, max_try: int = DEFAULT_MAX_TRY) -> tuple[OpenAI.ChatCompletion, str]:
    # client http so regenerate each time for connection timeout issue
    with getClient(llm_provider) as client:
        chat_completion, llm_code = genCode(client, llm_provider, question, max_try=max_try)
    return chat_completion, llm_code


if __name__ == "__main__":
    from ..utils.random_question import getRandoMBPP
    question = getRandoMBPP()
    code = generateSandboxReadyCode(question)
    print(code)
