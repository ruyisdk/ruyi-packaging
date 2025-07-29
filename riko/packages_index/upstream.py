
from .upstreams_data import board_images

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


_upstreams: list[Upstream] = []

def _gen_upstreams() -> None:

    for up in board_images.items():
        upu = Upstream(up[0], up[1]["category"], up[1]["data"])
        com_orig = up[1]["combos"]
        combos = []
        match = up[1].get("match")
        for c in com_orig:
            if match is not None and match.get(c) == "":
                match.pop(c)
                continue
            combos.append(c)

        upu.set_combos(combos, match)

        _upstreams.append(upu)

def get_upstreams() -> list[Upstream]:
    return _upstreams

_gen_upstreams()
