import json
import logging
import semver
import tomli_w

from .config.const import ruyi_cache_dir, nvchecker_config, nvchecker_result, nvchecker_old_ver, nvchecker_new_ver, \
    ruyi_pkgs_dir
from .nvchecker.results import NvcheckerResults
from .packages_index.packages_index import PackagesIndex
from .packages_index.manifests import PackageVersion
from .ruyi_packages.ruyi_packages import RuyiPackages, UpstreamConfig

logger = logging.getLogger(__name__)

class Riko:

    def __init__(self):
        self._packages_index: PackagesIndex = PackagesIndex(ruyi_cache_dir / "ruyi" / "packages-index")
        self._ruyi_packages: RuyiPackages = RuyiPackages(ruyi_pkgs_dir)
        self._nvchecker_result: NvcheckerResults = NvcheckerResults(nvchecker_result)

    def load_from_cache(self) -> None:
        """
        Start riko from local cache
        :return:
        """
        try:
            self._ruyi_packages.load()
            self._packages_index.load()
            self._nvchecker_result.load()
        except FileNotFoundError:
            logger.warning("Riko cache not found, please run `riko check` first")

    def generate_nvchecker_config(self) -> None:
        nvchecker_cfg: dict = {
            "__config__": {
                "oldver": str(nvchecker_old_ver.name),
                "newver": str(nvchecker_new_ver.name),
            }
        }
        for c in self._ruyi_packages.get_upstreams().values():
            nvchecker_cfg[c.get_name()] = c.get_nvchecker_dat()

        with open(nvchecker_config, "wb") as f:
            tomli_w.dump(nvchecker_cfg, f)

    def generate_nvchecker_old_ver(self) -> None:
        """
        Generate old_ver.json from packages-index for nvchecker on cli.check
        :return:
        """
        self._packages_index.load()

        nvchecker_ver = 2
        old_data = {}

        for up in self._ruyi_packages.get_upstreams().values():
            name = up.get_name()
            cat = self._packages_index.get_category(up.get_category())

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

    def get_nvchecker_results(self, event_or_level: str) -> list[dict]:
        if event_or_level == "any":
            return self._nvchecker_result.get_data()
        else:
            return self._nvchecker_result.get_event_data(event_or_level)

    def get_packages_index(self) -> PackagesIndex:
        return self._packages_index

    def get_packages_index_manifest(self, category: str, pkg: str, up_ver: str) -> PackageVersion | None:
        for v in self._packages_index.get_category(category).get_package(pkg).get_versions():
            if v.upstream_version == up_ver:
                return v

        return None

    def get_ruyi_packages(self) -> RuyiPackages:
        return self._ruyi_packages

    def get_ruyi_package(self, up_name: str) -> UpstreamConfig | None:
        return self._ruyi_packages.get_upstream(up_name)


_myriko: Riko | None = None

def get_riko() -> Riko:
    global _myriko

    if _myriko is None:
        _myriko = Riko()

    return _myriko
