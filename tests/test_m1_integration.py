from monitoring.disk_capacity import get_disk_capacity
from monitoring.disk_stats import get_disk_usage_percentage
from monitoring.disk_monitor import get_disk_io_stats


def run_test():
    print("Testing Disk Capacity...")
    print(get_disk_capacity())

    print("\nTesting Disk Usage...")
    print(get_disk_usage_percentage())

    print("\nTesting Disk I/O Stats...")
    print(get_disk_io_stats())

    print("\nM1 Integration Test Passed!")


if __name__ == "__main__":
    run_test()
