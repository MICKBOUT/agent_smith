import json
import random

from ..config import MBPP_SANITIZED_PATH
from ..models.models_public import MBPPTaskInput


def getRandoMBPP() -> MBPPTaskInput:
    with open(MBPP_SANITIZED_PATH, "r") as json_file:
        data = json.load(json_file)
    random_question = random.choice(data)
    return MBPPTaskInput.model_validate(random_question)


if __name__ == "__main__":
    question = getRandoMBPP()
    print("task_id:", question.task_id)
    print("task_definition:", question.task_definition)
    print("function_definition:", question.function_definition)
