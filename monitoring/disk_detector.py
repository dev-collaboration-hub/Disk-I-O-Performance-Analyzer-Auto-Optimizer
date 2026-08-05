"""Mounted disk discovery utilities."""

from __future__ import annotations

import os
from collections.abc import Iterable

import psutil


def _unique_mountpoints(partitions: Iterable[object]) -> list[str]:
    mountpoints: list[str] = []
    seen: set[str] = set()

    for partition in partitions:
        mountpoint = os.path.abspath(str(partition.mountpoint))
        normalized = os.path.normcase(os.path.normpath(mountpoint))
        if normalized in seen:
            continue
        seen.add(normalized)
        mountpoints.append(mountpoint)

    return mountpoints


def get_mounted_disks(include_pseudo: bool = False) -> list[str]:
    """Return accessible mounted disk paths on Windows, Linux, and macOS.

    ``psutil.disk_partitions(all=False)`` excludes most pseudo and duplicate
    filesystems. A platform root is returned as a safe fallback in restricted
    containers where partition discovery can be empty.
    """

    partitions = psutil.disk_partitions(all=include_pseudo)
    mountpoints = _unique_mountpoints(partitions)

    if mountpoints:
        return mountpoints

    fallback = os.path.abspath(os.sep)
    return [fallback]


# Compatibility alias used by earlier code and external callers.
get_mounted_partitions = get_mounted_disks


if __name__ == "__main__":
    for disk in get_mounted_disks():
        print(disk)
