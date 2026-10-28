import sys
import subprocess

from sandbox_utils import SandboxError


class Sandbox:
    TIMEOUT = 3
    MAX_CODE_LEN = 1024

    def repl(self) -> None:
        worker = subprocess.Popen(
            [sys.executable, "-u", "src/worker.py"],
            stdin=subprocess.PIPE,
            stdout=None,
            text=True,
        )

        try:
            while True:
                import time
                time.sleep(0.01)  # fix de vieux con

                line = input('\033[1;38;2;194;178;128mSand\033[1;38;2;0;150;255mBox\033[0m> ')

                if line.strip() == "exit":
                    break

                while line.strip().endswith(":") and line.strip():
                    line = line + "\n" + input("...")

                worker.stdin.write(line + "\n")
                worker.stdin.flush()

                # result = worker.stdout.readline()

                # print(result, end="")
        except EOFError:
            print("SUCESS")
        except (KeyboardInterrupt, SystemExit):
            print("\nBye!")

    def execute(self, code: str) -> None:
        if len(code.encode("utf-8")) > self.MAX_CODE_LEN:
            raise SandboxError("lenght of code hit the limits!")

        try:
            result = subprocess.run(
                [sys.executable, "src/worker.py"],
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


def main():
    sandbox = Sandbox()
    sandbox.repl()
