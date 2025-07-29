from pathlib import Path

from .config.const import ruyi_cache_dir
from .packages_index.api import PackagesIndex
from .packages_index.upstream import Upstream


class Riko:

    def __init__(self):
        self.packages_index: PackagesIndex = PackagesIndex(ruyi_cache_dir / "ruyi" / "packages-index")

        self.packages_index.load()



myriko: Riko

def setup_riko():
    global myriko
    myriko = Riko()
