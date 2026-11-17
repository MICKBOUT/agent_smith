from enum import Enum
from abc import ABC


class Provider(ABC):
    API_KEY_NAME = ""
    URL = ""
    MODEL_NAME = ""
    NAME = ""


class UserProvider(Provider):
    API_KEY_NAME = "API_KEY"
    NAME = "UserProvider"

    def __init__(self, provider_url: str, model_name: str):
        self.URL = provider_url
        self.MODEL_NAME = model_name


class GeminiProvider(Provider):
    API_KEY_NAME = "GEMINI_API_KEY"
    URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    MODEL_NAME = "gemini-3.5-flash-lite"
    NAME = "Gemini"


class OpenRouterProvider(Provider):
    API_KEY_NAME = "OPENROUTER_API_KEY"
    URL = "https://openrouter.ai/api/v1"
    MODEL_NAME = "dots-studio/dots-3-note-preview:free"
    NAME = "OpenRouter"


class TogetherIaProvider(Provider):
    API_KEY_NAME = "TOGETHER_API_KEY"
    URL = "https://api.together.ai/v1"
    MODEL_NAME = "Prism-ML/Ternary-Bonsai-27B"
    NAME = "TogetherIa"


class GroqProvider(Provider):
    API_KEY_NAME = "GROQ_API_KEY"
    URL = "https://api.groq.com/openai/v1"
    MODEL_NAME = "qwen/qwen3.8-27b"
    NAME = "groq"


class CoherProvider(Provider):
    API_KEY_NAME = "COHER_API_KEY"
    URL = "https://api.cohere.ai/compatibility/v1"
    MODEL_NAME = "command-a-plus-05-2026"
    NAME = "Coher"


class OpenAIProvider(Provider):
    API_KEY_NAME = "OPENAI_API_KEY"
    URL = "https://api.openai.com/v1"
    MODEL_NAME = "gpt-5.5"
    NAME = "OpenAi"


class LLMProvider(Enum):
    GEMIN = GeminiProvider()
    OPENROUTER = OpenRouterProvider()
    TOGETHERIA = TogetherIaProvider()
    GROQ = GroqProvider()
    COHER = CoherProvider()
    OPENAI = OpenAIProvider()
