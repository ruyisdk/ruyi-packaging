import json
import logging
import semver
import tomli_w

from .config.const import ruyi_cache_dir, nvchecker_config, nvchecker_old_ver, nvchecker_new_ver
from .packages_index.packages_index import PackagesIndex
from .packages_index.upstream import Upstream, get_upstreams

logger = logging.getLogger(__name__)

class Riko:

    def __init__(self):
        self.packages_index: PackagesIndex = PackagesIndex(ruyi_cache_dir / "ruyi" / "packages-index")
        self.upstreams: list[Upstream] = get_upstreams()

    def load_from_cache(self) -> None:
        """
        Start riko from local cache
        :return:
        """
        try:
            self.packages_index.load()
        except FileNotFoundError:
            logger.warning("Riko cache not found, please run `riko check` first")

    def generate_nvchecker_config(self) -> None:
        nvchecker_cfg: dict = {
            "__config__": {
                "oldver": str(nvchecker_old_ver.name),
                "newver": str(nvchecker_new_ver.name),
            }
        }
        for c in self.upstreams:
            nvchecker_cfg[c.get_name()] = c.get_data()

        with open(nvchecker_config, "wb") as f:
            tomli_w.dump(nvchecker_cfg, f)

    def generate_nvchecker_old_ver(self) -> None:
        """
        Generate old_ver.json from packages-index for nvchecker on cli.check
        :return:
        """
        self.packages_index.load()

        nvchecker_ver = 2
        old_data = {}

        for up in self.upstreams:
            name = up.get_name()
            cat = self.packages_index.get_category(up.get_category())

            # find latest version among all combos
            version = semver.Version(0, 0, 0)
            upstream_version = ""
            for pkg in up.get_combos():
                vers = cat.get_package(pkg).get_versions()

                for ver in vers:
                    if ver.version.compare(version) > 0:
                        if ver.upstream_version is None or ver.upstream_version == "":
                            continue
                        version = ver.version
                        upstream_version = ver.upstream_version

            old_data[name] = {"version": upstream_version}

        format_data = {
            "version": nvchecker_ver,
            "data": old_data,
        }

        with open(nvchecker_old_ver, "w") as f:
            json.dump(format_data, f, indent=2)


_myriko: Riko | None = None

def get_riko() -> Riko:
    global _myriko

    if _myriko is None:
        _myriko = Riko()

    return _myriko
