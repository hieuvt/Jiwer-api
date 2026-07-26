"""Custom application exceptions (filled in later phases)."""


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, *, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AlignmentError(AppError):
    """Raised when Gemini alignment fails or cannot produce valid pairs."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message, status_code=status_code)


class GeminiUnavailableError(AppError):
    """Raised when Gemini API is unreachable or returns an error."""

    def __init__(self, message: str = "Gemini API unavailable") -> None:
        super().__init__(message, status_code=502)


class GeminiConfigError(AppError):
    """Raised when GEMINI_API_KEY (or related config) is missing."""

    def __init__(self, message: str = "GEMINI_API_KEY is not configured") -> None:
        super().__init__(message, status_code=503)
