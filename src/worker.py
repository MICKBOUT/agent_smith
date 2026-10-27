import sys

from sandbox import SafeBuiltins, SandboxError


def main():
    code = sys.stdin.read()
    namespace = {
        "__builtins__": SafeBuiltins.all
    }

    try:
        exec(code, namespace, namespace)
    except NameError as e:
        raise SandboxError(e)


if __name__ == "__main__":
    try:
        main()
    except SandboxError as e:
        print(e)
