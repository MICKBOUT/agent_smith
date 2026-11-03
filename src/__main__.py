from .api import ChatApi
from .sandbox.sandbox import Sandbox
from .utils.random_question import getRandoMBPP
from .utils.misc import addTest
from .config import DEFAULT_MAX_ITERATION


def generate_mbpp():
    sandbox = Sandbox()
    question = getRandoMBPP()
    chat_api = ChatApi(question=question)

    print(f"Id: {question.task_id}\n"
          f"Question: {question.task_definition}")
    ret_code = None

    for trys in range(DEFAULT_MAX_ITERATION):
        code = chat_api.generateSandboxCode()
        code_and_test = addTest(code, question)
        ret_code = sandbox.execute(code_and_test)
        if ret_code != 0:
            print("\033[31mError in the code\033[0m")
            chat_api.addLog()
        else:
            print(code_and_test)
            print("\033[32mDone\033[0m")
            break


def main() -> None:
    generate_mbpp()


if __name__ == "__main__":
    main()
