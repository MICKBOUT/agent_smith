import os
from functools import lru_cache

from config import LLMProvider, Provider
from models import NoCodeBlockFound


def check_apikeys_available() -> list[Provider]:
    provider_lst = []
    for ell in LLMProvider:
        provider = ell.value
        try:
            getAPIkey(provider)
            provider_lst.append(provider)
        except ValueError:
            print(f"No key found for: {provider.NAME}")
    return provider_lst


@lru_cache(maxsize=1)
def _load_dotenv() -> None:
    from dotenv import load_dotenv
    load_dotenv()


def get_env_var(var_name: str) -> str:
    _load_dotenv()
    return os.getenv(var_name)


def getAPIkey(provider: Provider) -> str:
    _load_dotenv()
    API_KEY = os.getenv(provider.API_KEY_NAME)
    if API_KEY is None:
        raise ValueError(f"{provider.API_KEY_NAME} is not set as env variable")
    return API_KEY


def extractCode(message: str) -> str:
    start = message.find("```python")
    if start < 0:
        raise NoCodeBlockFound("no ```python block")
    start += len("```python")
    end = message.find("```", start)
    if end < 0:
        raise NoCodeBlockFound("unclosed code block")
    return message[start:end].strip()
