
import os
import tomllib

from pathlib import Path
from typing import Dict, List

class UpstreamConfig:
    def __init__(self, name: str, category: str, nv_dat: Dict):
        """
        describe upstream of a set of manifests
        :param name: the name of the upstream
        :param data: a set of nvchecker config data
        """
        # nvchecker config
        self._name: str = name
        self._category: str = category
        self._nv_data: Dict = nv_dat

        # empty combos
        self._combos: List[str] = []
        self._match: Dict[str, str] = {}

    def get_name(self) -> str:
        return self._name

    def get_category(self) -> str:
        return self._category

    def get_nvchecker_dat(self) -> Dict:
        return self._nv_data

    def set_combos(self, combos: List[str], match: Dict[str, str]) -> None:
        """
        set board-image combos
        :param combos: a set of manifests(board-images), they release in same source and should be checked together
        :param match: a set of file match regex
        :return:
        """
        self._combos = combos
        self._match = match

    def get_combos(self) -> List[str]:
        return self._combos

    def get_match(self) -> Dict[str, str]:
        return self._match


class RuyiPackages:

    def __init__(self, path: Path):
        self._path: Path = path
        self._upstream_cfg: Dict[str, UpstreamConfig] = {}

    def load(self):
        if not self._path.exists():
            raise FileNotFoundError(self._path)

        for cat in os.listdir(self._path):
            for pkg in os.listdir(self._path / cat):

                with open(self._path / cat / pkg / "riko.toml", "rb") as f:
                    cfg: Dict = tomllib.load(f)

                up = UpstreamConfig(pkg, cat, cfg["nvchecker"])
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

                self._upstream_cfg[pkg] = up

    def get_upstreams(self) -> Dict[str, UpstreamConfig]:
        return self._upstream_cfg

    def get_upstream(self, up_name: str) -> UpstreamConfig | None:
        return self._upstream_cfg.get(up_name)
