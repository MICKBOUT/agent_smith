import sys

from .sandbox_utils import get_new_namespace


namespace = get_new_namespace()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        code = sys.stdin.read()
        exec(code, namespace, namespace)
        return

    while True:
        header = sys.stdin.readline()
        if not header:
            break

        try:
            code_length = int(header)
        except ValueError:
            break

        code = sys.stdin.read(code_length)
        if len(code) != code_length:
            break

        try:
            exec(compile(code, "<sandbox>", "single"), namespace, namespace)
        except Exception as error:
            print(f"{type(error).__name__}: {error}", file=sys.stderr)

if __name__ == "__main__":
    main()
