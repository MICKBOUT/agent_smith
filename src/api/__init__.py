__all__ = ["generateSandboxReadyCode"]

# fix: this is needed if the code has a Runtime warning 'src.api.openai_api' found in sys.modules''
# def __getattr__(name: str):
#     if name == "generateSandboxReadyCode":
#         from .openai_api import generateSandboxReadyCode

#         return generateSandboxReadyCode
#     raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
