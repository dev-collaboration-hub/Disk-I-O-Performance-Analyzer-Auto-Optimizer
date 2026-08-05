import shutil

def get_disk_capacity(path):
    """
    Returns total, used, and free space in bytes.
    """

    usage = shutil.disk_usage(path)

    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free
    }


if __name__ == "__main__":
    disk = "/"

    stats = get_disk_capacity(disk)

    print(f"Total: {stats['total']} bytes")
    print(f"Used : {stats['used']} bytes")
    print(f"Free : {stats['free']} bytes")
