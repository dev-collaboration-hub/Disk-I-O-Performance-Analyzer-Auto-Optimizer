"""Structured error contracts for the scratch rebuild.

Errors crossing core boundaries carry machine-readable codes and deterministic
context. Later layers should branch on codes, not parse exception strings.
"""

from __future__ import annotations

from enum import Enum
from typing import Mapping, TypeAlias


ContextValue: TypeAlias = str | int | float | bool | None


class CoreErrorCode(str, Enum):
    INVALID_CONFIG = "INVALID_CONFIG"
    CONTRACT_VIOLATION = "CONTRACT_VIOLATION"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CollectorErrorCode(str, Enum):
    UNSUPPORTED = "UNSUPPORTED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID_DATA = "INVALID_DATA"
    IO_ERROR = "IO_ERROR"


def _normalize_context(
    context: Mapping[str, ContextValue] | None,
) -> tuple[tuple[str, ContextValue], ...]:
    if context is None:
        return ()

    normalized: list[tuple[str, ContextValue]] = []
    for key in sorted(context):
        if not key or not key.strip():
            raise ValueError("error context keys must be non-empty")
        normalized.append((key, context[key]))
    return tuple(normalized)


class CoreError(RuntimeError):
    """Base error with stable code, operation, retryability, and context."""

    def __init__(
        self,
        code: CoreErrorCode | CollectorErrorCode,
        operation: str,
        message: str,
        *,
        retryable: bool = False,
        context: Mapping[str, ContextValue] | None = None,
    ) -> None:
        if not operation or not operation.strip():
            raise ValueError("operation must be non-empty")
        if not message or not message.strip():
            raise ValueError("message must be non-empty")

        self.code = code
        self.operation = operation
        self.detail = message
        self.retryable = retryable
        self.context = _normalize_context(context)
        super().__init__(f"{code.value}: {operation}: {message}")


class ConfigurationError(CoreError):
    """Invalid or unreadable scratch-runtime configuration."""

    def __init__(
        self,
        operation: str,
        message: str,
        *,
        context: Mapping[str, ContextValue] | None = None,
    ) -> None:
        super().__init__(
            CoreErrorCode.INVALID_CONFIG,
            operation,
            message,
            retryable=False,
            context=context,
        )


class CollectorError(CoreError):
    """Explicit failure crossing a platform collector boundary."""

    def __init__(
        self,
        code: CollectorErrorCode,
        operation: str,
        message: str,
        *,
        platform: object | None = None,
        retryable: bool = False,
        context: Mapping[str, ContextValue] | None = None,
    ) -> None:
        self.platform = platform
        merged_context = dict(context or {})
        if platform is not None:
            platform_value = getattr(platform, "value", platform)
            merged_context.setdefault("platform", str(platform_value))
        super().__init__(
            code,
            operation,
            message,
            retryable=retryable,
            context=merged_context,
        )
