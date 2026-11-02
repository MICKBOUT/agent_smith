from ..utils.enum import LLMProvider


OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENROUTER_URL_KEY = OPENROUTER_URL + "/key"

DATASET_PATH = "datasets"
MPBB_FOLDER_PATH = DATASET_PATH + "/mbpp"
MBPP_SANITIZED_PATH = MPBB_FOLDER_PATH + "/sanitized_tasks.json"

DEFAULT_PROVIDER = LLMProvider.OPENROUTER

DEFAULT_MAX_TRY = 3
DEFAULT_REQUEST_TIMEOUT = 60  # in seconde / per request
DEFAULT_MAX_TOKEN = 1500  # per request to the llm
