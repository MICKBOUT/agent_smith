import sys
import socket

from sandbox_utils import get_new_namespace  # type: ignore

SOCKET_PATH = "/run/sandbox-control/sandbox.sock"


def main() -> None:
    """
    Main execution line for the REPL worker.

    exemple of differents sys.argv.

    """

    if len(sys.argv) > 1:
        authorized_imports = sys.argv[1].split()
        namespace = get_new_namespace(authorized_imports)
    else:
        return

    if len(sys.argv) == 3 and sys.argv[2] == "--single":
        code = sys.stdin.read()
        exec(code, namespace, namespace)
        return

    control = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    control.connect(SOCKET_PATH)

    try:
        reader = control.makefile("r", encoding="utf-8")
        try:
            while True:
                lines = []
                while True:
                    line = reader.readline()
                    if line == "":
                        return
                    if line == "\n":
                        break
                    lines.append(line)

                if not lines:
                    continue

                code = "".join(lines)
                try:
                    exec(
                        compile(code, "<sandbox>", "single"),
                        namespace,
                        namespace,
                    )
                except (KeyboardInterrupt, SystemExit) as error:
                    print(f"{type(error).__name__}: {error}", file=sys.stderr)
                    control.sendall(b"\x01")
                    raise
                except Exception as error:
                    print(f"{type(error).__name__}: {error}", file=sys.stderr)
                    control.sendall(b"\x01")
                else:
                    control.sendall(b"\x00")
        finally:
            reader.close()
    finally:
        control.close()


if __name__ == "__main__":
    main()
