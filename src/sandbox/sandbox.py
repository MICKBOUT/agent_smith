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
import tempfile
import uuid

from pathlib import Path

from models import SandboxError
from models import SandboxConfig

from .docker_init import Container, CONTROL_SOCKET
from .sandbox_loader import load_python_file, load_json_template


class Sandbox:
    """Basic class for sandboxing and executing python code."""

    RESET = "\001\033[0m\002"
    SAND = "\001\033[1;38;2;194;178;128m\002"
    BOX = "\001\033[1;38;2;80;150;255m\002"
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

    def __init__(self, config: SandboxConfig) -> None:
        """
        init the config and init the container.

        Args:
            config: The sandbox config.
        """
        print(self.LOGO)
        self.config = config
        self.timeout = config.max_execution_time_seconds
        self.authorized_imports = config.authorized_imports
        self.max_memory = config.max_memory_mb

        self.container = Container()

    def repl(self) -> None:
        """
        launch an interactive sandboxed REPL.
        """
        temporary_directory = tempfile.TemporaryDirectory(
            prefix="sandbox-control-"
        )
        control_directory = Path(temporary_directory.name)
        control_directory.chmod(0o711)

        socket_path = control_directory / Path(CONTROL_SOCKET).name
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(socket_path))
        socket_path.chmod(0o666)
        listener.listen(1)
        listener.settimeout(0.2)  # its for recv and accept ops

        worker = None
        control = None
        container_name = f"agent-smith-repl-{uuid.uuid4().hex[:12]}"

        try:
            worker, container_name = self.container.run_interactive(
                [" ".join(self.authorized_imports)],
                control_directory,
                self.config.max_memory_mb,
                self.config.allowed_directories,
            )

            startup_deadline = time.monotonic() + 10
            while control is None:
                try:
                    control, _ = listener.accept()
                except socket.timeout:
                    if worker.poll() is not None:
                        raise RuntimeError(
                            "The Docker worker stopped before connecting with"
                            f"exit code {worker.returncode}."
                        )
                    if time.monotonic() >= startup_deadline:
                        raise TimeoutError(
                            "The Docker worker did not connect to its "
                            "Unix control socket."
                        )

            while True:
                if worker.poll() is not None:
                    print("Sandbox worker stopped.", file=sys.stderr)
                    break

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
                control.sendall((code + "\n").encode("utf-8"))
                self._wait_return_code(control, worker, container_name)
                time.sleep(0.001)

        except EOFError:
            pass
        except KeyboardInterrupt:
            print("\nBye!")
        finally:
            if control is not None:
                control.close()
            listener.close()
            if worker is not None:
                self.container.stop_interactive(worker, container_name)
            temporary_directory.cleanup()

    def _wait_return_code(
        self,
        control: socket.socket,
        worker: subprocess.Popen[bytes],
        container_name: str,
    ) -> int:
        """
        Wait for the worker's one-byte status for the submitted code block.

        Args:
            control: the AF socket.
            worker: child process.
            container_name: container name.

        Returns:
            0: code executed without an exception
            1: code raised an exception

        Raises:
            SandboxError: if a timeout occurs
        """
        runtime = time.monotonic()
        while True:
            readable, _, _ = select.select(
                [control], [], [], 0.1)

            if not readable:
                if time.monotonic() - runtime > self.timeout:
                    self.container.stop_interactive(
                        worker,
                        container_name,
                        force=True,
                    )
                    raise SandboxError("TimeoutExpired!")
                if worker.poll() is not None:
                    print("Worker stopped.", file=sys.stderr)
                    raise RuntimeError("Sandbox worker stopped.")
                continue

            status = control.recv(1)

            if status == b"\x00":
                return 0
            elif status == b"\x01":
                return 1
            elif status == b"":
                raise RuntimeError("Sandbox worker closed the control socket.")
            raise RuntimeError(f"Unknown worker status: {status!r}")

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
                self.max_memory,
                code
            )

        except subprocess.TimeoutExpired:
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
