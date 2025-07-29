from pathlib import Path

from .config.const import ruyi_cache_dir
from .packages_index.api import PackagesIndex


class Riko:
    packages_index: PackagesIndex

    def __init__(self):
        packages_index = PackagesIndex(ruyi_cache_dir / "ruyi" / "packages-index")
        packages_index.load()

myriko: Riko

def setup_riko():
    global myriko
    myriko = Riko()
