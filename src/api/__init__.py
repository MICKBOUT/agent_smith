from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .openai_api import ChatApi


__all__ = ["ChatApi"]

# only if the scripte allow call to api modul
def __getattr__(name: str):
    if name == "ChatApi":
        from .openai_api import ChatApi

        return ChatApi
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
