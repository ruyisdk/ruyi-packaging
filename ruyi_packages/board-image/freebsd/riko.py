from typing import List

from riko.api import RikoPkg


def rikoring(old_pkgs: List[RikoPkg], new_pkgs: List[RikoPkg]) -> None:
    """
    old toml stored in old_pkg, format new toml to new_pkg
    :param old_pkgs: old pkg list
    :param new_pkgs: new pkg list
    :return:
    """
    urls = new_pkgs[0].get_manifest()[0]["distfiles"][0]["urls"]
    urls.append(urls[0].replace("mirror.iscas.ac.cn/FreeBSD", "download.freebsd.org"))
    urls.append(urls[0].replace("mirror.iscas.ac.cn/FreeBSD/releases", "archive.freebsd.org/old-releases"))
