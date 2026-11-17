import os
from functools import lru_cache
from ..config import LLMProvider, Provider


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


def getAPIkey(provider: Provider) -> str:
    _load_dotenv()
    API_KEY = os.getenv(provider.API_KEY_NAME)
    if API_KEY is None:
        raise ValueError(f"{provider.API_KEY_NAME} is not set as env variable")
    return API_KEY
