"""Notification formatting and dispatch helpers for M8."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def format_notification(event: dict[str, Any]) -> str:
    severity = str(event.get("severity", "INFO")).upper()
    event_type = str(event.get("event_type", "EVENT")).upper()
    title = str(event.get("title", "Disk I/O alert"))
    message = str(event.get("message", ""))
    return f"[{severity}] [{event_type}] {title}: {message}"


def dispatch_notifications(
    events: list[dict[str, Any]], *, output: Callable[[str], None] = print
) -> int:
    for event in events:
        output(format_notification(event))
    return len(events)
