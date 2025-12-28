"""
Core infrastructure for type-safe prompt execution.
"""

from .base import BasePrompt, TInput, TOutput
from .executor import PromptExecutor

__all__ = [
    "BasePrompt",
    "TInput",
    "TOutput",
    "PromptExecutor",
]
