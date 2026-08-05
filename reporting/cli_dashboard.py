import os
import time

from monitoring.disk_capacity import get_disk_capacity
from monitoring.disk_stats import get_disk_usage_percentage
from monitoring.disk_monitor import get_disk_io_stats


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def display_dashboard():
    while True:
        clear_screen()

        capacity = get_disk_capacity()
        usage = get_disk_usage_percentage()
        io_stats = get_disk_io_stats()

        print("=" * 50)
        print("   Disk I/O Performance Analyzer Dashboard")
        print("=" * 50)

        print(f"Disk Capacity : {capacity}")
        print(f"Disk Usage    : {usage}%")

        print("\nI/O Statistics")
        print("-" * 50)
        print(f"Read Speed    : {io_stats['read_rate']} MB/s")
        print(f"Write Speed   : {io_stats['write_rate']} MB/s")

        print("\nSystem Status")
        print("-" * 50)

        if usage >= 90:
            status = "CRITICAL"
        elif usage >= 70:
            status = "WARNING"
        else:
            status = "NORMAL"

        print(f"Status        : {status}")

        print("\nRefreshing every 2 seconds...")
        print("=" * 50)

        time.sleep(2)


if __name__ == "__main__":
    display_dashboard()
