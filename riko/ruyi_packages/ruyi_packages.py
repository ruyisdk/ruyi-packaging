
import os
import tomllib

from pathlib import Path
from typing import Dict, List

class UpstreamConfig:
    def __init__(self, name: str, category: str, nv_dat: Dict):
        """
        describe upstream of a set of manifests
        :param name: the name of the upstream
        :param category: refer to packages-index combo category
        :param nv_dat: a set of nvchecker config data
        """
        # nvchecker config
        self._name: str = name
        self._category: str = category
        self._nv_data: Dict = nv_dat

        # empty combos
        self._combos: List[str] = []
        self._policies: Dict[str, List[str]] = {}

    def get_name(self) -> str:
        return self._name

    def get_category(self) -> str:
        return self._category

    def get_nvchecker_dat(self) -> Dict:
        return self._nv_data

    def set_combos(self, combos: List[str], policies: Dict[str, List[str]]) -> None:
        """
        set board-image combos
        :param combos: a set of manifests(board-images), they release in same source and should be checked together
        :param policies: a set of combo policies
        :return:
        """
        self._combos = combos
        self._policies = policies

    def get_combos(self) -> List[str]:
        return self._combos

    def get_policies(self) -> Dict[str, List[str]]:
        return self._policies


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
                # check policies may not exist
                policies: Dict[str, List[str]] | None = cfg.get("policies")
                # policy "skip" presents means this combo should be ignored
                for c in com_orig:
                    if policies is not None and isinstance(policies.get(c), list) and "skip" in policies[c]:
                        policies.pop(c)
                        continue
                    combos.append(c)

                up.set_combos(combos, policies if policies is not None else {})

                self._upstream_cfg[pkg] = up

    def get_upstreams(self) -> Dict[str, UpstreamConfig]:
        return self._upstream_cfg

    def get_upstream(self, up_name: str) -> UpstreamConfig | None:
        return self._upstream_cfg.get(up_name)
