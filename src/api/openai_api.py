import os

from openai import OpenAI
from functools import lru_cache

from ..config import SYSTEM_PROMPT_v0, DEFAULT_PROVIDER
from ..utils.enum import LLMProvider
from ..models.exception import NoCodeBlockFound
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


def getClient(provider: LLMProvider) -> OpenAI:
    return OpenAI(
        base_url=provider.value.URL,
        api_key=getAPIkey(provider),
    )


def printModelslst(client: OpenAI) -> None:
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


def genCode(client: OpenAI, llm_provider: LLMProvider, question: MBPPTaskInput, max_retries: int = 3) -> str:
    task_text, func_def = question.task_definition, question.function_definition

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_v0},
        {"role": "user", "content": f"{task_text} Function Definition: '{func_def}'"},
    ]
    print(messages[1]["content"])
    for attempt in range(max_retries + 1):
        r = client.chat.completions.create(
            model=llm_provider.value.DEFAULT_MODEL,
            messages=messages,
            stop=["<end_code>"],
            max_tokens=1500,
            temperature=0.2,
        )
        message = r.choices[0].message.content
        if not isinstance(message, str):
            raise ValueError("The model returned an empty or non-text response")

        try:
            return extractCode(message)
        except NoCodeBlockFound as e:
            if attempt == max_retries:
                raise
            print(message)
            messages.append({"role": "assistant", "content": message})
            messages.append({
                "role": "user",
                "content": f"Your answer was invalid ({e}). Reply again with the code in a ```python block.",
            })
            print(message)


def addTest(code: str, question: MBPPTaskInput) -> str:
    code += '\n'
    for test_import in question.test_imports:
        code += test_import + '\n'
    code += '\n'
    for assert_test in question.test_list:
        code += assert_test + '\n'

    return code


def generateSandboxReadyCode(question: MBPPTaskInput, llm_provider: LLMProvider = DEFAULT_PROVIDER) -> str:
    # client http so regenerate each time for connection timeout issue
    with getClient(llm_provider) as client:
        llm_code = genCode(client, llm_provider, question)
    code = addTest(llm_code, question)
    return code


if __name__ == "__main__":
    from ..utils.random_question import getRandoMBPP
    code = generateSandboxReadyCode(getRandoMBPP())
    print(code)
