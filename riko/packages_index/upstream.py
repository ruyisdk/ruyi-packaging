
from .upstreams_data import board_images

class Upstream:
    def __init__(self, name: str, data: dict):
        """
        describe upstream of a set of manifests
        :param name: the name of the upstream
        :param data: a set of nvchecker config data
        """
        # nvchecker config
        self.name: str = name
        self.data: dict = data

        # empty combos
        self.combos: list[str] = []
        self.match: dict[str, str] = {}

    def set_combos(self, combos: list[str], match: dict[str, str]) -> None:
        """
        set board-image combos
        :param combos: a set of manifests(board-images), they release in same source and should be checked together
        :param match: a set of file match regex
        :return:
        """
        self.combos = combos
        self.match = match


upstreams: list[Upstream] = []

for up in board_images.items():
    upu = Upstream(up[0], up[1].get("data"))
    com_orig = up[1].get("combos")
    combos = []
    match = up[1].get("match")
    for c in com_orig:
        if match is not None and match.get(c) == "":
            match.pop(c)
            continue
        combos.append(c)

    upu.set_combos(combos, match)

    upstreams.append(upu)
