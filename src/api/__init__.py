from .openai_api import ChatApi

__all__ = ["ChatApi"]


# # fix: this is needed if the code has a Runtime warning 'src.api.openai_api' found in sys.modules''
# def __getattr__(name: str):
#     if name == "ChatApi":
#         from .openai_api import ChatApi

#         return ChatApi
#     raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
