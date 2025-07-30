import semver

from typing import Dict, List

class PackageVersion:

    def __init__(self, version: semver.Version, upstream_version: str, data: Dict):
        self.version: semver.Version = version
        self.upstream_version: str = upstream_version
        self.data: Dict = data


class Package:

    def __init__(self, name: str, versions=None):
        self._versions: List[PackageVersion]
        if versions is None:
            self._versions = []
        else:
            self._versions = versions
        self.name: str = name

    def add_version(self, version: PackageVersion) -> None:
        self._versions.append(version)

    def get_versions(self) -> List[PackageVersion]:
        return self._versions


class Category:

    def __init__(self, name: str, packages=None):
        self._packages: Dict[str, Package]
        if packages is None:
            self._packages = {}
        else:
            self._packages = packages
        self._name: str = name

    def add_package(self, package: Package) -> None:
        self._packages.update({package.name: package})

    def get_package(self, name: str) -> Package | None:
        return self._packages.get(name)

    def get_name(self) -> str:
        return self._name
