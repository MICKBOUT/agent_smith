class NoCodeBlockFound(Exception):
    def __init__(self, message: str = "No code block was found in the provided input."):
        super().__init__(message)


class NoneMessageError(Exception):
    def __init__(self, message: str = "The model returned an empty or None message"):
        super().__init__(message)


class SandboxError(Exception):
    RED, BOLD, RESET = "\033[31m", "\033[1m", "\033[0m"

    def __init__(self, message: str):
        super().__init__(
            f"{self.RED}{self.BOLD}SandboxError {self.RESET}: {message}"
        )


# class MaxTryReachError(Exception):
#     def __init__(self, message: str = "The maximum number of exception has been reach"):
#         super().__init__(message)
