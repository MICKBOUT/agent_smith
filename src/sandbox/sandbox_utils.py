from models.exception import SandboxError

# Typing
from typing import Any
Builtins = dict[str, object]
NameSpace = dict[str, Builtins]
Jsp = Any  # me sert a changer plus tard


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


def get_new_namespace() -> NameSpace:
    """
    function to get a new namespace.

    Returns:
        NameSpace: The new namespace.
    """
    return {
        "__builtins__": SafeBuiltins.all
    }


class SafeBuiltins:
    """
    This class define a dict `all`.
    it contain all allowed builtins used in the sandbox.
    """
    all = {
        "__import__": safe_import,

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

        #  jsp si on garde ca sert a creer des classes.
        "__build_class__": __build_class__,
        "__name__": __name__
    }


class SafeImports:
    """This class contain a dict `all`.
    it contain all the allowed modules."""
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
