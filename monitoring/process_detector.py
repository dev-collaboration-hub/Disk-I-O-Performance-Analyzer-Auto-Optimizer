"""Cross-platform process enumeration for M2."""

from __future__ import annotations

from typing import TypedDict

import psutil


class ProcessInfo(TypedDict):
    pid: int
    name: str
    status: str
    username: str | None
    create_time: float | None


_PROCESS_EXCEPTIONS = (
    psutil.NoSuchProcess,
    psutil.AccessDenied,
    psutil.ZombieProcess,
)


def get_running_processes() -> list[ProcessInfo]:
    """Return stable, serializable metadata for accessible running processes.

    Inaccessible and short-lived processes are skipped instead of interrupting
    the entire collection cycle.
    """

    processes: list[ProcessInfo] = []
    attributes = ["pid", "name", "status", "username", "create_time"]

    for process in psutil.process_iter(attributes, ad_value=None):
        try:
            info = process.info
            processes.append(
                {
                    "pid": int(info["pid"]),
                    "name": str(info.get("name") or "<unknown>"),
                    "status": str(info.get("status") or "unknown"),
                    "username": (
                        str(info["username"]) if info.get("username") is not None else None
                    ),
                    "create_time": (
                        float(info["create_time"])
                        if info.get("create_time") is not None
                        else None
                    ),
                }
            )
        except _PROCESS_EXCEPTIONS:
            continue

    processes.sort(key=lambda item: item["pid"])
    return processes


if __name__ == "__main__":
    for item in get_running_processes():
        print(item)
