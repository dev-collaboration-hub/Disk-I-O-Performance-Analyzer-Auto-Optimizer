CAUSE_DATABASE = {
    "SearchIndexer.exe": {
        "cause": "Windows Search Indexing",
        "category": "System Service",
    },
    "MsMpEng.exe": {
        "cause": "Windows Defender Scan",
        "category": "Antivirus",
    },
    "svchost.exe": {
        "cause": "Windows Background Service",
        "category": "System Service",
    },
    "chrome.exe": {
        "cause": "Browser Activity",
        "category": "User Application",
    },
    "Code.exe": {
        "cause": "Development Environment Activity",
        "category": "User Application",
    },
    "python.exe": {
        "cause": "Python Script Activity",
        "category": "User Application",
    },
}


def classify_process(process_name):
    """
    Classify a process into a likely root cause.
    """

    return CAUSE_DATABASE.get(
        process_name,
        {
            "cause": "Unknown Activity",
            "category": "Unknown",
        }
    )


if __name__ == "__main__":

    processes = [
        "chrome.exe",
        "SearchIndexer.exe",
        "python.exe",
        "unknown.exe",
    ]

    for process in processes:
        result = classify_process(process)

        print(f"Process : {process}")
        print(f"Cause   : {result['cause']}")
        print(f"Category: {result['category']}")
        print("-" * 40)
