import psutil


def get_running_processes():
    """
    Returns a list of running processes.
    """

    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "status"]
    ):
        try:
            processes.append(
                {
                    "pid": process.info["pid"],
                    "name": process.info["name"],
                    "status": process.info["status"],
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue

    return processes


if __name__ == "__main__":
    processes = get_running_processes()

    print(f"Processes Found: {len(processes)}")
    print("-" * 40)

    for process in processes[:20]:
        print(
            f"PID={process['pid']} | "
            f"Name={process['name']} | "
            f"Status={process['status']}"
        )
