import openai

from .api import ChatApi
from .api.openai_api import getAPIkey
from .config import DEFAULT_MAX_ITERATION, DEFAULT_PROVIDER, LLMProvider, Provider
from .models import SandboxConfig
from .sandbox.sandbox import Sandbox
from .utils import getRandoMBPP, addTest, rm_import_txt


def check_apikeys_available() -> list[Provider]:
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

    print(f"Id: {question.task_id}\n"
          f"Question: {question.task_definition}")

    for _ in range(DEFAULT_MAX_ITERATION):
        try:
            code = chat.generateSandboxCode()
        except openai.RateLimitError:
            provider_lst.pop()
            if len(provider_lst) == 0:
                raise Exception("No more provider available")
            chat.setProvider(provider_lst[-1])
            continue

        code_and_test = addTest(code, question)
        result = sandbox.execute(code_and_test)
        if result.returncode != 0:
            print("\033[31mError in the code\033[0m")
            print("\033[34m[LOG]\033[0m", result.stderr, flush=True)
            chat.addLog(result.stderr)
        else:
            print("\033[32mDone\033[0m")
            break

    print(code_and_test)
    print(f"total_input_tokens: {chat.total_input_tokens}")
    print(f"total_output_tokens: {chat.total_output_tokens}")


def main() -> None:
    provider_lst = check_apikeys_available()
    if len(provider_lst) == 0:
        raise ValueError("No Api keys are set as env variable")
    generate_mbpp(provider_lst)


if __name__ == "__main__":
    main()
