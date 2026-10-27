import json
import random

from ..config import MBPP_REDUCE_PATH


def getRandoMBPP() -> None:
    with open(MBPP_REDUCE_PATH, "r") as json_file:
        data = json.load(json_file)
    random_question = random.choice(data)
    return random_question
