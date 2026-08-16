"""Persistent rollback journal and transactional rollback for M7."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import OPTIMIZATION_JOURNAL_FILE


class OptimizationJournal:
    def __init__(self, path: str | Path = OPTIMIZATION_JOURNAL_FILE) -> None:
        self.path = Path(path)

    def append(
        self,
        event_type: str,
        *,
        session_id: str,
        payload: dict[str, Any],
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "session_id": session_id,
            "payload": payload,
        }
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
        return records

    def latest_active_session(self) -> tuple[str | None, list[dict[str, Any]]]:
        """Return rollback tokens for the most recent applied, not-ended session."""

        sessions: dict[str, list[dict[str, Any]]] = {}
        ended: set[str] = set()
        order: list[str] = []
        for record in self.load():
            session = str(record.get("session_id", ""))
            if not session:
                continue
            if session not in order:
                order.append(session)
            event = record.get("event_type")
            if event == "ACTION_APPLIED":
                token = record.get("payload", {}).get("rollback_token")
                if isinstance(token, dict):
                    sessions.setdefault(session, []).append(token)
            elif event in {"SESSION_ROLLED_BACK", "SESSION_COMMITTED"}:
                ended.add(session)

        for session in reversed(order):
            if session not in ended and sessions.get(session):
                return session, sessions[session]
        return None, []


def rollback_tokens(
    tokens: list[dict[str, Any]],
    *,
    controller: Any,
    journal: OptimizationJournal | None = None,
    session_id: str = "rollback",
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for token in reversed(tokens):
        try:
            result = controller.rollback(token)
            results.append(result)
            if journal:
                journal.append(
                    "ACTION_ROLLED_BACK",
                    session_id=session_id,
                    payload={"result": result},
                )
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}")

    if journal:
        journal.append(
            "SESSION_ROLLED_BACK",
            session_id=session_id,
            payload={"rolled_back": len(results), "errors": errors},
        )

    return {
        "status": "ROLLED_BACK" if not errors else "PARTIAL_ROLLBACK",
        "rolled_back_count": len(results),
        "errors": errors,
        "results": results,
    }
