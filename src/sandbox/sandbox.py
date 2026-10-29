import sys
import subprocess

from ..models.exception import SandboxError


class Sandbox:
    TIMEOUT = 3
    MAX_CODE_LEN = 1024

    def repl(self) -> None:
        worker = subprocess.Popen(
            [sys.executable, "-u", "-m", "src.sandbox.worker"],
            stdin=subprocess.PIPE,
            stdout=None,
            stderr=None,
            text=True,
        )

        try:
            while True:
                import time
                time.sleep(0.1)
                line = input("\033[1m\033[38;2;194;178;128msand\033[38;2;80;150;255mbox\033[0m>")
                if line.strip() == "exit":
                    break
                if not line.strip():
                    continue

                lines = [line]
                if line.rstrip().endswith(":") or line.rstrip().endswith("\\"):
                    while True:
                        next = input(".........")
                        if not next.strip():
                            break
                        lines.append(next)

                code = "\n".join(lines) + "\n"

                if len(code.encode("utf-8")) > self.MAX_CODE_LEN:
                    print("SandboxError: code length limit exceeded", file=sys.stderr)
                    continue
                if worker.poll() is not None:
                    print("Sandbox worker stopped.", file=sys.stderr)
                    break

                worker.stdin.write(str(len(code)) + "\n" + code)
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
        if len(code.encode("utf-8")) > self.MAX_CODE_LEN:
            raise SandboxError("lenght of code hit the limits!")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "src.sandbox.worker", "--single"],
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


def main():
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
