from .api import generateSandboxReadyCode
from .sandbox.sandbox import Sandbox
from .utils.random_question import getRandoMBPP


def main() -> None:
    # question = getRandoMBPP()
    # code = generateSandboxReadyCode(question)
    code = """
def upper_ctr(str):
    count = 0
    for char in str:
        if char.isupper():
            count += 1
    return count

assert upper_ctr('PYthon') == 1
assert upper_ctr('BigData') == 1
assert upper_ctr('program') == 0
"""
    sandbox = Sandbox()
    ret_code = sandbox.execute(code)

    if ret_code != 0:
        print("new request")
    else:
        print("Done")

if __name__ == "__main__":
    main()
