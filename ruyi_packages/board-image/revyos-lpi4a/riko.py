from typing import List

from riko.api import RikoPkg, RegexUpstream


def rikoring(old_pkgs: List[RikoPkg], new_pkgs: List[RikoPkg]) -> None:
    """
    old toml stored in old_pkg, format new toml to new_pkg
    :param old_pkgs: old pkg list
    :param new_pkgs: new pkg list
    :return:
    """

    # combos share same upstream object
    upstream: RegexUpstream = new_pkgs[0].get_upstream()
    upstream_version: str = new_pkgs[0].get_upstream_version()

    assert upstream.source == "regex"

    # get files from upstream
    boot, boot_url = upstream.get_release_assert_regex("^boot-.+\\.ext4")
    root, root_url = upstream.get_release_assert_regex("^root-.+\\.ext4")
    _, uboot_8g_url = upstream.get_release_assert_substring("u-boot-with-spl-lpi4a-main.bin")
    _, uboot_16g_url = upstream.get_release_assert_substring("u-boot-with-spl-lpi4a-16g")

    for i in range(0, len(old_pkgs)):
        # new toml to edit
        new_toml = new_pkgs[i].get_manifest()[0]
        # edit metadata.desc
        new_toml["metadata"]["desc"] = (new_toml["metadata"]["desc"].replace(old_pkgs[i].get_upstream_version(),
                                        new_pkgs[i].get_upstream_version()))
        # generate new version
        new_pkgs[i].version = old_pkgs[i].get_version().replace(minor=upstream_version, patch=0)

        if old_pkgs[i].get_combo() == "revyos-sipeed-lpi4a":
            new_toml["distfiles"][0]["name"] = boot
            new_toml["distfiles"][0]["urls"] = [boot_url]
            new_toml["distfiles"][1]["name"] = root
            new_toml["distfiles"][1]["urls"] = [root_url]
            new_toml["blob"]["distfiles"] = [boot, root]
            # manually set `provisionable.partition_map` for `fastboot-v1` strategy
            # riko will help with handling .zst suffix
            new_toml["provisionable"]["partition_map"] = {"boot": boot, "root": root}

        elif old_pkgs[i].get_combo() == "uboot-revyos-sipeed-lpi4a-8g":
            # there is a rename in this toml, use old format
            bin_name = new_toml["distfiles"][0]["name"].replace(old_pkgs[i].get_upstream_version(),
                                                        new_pkgs[i].get_upstream_version())
            new_toml["distfiles"][0]["name"] = bin_name
            new_toml["blob"]["distfiles"] = [bin_name]
            new_toml["distfiles"][0]["urls"] = [uboot_8g_url]
            # provisionable.partition_map will automatically set for `fastboot-v1(lpi4a-uboot)` strategy

        elif old_pkgs[i].get_combo() == "uboot-revyos-sipeed-lpi4a-16g":
            bin_name = new_toml["distfiles"][0]["name"].replace(old_pkgs[i].get_upstream_version(),
                                                        new_pkgs[i].get_upstream_version())
            new_toml["distfiles"][0]["name"] = bin_name
            new_toml["blob"]["distfiles"] = [bin_name]
            new_toml["distfiles"][0]["urls"] = [uboot_16g_url]

        else:
            raise RuntimeError(f"Unknown combo {old_pkgs[i].get_combo()}")

        new_pkgs[i].set_manifest_ready()
