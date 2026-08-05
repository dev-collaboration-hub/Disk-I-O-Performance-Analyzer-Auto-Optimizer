import json
import os


class HistoryManager:
    """
    Manages historical disk activity data.
    """

    def __init__(self, history_file="history.json"):
        self.history_file = history_file

        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", encoding="utf-8") as file:
                json.dump([], file)

    def load_history(self):
        """
        Load history from file.
        """

        try:
            with open(
                self.history_file,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except Exception:
            return []

    def save_snapshot(self, snapshot):
        """
        Save a snapshot to history.
        """

        history = self.load_history()

        history.append(snapshot)

        with open(
            self.history_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                history,
                file,
                indent=4
            )

    def clear_history(self):
        """
        Clear all stored history.
        """

        with open(
            self.history_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump([], file)


if __name__ == "__main__":
    manager = HistoryManager()

    sample_snapshot = {
        "timestamp": "2026-06-21 12:00:00",
        "disk_usage_percent": 87
    }

    manager.save_snapshot(sample_snapshot)

    print(manager.load_history())
