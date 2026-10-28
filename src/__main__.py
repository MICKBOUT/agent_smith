from .api import generateSandboxReadyCode
from .sandbox import Sandbox
from .utils.random_question import getRandoMBPP


def main() -> None:
    question = getRandoMBPP()
    code = generateSandboxReadyCode(question)
    try:
        sandbox = Sandbox()
        sandbox.execute(code)
    except AssertionError:
        print("Test Fail")


if __name__ == "__main__":
    main()
