from .api import ChatApi
from .api.openai_api import getAPIkey
from .config import DEFAULT_MAX_ITERATION, DEFAULT_PROVIDER
from .models.models_public import SandboxConfig
from .utils.random_question import getRandoMBPP
from .sandbox.sandbox import Sandbox
from .utils.misc import addTest, rm_import_txt
from .utils.enum import Provider, LLMProvider


def check_apikeys_available() -> list[Provider]:
    provider_lst = []
    for ell in LLMProvider:
        provider = ell
        try:
            getAPIkey(provider)
            provider_lst.append(provider)
        except ValueError:
            print(f"No key found for: {provider.value.NAME}")
    return provider_lst


def generate_mbpp(provider: LLMProvider):
    question = getRandoMBPP()
    sandbox = Sandbox(SandboxConfig(
        authorized_imports=rm_import_txt(question.test_imports)
    ))
    chat = ChatApi(
        question=question,
        llm_provider=provider
    )

    print(f"Id: {question.task_id}\n"
          f"Question: {question.task_definition}")

    for trys in range(DEFAULT_MAX_ITERATION):
        code = chat.generateSandboxCode()
        code_and_test = addTest(code, question)
        result = sandbox.execute(code_and_test)
        if result.returncode != 0:
            print("\033[31mError in the code\033[0m")
            print("\033[34m[LOG]\033[0m", result.stderr, flush=True)
            chat.addLog(result.stderr)
        else:
            print("\033[32mDone\033[0m")
            print(f"total_input_tokens: {chat.total_input_tokens}")
            print(f"total_output_tokens: {chat.total_output_tokens}")
            break

    print(code_and_test)
    print(f"total_input_tokens: {chat.total_input_tokens}")
    print(f"total_output_tokens: {chat.total_output_tokens}")


def main() -> None:
    provider_lst = check_apikeys_available()
    if len(provider_lst) == 0:
        raise ValueError("No Api keys are set as env variable")
    provider = DEFAULT_PROVIDER if DEFAULT_PROVIDER in provider_lst else provider_lst[0]
    generate_mbpp(provider)


if __name__ == "__main__":
    main()
