import sys

from sandbox_utils import get_new_namespace


namespace = get_new_namespace()


def main():
    code = ""
    for line in sys.stdin:
        code += line.rstrip("\n")
        if code.strip().endswith(":"):
            code += "\n"
            continue
        if code == "exit":
            break

        exec(code, namespace, namespace)
        code = ""


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
