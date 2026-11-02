import sys
import subprocess
import codeop
import readline  # noqa, for better input, do not delete

from models.exception import SandboxError


class Sandbox:
    """Basic class for sandboxing and executing python code."""
    TIMEOUT = 3

    RESET = "\001\033[0m\002"
    SAND = "\001\033[1;38;2;194;178;128m\002"
    BOX = "\001\033[1;38;2;80;150;255m\002"
    NAME = f"{SAND}sand{BOX}box{RESET}> "

    def repl(self) -> None:
        """
        launch an interactive sandboxed REPL.
        """
        worker = subprocess.Popen(
            [sys.executable, "-u", "-m", "sandbox.worker"],
            stdin=subprocess.PIPE,
            stdout=None,
            stderr=None,
            text=True,
        )

        try:
            while True:
                import time
                time.sleep(0.01)  # fix denfoire a changer le plus vite possible

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

    def execute(self, code: str) -> int:
        """
        Execute code in a sandboxed python environnement.

        Args:
            code (str): The python code to be executed.

        Returns:
            int: return_code, 0 if everything works.
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "sandbox.worker", "--single"],
                input=code,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT
            )
        except subprocess.TimeoutExpired:
            raise SandboxError("TimeoutExpired!")

        if result.stdout:
            print(result.stdout, end="")

        if result.returncode != 0:
            print(result.stderr, end="", file=sys.stderr)

        return result.returncode


def main() -> None:
    """Main function for uv run sandbox command."""
    sandbox = Sandbox()

    # with open(".dev/suspicious_code.py", "r") as f:
    #     code = f.read()
    # sandbox.execute(code)

    try:
        sandbox.repl()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
