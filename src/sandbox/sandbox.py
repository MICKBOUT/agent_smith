import sys
import subprocess
import codeop
import readline  # noqa, for better input, do not delete
import socket
import select
import time

from typing import Any

from models.exception import SandboxError
from models.models_public import SandboxConfig
from .docker_init import run_docker_single


Jsp = Any


class Sandbox:
    """Basic class for sandboxing and executing python code."""

    RESET = "\001\033[0m\002"
    SAND = "\001\033[1;38;2;194;178;128m\002"
    BOX = "\001\033[1;38;2;80;150;255m\002"
    NAME = f"{SAND}sand{BOX}box{RESET}> "

    def __init__(self, config: SandboxConfig) -> None:
        self.config = config
        self.timeout = config.max_execution_time_seconds
        self.authorized_imports = config.authorized_imports

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

    def execute(self, code: str) -> subprocess.CalledProcessError | None:
        """
        Execute code in a sandboxed python environnement.

        Args:
            code (str): The python code to be executed.
        """
        try:
            return_code = run_docker_single(
                [" ".join(self.authorized_imports), "--single"],
                code
            )

            if return_code != 0:
                print(f"Container failed with exit code {return_code}.")

            # UNCOMMENT FOR SIMPLE ISOLATION WITHOUT DOCKER
            # result = subprocess.run(
            #     [sys.executable, "-m", "sandbox.worker", " ".join(self.authorized_imports), "--single"],
            #     input=code,
            #     capture_output=True,
            #     text=True,
            #     timeout=self.timeout
            # )

        except subprocess.TimeoutExpired:  # obsolete
            raise SandboxError("TimeoutExpired!")
        except subprocess.CalledProcessError as err:
            return err

        return None


def main() -> None:
    """Main function for uv run sandbox command."""

    config_exemple = SandboxConfig(
        max_execution_time_seconds=3,
        authorized_imports=["math", "numpy"]
    )  # default factories in all fields.
    sandbox = Sandbox(config_exemple)

    with open(".dev/suspicious_code.py", "r") as f:
        code = f.read()

    ret = sandbox.execute(code)
    if ret is None:
        print("Successfully executed.")
    else:
        print(f"Failed with exit code {ret.returncode}.")
        print(f"{ret.stderr}")

    # try:
    #     sandbox.repl()
    # except Exception as e:
    #     print(e)


if __name__ == "__main__":
    main()
