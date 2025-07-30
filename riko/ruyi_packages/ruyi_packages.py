
import os
import tomllib

from pathlib import Path

class Upstream:
    def __init__(self, name: str, category: str, data: dict):
        """
        describe upstream of a set of manifests
        :param name: the name of the upstream
        :param data: a set of nvchecker config data
        """
        # nvchecker config
        self._name: str = name
        self._category: str = category
        self._data: dict = data

        # empty combos
        self._combos: list[str] = []
        self._match: dict[str, str] = {}

    def get_name(self) -> str:
        return self._name

    def get_category(self) -> str:
        return self._category

    def get_data(self) -> dict:
        return self._data

    def set_combos(self, combos: list[str], match: dict[str, str]) -> None:
        """
        set board-image combos
        :param combos: a set of manifests(board-images), they release in same source and should be checked together
        :param match: a set of file match regex
        :return:
        """
        self._combos = combos
        self._match = match

    def get_combos(self) -> list[str]:
        return self._combos

    def get_match(self) -> dict[str, str]:
        return self._match


class RuyiPackages:

    def __init__(self, path: Path):
        self._path: Path = path
        self._upstream: list[Upstream] = []

    def load(self):
        if not self._path.exists():
            raise FileNotFoundError(self._path)

        for cat in os.listdir(self._path):
            for pkg in os.listdir(self._path / cat):

                with open(self._path / cat / pkg / "riko.toml", "rb") as f:
                    cfg: dict = tomllib.load(f)

                up = Upstream(pkg, cat, cfg["nvchecker"])
                if cat != "board-image":
                    raise NotImplementedError(f"Category {cat} not implemented")

                com_orig = cfg["entities"]["image-combo"]
                combos = []
                # match may not exist
                match = cfg.get("match")
                # match present and is "" means this combo should be ignored
                for c in com_orig:
                    if match is not None and match.get(c) == "":
                        match.pop(c)
                        continue
                    combos.append(c)

                up.set_combos(combos, match)

                self._upstream.append(up)

    def get_upstreams(self) -> list[Upstream]:
        return self._upstream
