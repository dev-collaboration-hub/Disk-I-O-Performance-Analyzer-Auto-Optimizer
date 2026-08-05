import psutil


def get_process_io_stats():
    """
    Returns disk I/O statistics for all accessible processes.
    """

    process_stats = []

    for process in psutil.process_iter(
        ["pid", "name"]
    ):
        try:
            io = process.io_counters()

            process_stats.append(
                {
                    "pid": process.info["pid"],
                    "name": process.info["name"],
                    "read_bytes": io.read_bytes,
                    "write_bytes": io.write_bytes,
                    "read_count": io.read_count,
                    "write_count": io.write_count,
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
            AttributeError,
        ):
            continue

    return process_stats


if __name__ == "__main__":
    processes = get_process_io_stats()

    print("Process I/O Statistics")
    print("-" * 60)

    for process in processes[:20]:
        print(
            f"PID={process['pid']} | "
            f"Name={process['name']} | "
            f"Read={process['read_bytes']} | "
            f"Write={process['write_bytes']}"
        )
