class LLMError(Exception):
    """Base exception for LLM errors."""
    pass

class LLMRetryableError(LLMError):
    """Errors that can be retried (e.g., rate limits, timeouts)."""
    pass

class LLMFatalError(LLMError):
    """Errors that should not be retried (e.g., invalid API key, bad request)."""
    pass
