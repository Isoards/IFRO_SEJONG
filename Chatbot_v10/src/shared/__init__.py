"""Shared utilities module"""
from .errors import (
    OntologyError,
    ParsingError,
    ValidationError,
    LLMError,
    ActionError,
    EntityResolutionError,
)
from .logging import get_logger, log_error
from .types import Result, PaginatedResult

__all__ = [
    "OntologyError",
    "ParsingError",
    "ValidationError",
    "LLMError",
    "ActionError",
    "EntityResolutionError",
    "get_logger",
    "log_error",
    "Result",
    "PaginatedResult",
]
