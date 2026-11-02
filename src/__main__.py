from .api import generateSandboxReadyCode
from .sandbox.sandbox import Sandbox
from .utils.random_question import getRandoMBPP
from .utils.misc import addTest


def generate_mbpp():
    question = getRandoMBPP()
    question.test_list = """
assert True
assert True
assert True
assert False
"""
    print(f"Id: {question.task_id}\n"
          f"Question: {question.task_definition}")
    chat_completion, code = generateSandboxReadyCode(question)
    code_and_test = addTest(code, question)
    sandbox = Sandbox()
    ret_code = sandbox.execute(code_and_test)

    print(code_and_test)
    if ret_code != 0:
        print("new request")
    else:
        print("Done")


def main() -> None:
    generate_mbpp()


if __name__ == "__main__":
    main()
