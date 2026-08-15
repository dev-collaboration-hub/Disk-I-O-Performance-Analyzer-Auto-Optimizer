"""M4 process-to-cause classification rules."""

from __future__ import annotations

from typing import Any


CAUSE_DATABASE: dict[str, dict[str, str]] = {
    "searchindexer.exe": {
        "cause": "Windows Search Indexing",
        "category": "System Service",
    },
    "msmpeng.exe": {
        "cause": "Windows Defender Scan",
        "category": "Antivirus",
    },
    "svchost.exe": {
        "cause": "Windows Background Service",
        "category": "System Service",
    },
    "chrome.exe": {
        "cause": "Browser Activity",
        "category": "User Application",
    },
    "msedge.exe": {
        "cause": "Browser Activity",
        "category": "User Application",
    },
    "firefox.exe": {
        "cause": "Browser Activity",
        "category": "User Application",
    },
    "code.exe": {
        "cause": "Development Environment Activity",
        "category": "Developer Tool",
    },
    "python.exe": {
        "cause": "Python Runtime Activity",
        "category": "Developer Tool",
    },
    "python3": {
        "cause": "Python Runtime Activity",
        "category": "Developer Tool",
    },
}

_PATTERN_RULES: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("chrome", "chromium", "firefox", "msedge", "safari"), "Browser Activity", "User Application"),
    (("python",), "Python Runtime Activity", "Developer Tool"),
    (("node", "npm", "pnpm", "yarn"), "JavaScript Runtime or Build Activity", "Developer Tool"),
    (("code", "idea", "pycharm", "studio"), "Development Environment Activity", "Developer Tool"),
    (("postgres", "mysql", "mysqld", "mongod"), "Database Activity", "Database"),
    (("onedrive", "dropbox", "rclone", "syncthing"), "File Synchronization", "Background Service"),
    (("backup", "restic", "borg"), "Backup Activity", "Background Service"),
    (("defender", "antivirus", "clam"), "Antivirus Scan", "Antivirus"),
)


def _normalize_process_name(process_name: Any) -> str:
    if process_name is None:
        return ""
    name = str(process_name).strip().replace("\\", "/").split("/")[-1]
    return name.casefold()


def classify_process(process_name: Any) -> dict[str, str]:
    """Classify a process into a likely root-cause category.

    Exact rules are preferred; cross-platform pattern rules provide a useful
    fallback without pretending that an unknown process is understood.
    """

    normalized = _normalize_process_name(process_name)
    if normalized in CAUSE_DATABASE:
        return {
            **CAUSE_DATABASE[normalized],
            "matched_rule": "exact",
        }

    for patterns, cause, category in _PATTERN_RULES:
        if any(pattern in normalized for pattern in patterns):
            return {
                "cause": cause,
                "category": category,
                "matched_rule": "pattern",
            }

    return {
        "cause": "Unknown Process Activity",
        "category": "Unknown",
        "matched_rule": "unknown",
    }


if __name__ == "__main__":
    for process in (
        "chrome.exe",
        "SearchIndexer.exe",
        "python3",
        "postgres",
        "unknown.exe",
    ):
        result = classify_process(process)
        print(f"{process}: {result['cause']} ({result['category']})")
