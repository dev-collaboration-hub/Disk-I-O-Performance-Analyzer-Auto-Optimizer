from datetime import datetime

from monitoring.disk_stats import get_disk_usage
from monitoring.disk_monitor import get_disk_io_stats
from monitoring.top_disk_consumers import get_top_disk_consumers


def create_snapshot(path="/", top_process_limit=5):
    """
    Create a complete system snapshot.
    """

    disk_usage = get_disk_usage(path)
    io_stats = get_disk_io_stats()
    top_processes = get_top_disk_consumers(
        limit=top_process_limit
    )

    snapshot = {
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "disk_usage_percent": disk_usage[
            "usage_percent"
        ],
        "total_bytes": disk_usage[
            "total_bytes"
        ],
        "used_bytes": disk_usage[
            "used_bytes"
        ],
        "free_bytes": disk_usage[
            "free_bytes"
        ],
        "read_bytes": io_stats[
            "read_bytes"
        ],
        "write_bytes": io_stats[
            "write_bytes"
        ],
        "top_processes": top_processes,
    }

    return snapshot


if __name__ == "__main__":
    snapshot = create_snapshot()

    print(snapshot)
