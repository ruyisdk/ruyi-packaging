import os
import semver
import tomllib

from pathlib import Path

from .manifests import Category, Package, PackageVersion

class PackagesIndex:

    def __init__(self, path: Path):
        self.path: Path = path
        self.categories: list[Category] = []

    def load(self) -> None:

        if not os.path.exists(self.path / 'manifests'):
            raise FileNotFoundError(self.path / 'manifests')

        for cat in os.listdir(self.path / 'manifests'):
            mycat = Category(cat)

            for pkg in os.listdir(self.path / 'manifests' / cat):
                mypkg = Package(pkg)

                for ver in os.listdir(self.path / 'manifests' / cat / pkg):
                    tml = self.path / 'manifests' / cat / pkg / ver
                    if tml.suffix.lower() != '.toml':
                        raise NotImplementedError(f"file type {tml.suffix.lower()} not supported")

                    data = tomllib.loads(tml.read_text())
                    version = semver.parse_version_info(tml.stem)
                    upstream_version = data.get('metadata').get('upstream_version')

                    mypkg.new_version(PackageVersion(version, upstream_version, data))

                mycat.new_package(mypkg)

            self.categories.append(mycat)
