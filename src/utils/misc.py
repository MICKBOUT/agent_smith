import json

from models import MBPPTaskInput, SWEBenchTaskInput


def getTest(question: MBPPTaskInput) -> str:
    "If question.test_imports empty, this still add a new line at the start"
    str_import = "\n".join(question.test_imports)
    str_assert = "\n".join(question.test_list)
    return "\n".join((str_import, str_assert))


def addTest(code: str, question: MBPPTaskInput) -> str:
    return "\n".join((code, getTest(question)))


def sanitizeImport(modules: list[str]) -> list[str]:
    return [ell for ell in modules if ell[:7] == "import "]


def createProgram(code: str, test_list: list[str], test_imports: list[str]) -> str:
    return "\n".join([*test_imports, code, *test_list])


def _load_question(task_file: str) -> str:
    with open(task_file) as file:
        conetent = json.load(file)
    return conetent


def load_mbpp_question(task_file: str) -> MBPPTaskInput:
    return MBPPTaskInput.model_validate(_load_question(task_file))


def load_swe_question(task_file: str) -> SWEBenchTaskInput:
    return SWEBenchTaskInput.model_validate(_load_question(task_file))
