"""M8 alert history and active-alert CLI report."""

from __future__ import annotations

import argparse
import json
from typing import Any

from alerts.alert_store import AlertStore
from config.settings import ALERT_FILE, ALERT_RETENTION_RECORDS


def render_alert_report(events: list[dict[str, Any]], *, active_only: bool = False) -> str:
    lines = ["ACTIVE ALERTS" if active_only else "ALERT HISTORY", "=" * 72]
    if not events:
        lines.append("No matching alert events.")
        return "\n".join(lines)
    for event in events:
        lines.append(
            f"[{event.get('severity', 'INFO')}] {event.get('event_type', 'EVENT')} | "
            f"{event.get('title', event.get('alert_key', 'alert'))}"
        )
        if event.get("message"):
            lines.append(f"  {event.get('message')}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show M8 alert history or active alerts.")
    parser.add_argument("--alert-file", default=ALERT_FILE)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--active", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    store = AlertStore(args.alert_file, max_records=ALERT_RETENTION_RECORDS)
    if args.active:
        events = list(store.active_alerts().values())
        events.sort(key=lambda item: str(item.get("emitted_at", "")))
        if args.limit < 0:
            raise ValueError("limit must be non-negative")
        events = events[-args.limit:] if args.limit else []
    else:
        events = store.load(limit=args.limit)
    if args.json:
        print(json.dumps(events, indent=2, sort_keys=True))
    else:
        print(render_alert_report(events, active_only=args.active))


if __name__ == "__main__":
    main()
