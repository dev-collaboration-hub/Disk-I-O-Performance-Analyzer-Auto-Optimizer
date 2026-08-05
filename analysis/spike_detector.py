SPIKE_THRESHOLD_PERCENT = 20


def detect_spikes(history):
    """
    Detect significant disk usage spikes from snapshots.
    """

    spikes = []

    if len(history) < 2:
        return spikes

    for index in range(1, len(history)):

        previous = history[index - 1]
        current = history[index]

        previous_usage = previous.get(
            "disk_usage_percent",
            0
        )

        current_usage = current.get(
            "disk_usage_percent",
            0
        )

        difference = (
            current_usage - previous_usage
        )

        if difference >= SPIKE_THRESHOLD_PERCENT:

            spikes.append(
                {
                    "timestamp": current.get(
                        "timestamp"
                    ),
                    "previous_usage": previous_usage,
                    "current_usage": current_usage,
                    "difference": difference,
                    "event": "DISK_SPIKE_DETECTED",
                }
            )

    return spikes


def print_spikes(history):
    """
    Display detected spikes.
    """

    spikes = detect_spikes(history)

    print("Disk Spike Report")
    print("=" * 60)

    if not spikes:
        print("No spikes detected.")
        return

    for spike in spikes:
        print(
            f"Time      : {spike['timestamp']}"
        )
        print(
            f"Previous  : "
            f"{spike['previous_usage']}%"
        )
        print(
            f"Current   : "
            f"{spike['current_usage']}%"
        )
        print(
            f"Increase  : "
            f"{spike['difference']}%"
        )
        print(
            f"Event     : "
            f"{spike['event']}"
        )
        print("-" * 60)


if __name__ == "__main__":

    sample_history = [
        {
            "timestamp": "2026-06-21 09:12:00",
            "disk_usage_percent": 42,
        },
        {
            "timestamp": "2026-06-21 09:13:00",
            "disk_usage_percent": 47,
        },
        {
            "timestamp": "2026-06-21 09:14:00",
            "disk_usage_percent": 91,
        },
        {
            "timestamp": "2026-06-21 09:15:00",
            "disk_usage_percent": 95,
        },
    ]

    print_spikes(sample_history)
