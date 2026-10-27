import sys
import subprocess


class SandboxError(Exception):
    RED, BOLD, RESET = "\033[31m", "\033[1m", "\033[0m"

    def __init__(self, message: str):
        super().__init__(
            f"{self.RED}{self.BOLD}SandboxError {self.RESET}: {message}"
        )


class Sandbox:
    TIMEOUT = 3
    MAX_CODE_LEN = 1024

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
        # try:
        #     exec(
        #         code,
        #         self.namespace,
        #         self.namespace,
        #     )
        # except NameError as e:
        #     raise SandboxError(str(e))

    def get_builtins(self):
        safe_builtins = SafeBuiltins.all.copy()

        safe_builtins.update(
            {"__import__": Sandbox._safe_import}
        )

        return safe_builtins

    def get_imports(self):
        return SafeImports.all.copy()

    @staticmethod
    def _safe_import(
        name,
        globals=None,
        locals=None,
        fromlist=(),
        level=0,
    ):
        if level != 0:
            raise SandboxError("Relative imports are forbidden")

        if name not in SafeImports.all:
            raise SandboxError(
                f"Import of module '{name}' is not allowed!"
            )

        return __import__(
            name,
            globals,
            locals,
            fromlist,
            level,
        )


class SafeBuiltins:
    all = {
        "__import__": Sandbox._safe_import,

        # STDOUT # JSPPPP
        "print": print,

        # Types fondamentaux
        "bool": bool,
        "int": int,
        "float": float,
        "complex": complex,
        "str": str,
        "bytes": bytes,
        "list": list,
        "tuple": tuple,
        "dict": dict,
        "set": set,
        "frozenset": frozenset,

        # Itération et collections
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "reversed": reversed,
        "sorted": sorted,

        # Calculs
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "round": round,
        "divmod": divmod,
        "pow": pow,

        # Tests et conversions
        "all": all,
        "any": any,
        "isinstance": isinstance,

        # Exceptions utiles
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "ZeroDivisionError": ZeroDivisionError,
        "IndexError": IndexError,
        "KeyError": KeyError,
    }


class SafeImports:
    all = frozenset({
        "math",
        "statistics",
        "decimal",
        "fractions",
        "json",
        "datetime",
        "re",
        "collections",
        "itertools",
    })


if __name__ == "__main__":
    """
    To test the sanbox, I use the file:
    .dev/suspicious_code.py
    and just execute python3 sandbox.py
    all the code in this file will be executed in the sandbox.

    """
    with open(".dev/suspicious_code.py", "r") as f:
        code = f.read()

    sandbox_1 = Sandbox()
    try:
        sandbox_1.execute(code)
    except SandboxError as e:
        print(e)
