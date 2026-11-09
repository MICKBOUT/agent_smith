"""

"""

import sys
import subprocess
import codeop
import readline  # noqa, for better input, do not delete
import socket
import select
import time
import argparse

from typing import Any
from pathlib import Path

from models import SandboxError
from models import SandboxConfig

from .docker_init import Container
from .sandbox_loader import load_python_file, load_json_template


Jsp = Any


class Sandbox:
    """Basic class for sandboxing and executing python code."""

    RESET = "\001\033[0m\002"
    SAND = "\001\033[1;38;2;194;178;128m\002"
    BOX = "\001\033[1;38;2;80;150;255m\002"
    ITALIC = "\033[0m"
    NAME = f"{SAND}sand{BOX}box{RESET}> "

    LOGO = (
        f"{SAND} ____   __   __ _  ____  "
        f"{BOX}____   __  _  _ \n"
        f"{SAND}/ ___) / _\\ (  ( \\(    \\"
        f"{BOX}(  _ \\ /  \\( \\/ )\n"
        f"{SAND}\\___ \\/    \\/    / ) D ( "
        f"{BOX}) _ ((  O ))  ( \n"
        f"{SAND}(____/\\_/\\_/\\_)__)(____/"
        f"{BOX}(____/ \\__/(_/\\_){RESET}"
        "\npdauga & mboutte.\n"
    )
    print(LOGO)

    def __init__(self, config: SandboxConfig) -> None:
        """
        init the config and init the container.

        Args:
            config: The sandbox config.
        """
        self.config = config
        self.timeout = config.max_execution_time_seconds
        self.authorized_imports = config.authorized_imports

        self.container = Container()

    def new_repl(self) -> None:
        """
        launch an interactive sandboxed and Docker isolated REPL.
        """

        self.container.run_interactive()

    def repl(self) -> None:
        """
        launch an interactive sandboxed REPL.
        """
        parent_control, worker_control = socket.socketpair()

        worker = subprocess.Popen(
            [
                sys.executable, "-u", "-m", "sandbox.worker",
                " ".join(self.authorized_imports), "--control-fd",
                str(worker_control.fileno()),
            ],
            stdin=subprocess.PIPE,
            stdout=None,
            stderr=None,
            text=True,
            pass_fds=(worker_control.fileno(),),
        )

        worker_control.close()

        try:
            while True:

                line = input(Sandbox.NAME)

                if line.strip() == "exit":
                    break
                if not line.strip():
                    continue

                lines = [line]
                try:
                    finished = codeop.compile_command(line)
                except (SyntaxError):
                    pass
                else:
                    if finished is None:
                        while True:
                            next = input(".........")
                            if not next.strip():
                                break
                            lines.append(next)

                code = "\n".join(lines) + "\n"
                if worker.poll() is not None:
                    print("Sandbox worker stopped.", file=sys.stderr)
                    break

                worker.stdin.write(code + "\n")
                worker.stdin.flush()

                self._wait_return_code(parent_control, worker)

        except EOFError:
            pass
        except KeyboardInterrupt:
            print("\nBye!")
            worker.kill()
            worker.wait()
        finally:
            if worker.stdin is not None and not worker.stdin.closed:
                worker.stdin.close()
            if worker.poll() is None:
                worker.wait()

    def _wait_return_code(self, parent_control: Jsp, worker: Jsp) -> int:
        """
        This function wait and get the return code
        from a python code given in the REPL

        Returns:
            0: line executed without error
            1: line executed with one Exception
            None: if an Exception is raised

        Raises:
            SandboxError: if a timeout occurs
        """
        runtime = time.time()
        while True:
            readable, _, _ = select.select(
                [parent_control], [], [], 0.1)

            if not readable:
                if time.time() - runtime > self.timeout:
                    worker.kill()
                    worker.wait()
                    parent_control.close()
                    raise SandboxError("TimeoutExpired!")
                if worker.poll() is not None:
                    print("Worker stopped.", file=sys.stderr)
                    break
                continue

            status = parent_control.recv(1)

            if status == b"\x00":
                return 0
            elif status == b"\x01":
                return 1
            elif status == b"":
                return None
            break

    def execute(self, code: str) -> subprocess.CalledProcessError | subprocess.CompletedProcess:
        """
        Execute code in a sandboxed python environnement.

        Args:
            code (str): The python code to be executed.

        Returns:
            CalledProcessError: result of an error raised during execution
            CompletedProcess: result of a successful execution.

        Raises:
            SandboxError: when the code timeout.
        """
        try:
            result = self.container.run(
                [" ".join(self.authorized_imports), "--single"],
                self.timeout,
                code
            )

        except subprocess.TimeoutExpired:  # obsolete
            raise SandboxError("TimeoutExpired!")
        except subprocess.CalledProcessError as err:
            return err

        return result


def parse_args() -> tuple[SandboxConfig, str | None] | None:
    """
    parser with argparse to load a config template file.

    Returns:
        tuple[SandboxConfig, str]: The loaded model or default model
        with the python code to be executed.
        None: if any error has occured.
    """
    parser = argparse.ArgumentParser(
        description="CLI tool for sandbox"
    )

    parser.add_argument(
        "template",
        nargs="?",
        type=Path,
        default=None,
        help="path of the sandbox config tempate (json file)"
    )

    parser.add_argument(
        "-e", "--execute",
        type=Path,
        default=None,
        help="Execute a single python file."
    )

    model = None
    args = parser.parse_args()
    code = None

    if args.execute is not None:
        code = load_python_file(args.execute)
        if code is None:
            return None
        print(f"Running {args.execute} with sandbox...")

    if args.template:
        print(f"Loading {args.template}...")
        model = load_json_template(args.template)
    else:
        if code is None:
            print("Running sandbox's REPL with default config.")

    if model is not None:
        return model, code

    if args.template:
        print("Fallback with default config")

    return SandboxConfig(), code


def main() -> None:
    """Main function for uv run sandbox command."""

    args = parse_args()
    if args is None:
        return

    config, code = args
    sandbox = Sandbox(config)

    if code is None:
        try:
            sandbox.repl()
        except Exception as e:
            print(e)
    else:
        try:
            result = sandbox.execute(code)
        except SandboxError as e:
            print(e)
        else:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

            print(f"Code executed with exit code {result.returncode}.")


if __name__ == "__main__":
    main()
