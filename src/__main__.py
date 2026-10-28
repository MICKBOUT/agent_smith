from .api import generateSandboxReadyCode
from .sandbox.sandbox import Sandbox
from .utils.random_question import getRandoMBPP


def main() -> None:
    question = getRandoMBPP()
    code = generateSandboxReadyCode(question)
    # print(code)
    sandbox = Sandbox()
    ret_code = sandbox.execute(code)

    if ret_code != 0:
        print("new request")
    else:
        print("Done")


if __name__ == "__main__":
    main()
