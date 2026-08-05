import psutil


def get_disk_io_stats():
    """
    Returns system-wide disk I/O statistics.
    """

    io = psutil.disk_io_counters()

    return {
        "read_count": io.read_count,
        "write_count": io.write_count,
        "read_bytes": io.read_bytes,
        "write_bytes": io.write_bytes,
        "read_time_ms": io.read_time,
        "write_time_ms": io.write_time,
    }


if __name__ == "__main__":
    stats = get_disk_io_stats()

    print("Disk I/O Statistics")
    print("-" * 30)

    for key, value in stats.items():
        print(f"{key}: {value}")
