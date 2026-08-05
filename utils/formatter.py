def format_size(size_bytes):
    """
    Convert bytes into a human-readable format.
    Example:
    1073741824 -> 1.00 GB
    """

    units = ["B", "KB", "MB", "GB", "TB", "PB"]

    size = float(size_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024


if __name__ == "__main__":
    print(format_size(1024))
    print(format_size(1048576))
    print(format_size(1073741824))
