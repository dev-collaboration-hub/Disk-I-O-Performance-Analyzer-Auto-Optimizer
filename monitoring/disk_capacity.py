"""Disk capacity collection."""

from __future__ import annotations

import os
import shutil
from typing import TypedDict


class DiskCapacity(TypedDict):
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int


def get_disk_capacity(path: str = os.sep) -> DiskCapacity:
    """Return total, used, and free bytes for ``path``."""

    normalized_path = os.path.abspath(path)
    usage = shutil.disk_usage(normalized_path)
    return {
        "path": normalized_path,
        "total_bytes": int(usage.total),
        "used_bytes": int(usage.used),
        "free_bytes": int(usage.free),
    }


if __name__ == "__main__":
    print(get_disk_capacity())
