import sys
import socket

from sandbox_utils import get_new_namespace  # type: ignore


def main() -> None:
    """
    Main execution line for the REPL worker.

    exemple of differents sys.argv.

    "math numpy functools", "--single"
    "numpy random pandas", "--control-fd 5"
    """

    if len(sys.argv) > 1:
        authorized_imports = sys.argv[1].split(" ")
        namespace = get_new_namespace(authorized_imports)
    else:
        return

    if len(sys.argv) == 3 and sys.argv[2] == "--single":
        code = sys.stdin.read()
        exec(code, namespace, namespace)
        return

    if len(sys.argv) != 4 or sys.argv[2] != "--control-fd":
        raise ValueError("Expected --control-fd FD")

    control_fd = int(sys.argv[3])
    control = socket.socket(fileno=control_fd)

    try:
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
            status = b"\x00"
            try:
                exec(compile(code, "<sandbox>", "single"), namespace, namespace)
            except Exception as error:
                status = b"\x01"
                print(f"{type(error).__name__}: {error}", file=sys.stderr)
            finally:
                control.sendall(status)

            if not line:
                break
    finally:
        control.close()


if __name__ == "__main__":
    main()
