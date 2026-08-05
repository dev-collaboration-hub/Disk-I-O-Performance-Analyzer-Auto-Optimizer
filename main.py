import time

from config.settings import (
    REFRESH_INTERVAL,
    WARNING_DISK_USAGE_PERCENT,
    CRITICAL_DISK_USAGE_PERCENT,
)

from monitoring.disk_detector import (
    get_mounted_disks as get_mounted_partitions,
)
from monitoring.disk_capacity import get_disk_capacity
from monitoring.disk_monitor import get_disk_io_stats
from monitoring.disk_stats import get_disk_usage
from utils.logger import log_event
from utils.formatter import format_size as format_bytes


def display_disk_information():
    """
    Display disk monitoring information.
    """

    print("\n" + "=" * 60)
    print("DISK I/O PERFORMANCE ANALYZER")
    print("=" * 60)

    partitions = get_mounted_partitions()

    for partition in partitions:
        print(f"\nPartition: {partition}")

        try:
            capacity = get_disk_capacity(partition)
            usage = get_disk_usage(partition)

            print(
                f"Total Space : {format_bytes(capacity['total_bytes'])}"
            )
            print(
                f"Used Space  : {format_bytes(capacity['used_bytes'])}"
            )
            print(
                f"Free Space  : {format_bytes(capacity['free_bytes'])}"
            )
            print(
                f"Disk Usage  : {usage['usage_percent']}%"
            )

            if usage["usage_percent"] >= CRITICAL_DISK_USAGE_PERCENT:
                message = (
                    f"CRITICAL: {partition} usage "
                    f"{usage['usage_percent']}%"
                )
                log_event(message)

            elif usage["usage_percent"] >= WARNING_DISK_USAGE_PERCENT:
                message = (
                    f"WARNING: {partition} usage "
                    f"{usage['usage_percent']}%"
                )
                log_event(message)

        except PermissionError:
            print("Access denied.")
        except Exception as error:
            print(f"Error: {error}")

    io_stats = get_disk_io_stats()

    print("\nDisk I/O Statistics")
    print("-" * 30)
    print(f"Read Count  : {io_stats['read_count']}")
    print(f"Write Count : {io_stats['write_count']}")
    print(
        f"Read Bytes  : "
        f"{format_bytes(io_stats['read_bytes'])}"
    )
    print(
        f"Write Bytes : "
        f"{format_bytes(io_stats['write_bytes'])}"
    )


def main():
    """
    Main monitoring loop.
    """

    log_event("Disk monitoring started.")

    while True:
        display_disk_information()
        time.sleep(REFRESH_INTERVAL)


if __name__ == "__main__":
    main()
