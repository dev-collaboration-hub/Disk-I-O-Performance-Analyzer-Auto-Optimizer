"""Human-readable formatting helpers."""

from __future__ import annotations


def format_size(size_bytes: float | int) -> str:
    """Convert a byte value into a compact binary unit string."""

    size = float(max(0, size_bytes))
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024

    raise AssertionError("unreachable")


# Backward-compatible alias.
format_bytes = format_size
