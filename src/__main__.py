import openai
import time

from .api import ChatApi
from .api.openai_api import getAPIkey
from .config import (
    DEFAULT_GENERATION_TIMEOUT, DEFAULT_MAX_ITERATION, DEFAULT_PROVIDER, SYSTEM_PROMPT,
    LLMProvider
)
from .models import SandboxConfig, SolutionOutput
from .sandbox.sandbox import Sandbox
from .utils import getRandoMBPP, addTest, rm_import_txt


def check_apikeys_available() -> list[LLMProvider]:
    provider_lst = []
    for provider in LLMProvider:
        if provider == DEFAULT_PROVIDER:
            continue
        try:
            getAPIkey(provider)
            provider_lst.append(provider)
        except ValueError:
            print(f"No key found for: {provider.value.NAME}")
    try:
        getAPIkey(DEFAULT_PROVIDER)
        provider_lst.append(DEFAULT_PROVIDER)
    except ValueError:
        print(f"No key found for: {DEFAULT_PROVIDER.value.NAME}")
    return provider_lst


def generate_mbpp(provider_lst: list[LLMProvider]):
    question = getRandoMBPP()
    sandbox = Sandbox(SandboxConfig(
        authorized_imports=rm_import_txt(question.test_imports)
    ))
    chat = ChatApi(
        question=question,
        llm_provider=provider_lst[-1]
    )

    print(
        f"Id: {question.task_id}\n"
        f"Question: {question.task_definition}"
    )

    code_and_test, success, error = None, False, ""

    start_time = time.monotonic()
    generation_deadline = start_time + DEFAULT_GENERATION_TIMEOUT
    for iteration in range(DEFAULT_MAX_ITERATION):
        remaining_time = generation_deadline - time.monotonic()
        if remaining_time < 0:
            error = "Generation timed out"
            break

        try:
            code = chat.generateSandboxCode(timeout=remaining_time)
        except openai.RateLimitError:
            provider_lst.pop()
            if len(provider_lst) == 0:
                error = "No provider available"
                break
            chat.setProvider(provider_lst[-1])
            continue

        code_and_test = addTest(code, question)
        result = sandbox.execute(code_and_test)
        if result.returncode != 0:
            error = result.stderr
            print("\033[31mError in the code\033[0m")
            print("\033[34m[LOG]\033[0m", result.stderr, flush=True)
            chat.addLog(result.stderr)
        else:
            print("\033[32mDone\033[0m")
            error, success = None, True
            break

    print(code_and_test)
    ans = SolutionOutput.model_validate({
        "task_id": str(question.task_id),
        "benchmark": "mbpp",
        "success": success,
        "solution": code,
        "iterations": iteration,  # to-do: put the right thing here
        "total_requests": iteration,
        "total_input_tokens": chat.total_input_tokens,
        "total_output_tokens": chat.total_output_tokens,
        "total_time_seconds": time.monotonic() - start_time,
        "steps": [],  # to-do: put the right thing here
        "system_prompt": SYSTEM_PROMPT,
        "error": error
    })
    print(ans)


def main() -> None:
    provider_lst = check_apikeys_available()
    if len(provider_lst) == 0:
        raise ValueError("No Api keys are set as env variable")
    generate_mbpp(provider_lst)


if __name__ == "__main__":
    main()
