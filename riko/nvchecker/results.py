import json
import os

from pathlib import Path

class NvcheckerResults:
    """
    nvchecker results json
    """
    def __init__(self, path: Path):
        self._path: Path = path
        self._data: list[dict] = []

    def load(self) -> None:
        if not os.path.exists(self._path):
            raise FileNotFoundError(self._path)

        with open(self._path) as f:
            self._data = json.load(f)

    def get_data(self) -> list[dict]:
        return self._data

    def get_event_data(self, event_or_level: str) -> list[dict]:
        """
        check event or level
        :param event_or_level:
        :return:
        """
        res = []
        for r in self._data:
            ev = r.get("event")
            lv = r.get("level")
            if ev is not None and ev == event_or_level:
                res.append(r)
            elif lv is not None and lv == event_or_level:
                res.append(r)

        return res
