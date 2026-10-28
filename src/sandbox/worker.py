import sys

from .sandbox_utils import get_new_namespace


namespace = get_new_namespace()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        code = sys.stdin.read()
        exec(code, namespace, namespace)
        return

    code = ""
    for line in sys.stdin:
        code += line
        if code.strip().endswith(":"):
            continue
        if code.strip() == "exit":
            break

        exec(code, namespace, namespace)
        code = ""


if __name__ == "__main__":
    main()
