from typing import List, Dict, Tuple

from riko.api import RikoPkg, GithubUpstream


def rikoring(old_pkgs: List[RikoPkg], new_pkgs: List[RikoPkg]) -> None:
    """
    old toml stored in old_pkg, format new toml to new_pkg
    :param old_pkgs: old pkg list
    :param new_pkgs: new pkg list
    :return:
    """

    # First, get new toml, some items such as upstream_version will automatically set.
    # NOTE that `old_pkgs` is read only, do not modify it to prevent unexpected result
    # Note that this package only has one combo
    new_toml: Dict = new_pkgs[0].get_manifest()[0]
    upstream: GithubUpstream = new_pkgs[0].get_upstream()
    upstream_version: str = new_pkgs[0].get_upstream_version()

    assert upstream.source == "github"

    # Second, generate new version
    new_ver = old_pkgs[0].get_version().replace(minor=upstream_version, patch=0)
    new_pkgs[0].version = new_ver

    # Third, edit metadata.desc
    new_toml["metadata"]["desc"] = (
        new_toml["metadata"]["desc"].replace(old_pkgs[0].get_upstream_version(), new_pkgs[0].get_upstream_version()))

    # Fourth, get file
    assets = upstream.get_release_asserts(upstream_version)
    files: List[Tuple[str, str]] = []
    for asset in assets:
        files.append((asset.name, asset.browser_download_url))

    assert len(files) == 1
    new_toml["blob"]["distfiles"] = [files[0][0], ]
    new_toml["distfiles"][0]["name"] = files[0][0]
    new_toml["distfiles"][0]["urls"] = [files[0][1], ]

    # finally, set flag to ask riko package new one
    new_pkgs[0].set_manifest_ready()


"""
# See:
#   https://github.com/ruyisdk/packages-index/tree/main/
#       manifests/board-image/buildroot-sdk-sipeed-licheervnano/0.20250319.0.toml

format = "v1"                                                   # do not edit

[metadata]
desc = "buildroot  for LicheeRV Nano with version 20250319"     # should be manually set
vendor = { name = "Sipeed", eula = "" }
upstream_version = "20250319"                                   # automatically set before packaging()

[[distfiles]]
name = "2025-03-19-15-13-e4e133.img.xz"                         # should be manually set
size = 145585860                                                # automatically set after packaging()
urls = [                                                        # should be manually set
  "https://github.com/sipeed/LicheeRV-Nano-Build/releases/download/20250319/2025-03-19-15-13-e4e133.img.xz",
]
restrict = ["mirror"]                                           # do not edit

[distfiles.checksums]                                           # automatically set after packaging()
sha256 = "710b4235ba1da752c843bdacc350209032a54e3f4fa3cb42289d7793fe61b46b"
sha512 = "9d7e9f14dcfad4a9a4cfe5dcf8dfbeb966bfbd13b12a4ce4a01188e9912facb649f4411c849c569f6216b9358b79035cfc...<TL,DR>"

[blob]
distfiles = [                                                   # should be manually set
  "2025-03-19-15-13-e4e133.img.xz",
]

[provisionable]
strategy = "dd_v1"                                              # do not edit

[provisionable.partition_map]
disk = "2025-03-19-15-13-e4e133.img"                            # automatically set after packaging()
"""
