from datetime import datetime


def log_event(message, log_file="disk.log"):
    """
    Write an event to the log file with a timestamp.
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_file, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {message}\n")


if __name__ == "__main__":
    log_event("Disk monitoring started.")
    print("Log entry written successfully.")
