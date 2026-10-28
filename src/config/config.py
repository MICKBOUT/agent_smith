from ..utils.enum import LLMProvider


OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENROUTER_URL_KEY = OPENROUTER_URL + "/key"

DATASET_PATH = "datasets"
MPBB_FOLDER_PATH = DATASET_PATH + "/mbpp"
MBPP_SANITIZED_PATH = MPBB_FOLDER_PATH + "/sanitized_tasks.json"

DEFAULT_PROVIDER = LLMProvider.OPENROUTER
