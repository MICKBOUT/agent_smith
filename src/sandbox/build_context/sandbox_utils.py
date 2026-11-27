import json
import socket
from typing import Any, Callable
from ...mcp_tools_swebench import (
    validate_mcp_paths,
    read_file,
    edit_file,
    list_files,
    search_code,
    search_function_or_class_definition_in_code,
    find_references,
    run_command,
    get_patch
)

Builtins = dict[str, object]
NameSpace = dict[str, Builtins]
FINAL_ANSWER_MAX_BYTES = 200_000


class SandboxError(Exception):
    """Exception for sandbox-related errors."""
    RED, BOLD, RESET = "\033[31m", "\033[1m", "\033[0m"

    def __init__(self, message: str) -> None:
        super().__init__(
            f"{self.RED}{self.BOLD}SandboxError {self.RESET}: {message}"
        )


def create_safe_import(authorized_imports: list[str]) -> Callable:
    """
    wrapper function to get the safe_import callable

    Args:
        authorized_imports: list of allowed python modules.

    Returns:
        Callable: the safe import function
    """
    def safe_import(
        name,
        globals=None,
        locals=None,
        fromlist=(),
        level=0,
    ) -> Any:
        """
        Redefinition of the builtin import function.
        Allows users to import only modules defined in SafeImports.all.

        Args:
            name: Name of the module to import.
            globals: Global namespace for the import.
            locals: Local namespace for the import.
            fromlist: Objects to import from the module.
            level: Relative import level (must be 0).

        Returns:
            The imported module.

        Raises:
            SandboxError: If the module is not allowed or a relative
                        import is attempted.
        """

        if level != 0:
            raise SandboxError("Relative imports are forbidden")

        if name not in authorized_imports:
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

    return safe_import


def get_new_namespace(
    authorized_imports: list[str],
    final_answer_socket: str | None = None,
) -> NameSpace:
    """
    Build a restricted namespace.

    Args:
        authorized_imports: list of allowed python modules.
        final_answer_socket: AF UNIX socket for final answer submit.

    Returns:
        NameSpace: The new namespace.

    Raises:
        SandboxError: if a sandbox error occurs.
        TypeError: if args validation fails.
    """
    builtins = SafeBuiltins.all.copy()

    def submit_final_answer(answer: str) -> None:
        if not isinstance(answer, str):
            raise TypeError("final_answer expects a string")
        if final_answer_socket is None:
            raise SandboxError("final_answer is unavailable in this execution")

        payload = json.dumps(answer).encode("utf-8")
        if len(payload) > FINAL_ANSWER_MAX_BYTES:
            raise SandboxError("final_answer is too large")

        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sender:
            sender.connect(final_answer_socket)
            sender.send(payload)
        raise SystemExit(0)

    builtins["final_answer"] = submit_final_answer
    without_import: NameSpace = {"__builtins__": builtins}

    without_import["__builtins__"].update(
        {"__import__": create_safe_import(authorized_imports)}
    )

    return without_import


class SafeBuiltins:
    """
    This class define a dict `all`.
    it contain all allowed builtins used in the sandbox.
    """
    all = {
        # mcp functions
        "validate_mcp_paths": validate_mcp_paths,
        "read_file": read_file,
        "edit_file": edit_file,
        "list_files": list_files,
        "search_code": search_code,
        "search_function_or_class_definition_in_code": search_function_or_class_definition_in_code,
        "find_references": find_references,
        "run_command": run_command,
        "get_patch": get_patch,

        # basic types
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

        # iteration and collections
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "reversed": reversed,
        "sorted": sorted,

        # calculation
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "round": round,
        "divmod": divmod,
        "pow": pow,

        # tests
        "all": all,
        "any": any,
        "isinstance": isinstance,

        # exceptions
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "ZeroDivisionError": ZeroDivisionError,
        "IndexError": IndexError,
        "KeyError": KeyError,

        # classes
        "__build_class__": __build_class__,
        "__name__": __name__
    }
