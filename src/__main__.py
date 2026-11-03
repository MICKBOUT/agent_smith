from .api import ChatApi
from .sandbox.sandbox import Sandbox
from .utils.random_question import getRandoMBPP
from .utils.misc import addTest
from .config import DEFAULT_MAX_ITERATION
from .models.models_public import SandboxConfig


def generate_mbpp():
    sandbox = Sandbox(SandboxConfig())
    question = getRandoMBPP()
    chat = ChatApi(question=question)

    print(f"Id: {question.task_id}\n"
          f"Question: {question.task_definition}")

    for trys in range(DEFAULT_MAX_ITERATION):
        code = chat.generateSandboxCode()
        code_and_test = addTest(code, question)
        result = sandbox.execute(code_and_test)
        if result:
            print("\033[31mError in the code\033[0m")
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
    generate_mbpp()



if __name__ == "__main__":
    main()
