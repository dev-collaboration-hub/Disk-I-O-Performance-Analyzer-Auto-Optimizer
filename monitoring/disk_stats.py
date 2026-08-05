"""Disk utilization percentage collection."""

from __future__ import annotations

import os
from typing import TypedDict

import psutil


class DiskUsage(TypedDict):
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    usage_percent: float


def get_disk_usage(path: str = os.sep) -> DiskUsage:
    """Return capacity and utilization percentage for ``path``."""

    normalized_path = os.path.abspath(path)
    usage = psutil.disk_usage(normalized_path)
    return {
        "path": normalized_path,
        "total_bytes": int(usage.total),
        "used_bytes": int(usage.used),
        "free_bytes": int(usage.free),
        "usage_percent": float(usage.percent),
    }


def get_disk_usage_percentage(path: str = os.sep) -> float:
    """Return only the disk usage percentage for compatibility and CLI use."""

    return get_disk_usage(path)["usage_percent"]


if __name__ == "__main__":
    print(get_disk_usage())
