from monitoring.process_io_monitor import get_process_io_stats


def get_top_disk_consumers(limit=10):
    """
    Returns the top disk-consuming processes based on
    total read + write bytes.
    """

    processes = get_process_io_stats()

    for process in processes:
        process["total_io_bytes"] = (
            process["read_bytes"] +
            process["write_bytes"]
        )

    total_system_io = sum(
        process["total_io_bytes"]
        for process in processes
    )

    if total_system_io == 0:
        total_system_io = 1

    processes.sort(
        key=lambda process: process["total_io_bytes"],
        reverse=True
    )

    top_processes = []

    for process in processes[:limit]:
        percentage = (
            process["total_io_bytes"] /
            total_system_io
        ) * 100

        top_processes.append(
            {
                "pid": process["pid"],
                "name": process["name"],
                "read_bytes": process["read_bytes"],
                "write_bytes": process["write_bytes"],
                "total_io_bytes": process["total_io_bytes"],
                "percentage": round(percentage, 2),
            }
        )

    return top_processes


if __name__ == "__main__":
    consumers = get_top_disk_consumers()

    print("Top Disk Consumers")
    print("-" * 70)

    for process in consumers:
        print(
            f"{process['name']:<25} "
            f"{process['percentage']:>6}%"
        )
