from enum import Enum
from abc import ABC


class Provider(ABC):
    API_KEY_NAME = ""
    URL = ""
    DEFAULT_MODEL = ""


class OpenAIProvider(Provider):
    API_KEY_NAME = "OPENAI_API_KEY"
    URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-5.5"


class GeminiProvider(Provider):
    API_KEY_NAME = "GEMINI_API_KEY"
    URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    DEFAULT_MODEL = "gemini-3.5-flash-lite"


class OpenRouterProvider(Provider):
    API_KEY_NAME = "OPENROUTER_API_KEY"
    URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "poolside/laguna-s-2.1"


class TogetherIaProvider(Provider):
    API_KEY_NAME = "TOGETHER_API_KEY"
    URL = "https://api.together.ai/v1"
    DEFAULT_MODEL = "Prism-ML/Ternary-Bonsai-27B"


class GroqProvider(Provider):
    API_KEY_NAME = "GROQ_API_KEY"
    URL = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL = "qwen/qwen3.8-27b"


class CoherProvider(Provider):
    API_KEY_NAME = "COHER_API_KEY"
    URL = "https://api.cohere.ai/compatibility/v1"
    DEFAULT_MODEL = "command-a-plus-05-2026"


class LLMProvider(Enum):
    GEMIN = GeminiProvider
    OPENROUTER = OpenRouterProvider
    TOGETHERIA = TogetherIaProvider
    GROQ = GroqProvider
    COHER = CoherProvider
    OPENAI = OpenAIProvider
