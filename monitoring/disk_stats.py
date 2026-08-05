import psutil


def get_disk_usage(path="/"):
    """
    Returns disk usage statistics for the specified path.
    """

    usage = psutil.disk_usage(path)

    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "usage_percent": usage.percent,
    }


if __name__ == "__main__":
    stats = get_disk_usage()

    print("Disk Usage Statistics")
    print("-" * 30)

    for key, value in stats.items():
        print(f"{key}: {value}")
