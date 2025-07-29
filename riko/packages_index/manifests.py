import semver

class PackageVersion:

    def __init__(self, version: semver.Version, upstream_version: str, data: dict):
        self.version: semver.Version = version
        self.upstream_version: str = upstream_version
        self.data: dict = data


class Package:

    def __init__(self, name: str, versions=None):
        self.versions: list[PackageVersion]
        if versions is None:
            self.versions = []
        else:
            self.versions = versions
        self.name: str = name

    def new_version(self, version: PackageVersion):
        self.versions.append(version)


class Category:

    def __init__(self, name: str, packages=None):
        self.packages: list[Package]
        if packages is None:
            self.packages = []
        else:
            self.packages = packages
        self.name: str = name

    def new_package(self, package: Package):
        self.packages.append(package)
