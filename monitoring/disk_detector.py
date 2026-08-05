import os
import platform

def get_mounted_disks():
    """
    Returns a list of mounted disk partitions.
    Works on Windows, Linux, and macOS.
    """

    system = platform.system()

    if system == "Windows":
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    else:  # Linux / macOS
        mounts = []

        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    mount_point = parts[1]

                    if mount_point not in mounts:
                        mounts.append(mount_point)

        except FileNotFoundError:
            mounts.append("/")

        return mounts


if __name__ == "__main__":
    disks = get_mounted_disks()

    print("Mounted Disks / Partitions:")
    for disk in disks:
        print(f"- {disk}")
