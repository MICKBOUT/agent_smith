from ..models.exception import SandboxError


def safe_import(
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


def get_new_namespace() -> dict:
    return {
        "__builtins__": SafeBuiltins.all
    }


class SafeBuiltins:
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
