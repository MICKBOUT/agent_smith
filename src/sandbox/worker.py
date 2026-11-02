import sys

from .sandbox_utils import get_new_namespace

namespace = get_new_namespace()


def main() -> None:
    """
    Main execution line for the REPL worker.
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        code = sys.stdin.read()
        exec(code, namespace, namespace)
        return

    while True:
        lines = []
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            if line == "\n":
                break
            lines.append(line)

        if not lines:
            if not line:
                break
            continue

        code = "".join(lines)
        try:
            exec(compile(code, "<sandbox>", "single"), namespace, namespace)
        except Exception as error:
            print(f"{type(error).__name__}: {error}", file=sys.stderr)

        if not line:
            break


if __name__ == "__main__":
    main()
