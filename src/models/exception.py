class NoCodeBlockFound(Exception):
    def __init__(self, message: str = "No code block was found in the provided input."):
        super().__init__(message)
