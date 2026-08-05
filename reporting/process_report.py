from monitoring.top_disk_consumers import get_top_disk_consumers


def get_risk_level(percentage):
    """
    Determine risk level based on disk usage share.
    """

    if percentage >= 40:
        return "CRITICAL"

    if percentage >= 25:
        return "HIGH"

    if percentage >= 10:
        return "MEDIUM"

    return "LOW"


def generate_process_report(limit=10):
    """
    Generate a process analysis report.
    """

    processes = get_top_disk_consumers(limit)

    report = []

    for process in processes:
        report.append(
            {
                "pid": process["pid"],
                "name": process["name"],
                "read_bytes": process["read_bytes"],
                "write_bytes": process["write_bytes"],
                "total_io_bytes": process["total_io_bytes"],
                "percentage": process["percentage"],
                "risk_level": get_risk_level(
                    process["percentage"]
                ),
            }
        )

    return report


if __name__ == "__main__":
    report = generate_process_report()

    print("Process Analysis Report")
    print("=" * 70)

    for process in report:
        print(f"\nPID         : {process['pid']}")
        print(f"Process     : {process['name']}")
        print(f"Read Bytes  : {process['read_bytes']}")
        print(f"Write Bytes : {process['write_bytes']}")
        print(f"Total I/O   : {process['total_io_bytes']}")
        print(f"Share       : {process['percentage']}%")
        print(f"Risk Level  : {process['risk_level']}")
        print("-" * 70)
