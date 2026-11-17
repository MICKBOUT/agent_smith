from ..models import MBPPTaskInput


def getTest(question: MBPPTaskInput) -> str:
    "If question.test_imports empty, this still add a new line at the start"
    str_import = "\n".join(question.test_imports)
    str_assert = "\n".join(question.test_list)
    return "\n".join((str_import, str_assert))


def addTest(code: str, question: MBPPTaskInput) -> str:
    return "\n".join((code, getTest(question)))


def sanitizeImport(modules: list[str]):
    return [ell for ell in modules if ell[:7] == "import "]


def createProgram(code: str, test_list: list[str], test_imports: list[str] | None) -> str:
    test_imports = test_imports or []
    return "\n".join([*test_imports, code, *test_list])
