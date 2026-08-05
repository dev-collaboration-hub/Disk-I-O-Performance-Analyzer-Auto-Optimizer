from datetime import datetime


def build_timeline(history):
    """
    Convert stored snapshots into a timeline of events.
    """

    timeline = []

    for snapshot in history:
        timestamp = snapshot.get(
            "timestamp",
            "Unknown Time"
        )

        disk_usage = snapshot.get(
            "disk_usage_percent",
            0
        )

        event = (
            f"{timestamp} | "
            f"Disk Usage: {disk_usage}%"
        )

        timeline.append(event)

    return timeline


def print_timeline(history):
    """
    Print timeline to console.
    """

    timeline = build_timeline(history)

    print("System Activity Timeline")
    print("=" * 60)

    for event in timeline:
        print(event)


if __name__ == "__main__":

    sample_history = [
        {
            "timestamp": "2026-06-21 09:12:00",
            "disk_usage_percent": 100
        },
        {
            "timestamp": "2026-06-21 09:13:00",
            "disk_usage_percent": 98
        },
        {
            "timestamp": "2026-06-21 09:14:00",
            "disk_usage_percent": 85
        }
    ]

    print_timeline(sample_history)
