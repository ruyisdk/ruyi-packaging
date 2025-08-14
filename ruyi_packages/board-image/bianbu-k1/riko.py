from typing import List, Dict, Tuple

from riko.api import RikoPkg, RegexUpstream


def rikoring(old_pkgs: List[RikoPkg], new_pkgs: List[RikoPkg]) -> None:
    """
    old toml stored in old_pkg, format new toml to new_pkg
    :param old_pkgs: old pkg list
    :param new_pkgs: new pkg list
    :return:
    """

    # set versions
    upstream_version_orig: str = new_pkgs[0].get_upstream_version()
    # v2.1 -> 2.1
    upstream_version = upstream_version_orig[1:]
    # 2.1 -> 2.1.0
    if upstream_version.count(".") == 1:
        upstream_version += ".0"
    assert upstream_version.count(".") == 2

    for p in new_pkgs:
        p.version = p.get_version().parse(upstream_version)

    # get files from upstream
    upstream: RegexUpstream = new_pkgs[0].get_upstream()
    assert upstream.source == "regex"
    desktop, desktop_url = upstream.get_release_assert_regex(f"^bianbu-[\\d]+\\.[\\d]+-desktop-k1-{upstream_version_orig}-release-[\\d]+.img.zip$")
    minimal, minimal_url = upstream.get_release_assert_regex(f"^bianbu-[\\d]+\\.[\\d]+-minimal-k1-{upstream_version_orig}-release-[\\d]+.img.zip$")

    for i in range(0, len(old_pkgs)):
        # set metadata.desc
        new_toml: Dict = new_pkgs[i].get_manifest()[0]
        new_toml["metadata"]["desc"] = new_toml["metadata"]["desc"].replace(old_pkgs[i].get_upstream_version(), upstream_version_orig)

        if old_pkgs[i].get_combo() == "bianbu-desktop-spacemit-k1-sd":
            new_toml["distfiles"][0]["name"] = desktop
            new_toml["distfiles"][0]["urls"] = [desktop_url]
            new_toml["blob"]["distfiles"] = [desktop]
        elif old_pkgs[i].get_combo() == "bianbu-minimal-spacemit-k1-sd":
            new_toml["distfiles"][0]["name"] = minimal
            new_toml["distfiles"][0]["urls"] = [minimal_url]
            new_toml["blob"]["distfiles"] = [minimal]
        else:
            raise RuntimeError(f"Unknown combo {old_pkgs[i].get_combo()}")

        new_pkgs[i].set_manifest_ready()
