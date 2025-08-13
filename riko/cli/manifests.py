
import copy
import hashlib
import importlib.util
import logging
import os
import subprocess
import traceback

from typing import Dict, List

import tomli_w

from .utils import ensure_dir
from ..api import RikoPkg
from ..config.const import riko_cache_dir, riko_manifests_dir, ruyi_pkgs_dir
from ..packages_index.manifests import PackageVersion
from ..rikoriko import get_riko
from ..upstreams.github import GithubUpstream

logger = logging.getLogger(__name__)


def manifests(up_name: str, gen_vers: list[str]):
    """
    Generate packages-index manifests
    :param up_name: upstream name
    :param gen_vers: will generate versions
    :return:
    """
    res = get_riko().get_nvchecker_results("any")
    result: Dict = {}

    for r in res:
        if r.get("name") == up_name:
            result = r
            break

    # if no gen_vers given, let nvchecker deside
    if len(gen_vers) == 0:
        if result.get("name") is None:
            logger.error("No such upstream name found in nvchecker result!")
            logger.error("No manifest generated")

            return

        gen_vers.append(result["version"])

    old_ver = result["old_version"]

    logger.info(f"Generate {up_name} manifests for versions {gen_vers}")
    logger.info(f"Generate {up_name} manifests base on old version `{old_ver}`")

    # check list
    if old_ver in gen_vers:
        logger.warning(f"Remove old version `{old_ver}` from generate version list")
        gen_vers.remove(old_ver)

    if len(gen_vers) == 0:
        logger.warning("No version to be generated")
        return

    # load config
    up_cfg = get_riko().get_ruyi_package(up_name)
    if up_cfg is None:
        raise FileNotFoundError(f"No riko upstream package `{up_name}` found")

    # load old manifest
    cbs: list[str] = up_cfg.get_combos()
    vers: list[PackageVersion] = []
    for c in cbs:
        pkg_ver = get_riko().get_packages_index_manifest(up_cfg.get_category(), c, old_ver)
        if pkg_ver is None:
            raise FileNotFoundError(f"No ruyi packages-index manifest for category `{up_cfg.get_category()}` "
                                    f"package {c} version {old_ver} found")
        vers.append(pkg_ver)

    # output dir
    ensure_dir(riko_cache_dir)
    ensure_dir(riko_manifests_dir)

    # old ver
    old_versions: List[RikoPkg] = []
    for i in range(0, len(vers)):
        pkg = RikoPkg(up_cfg.get_category(), cbs[i], up_cfg.get_name(), vers[i].version, vers[i].upstream_version)
        pkg.set_manifest(vers[i].manifest)
        old_versions.append(pkg)

    # new ver
    for gv in gen_vers:
        # gv is upstream version str

        # this version
        new_versions: List[RikoPkg] = []

        # many combos
        for i in range(0, len(vers)):
            # get UpstreamLike
            nv_dat = up_cfg.get_nvchecker_dat()
            up_source = nv_dat["source"]
            if up_source == "github":
                up = GithubUpstream(nv_dat["github"])
            else:
                raise NotImplementedError(f"upstream source {up_source} not supported")

            pkg = RikoPkg(up_cfg.get_category(), cbs[i], up_cfg.get_name(), vers[i].version, gv, up)

            # automatically set new values
            # before rikoring
            ma_cp = copy.deepcopy(vers[i].manifest)
            ma_cp["metadata"]["upstream_version"] = gv
            pkg.set_manifest(ma_cp)

            new_versions.append(pkg)

        # generate new manifests for this version
        riko_py = ruyi_pkgs_dir / new_versions[0].get_category() / new_versions[0].get_upstream_name() / "riko.py"
        if not riko_py.exists():
            raise FileNotFoundError(f"{riko_py} not found")

        # call riko.py
        spec = importlib.util.spec_from_file_location("riko_py", riko_py)
        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
            rikoring = getattr(module, "rikoring")
            rikoring(old_versions, new_versions)
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            logger.error(f"Skip version `{gv}` due to previous error")
            # skip this version
            continue

        # check manifests
        for nv in new_versions:
            ma, rdy = nv.get_manifest()

            if rdy:

                # final state
                # automatically set new values
                # after rikoring

                # assign disk partition map for dd-v1
                tp = ma["provisionable"]["strategy"]
                if tp == "dd-v1":
                    ma["provisionable"]["partition_map"]["disk"] = ma["blob"]["distfiles"][0]
                else:
                    raise NotImplementedError(f"provisionable strategy {tp} not supported")

                # unpack package
                # See: https://github.com/ruyisdk/ruyi/blob/main/ruyi/ruyipkg/unpack_method.py
                tars = [".tar.gz", ".tar.bz2", ".tar.lz4", ".tar.xz", ".tar.zst", ".gz", ".bz2", ".lz4", ".xz", ".zst", ".zip"]
                for tar in tars:
                    if tp == "dd-v1":
                        if ma["provisionable"]["partition_map"]["disk"].endswith(tar):
                            ma["provisionable"]["partition_map"]["disk"] = ma["provisionable"]["partition_map"]["disk"][:-len(tar)]
                    elif tp == "fastboot-v1":
                        if ma["provisionable"]["partition_map"]["boot"].endswith(tar):
                            ma["provisionable"]["partition_map"]["boot"] = ma["provisionable"]["partition_map"]["boot"][:-len(tar)]
                        if ma["provisionable"]["partition_map"]["root"].endswith(tar):
                            ma["provisionable"]["partition_map"]["boot"] = ma["provisionable"]["partition_map"]["boot"][:-len(tar)]
                    elif tp == "fastboot-v1(lpi4a-uboot)":
                        if ma["provisionable"]["partition_map"]["uboot"].endswith(tar):
                            ma["provisionable"]["partition_map"]["uboot"] = ma["provisionable"]["partition_map"]["uboot"][:-len(tar)]

                # download files
                for i in range(0, len(ma["distfiles"])):
                    url: str = ma["distfiles"][i]["urls"][0]
                    f_loc: str = riko_cache_dir / "curl.cache"
                    cmd: List[str] = ["curl", "-L", url, "-o", str(f_loc), ]
                    env = os.environ.copy()

                    process = subprocess.Popen(cmd, env=env)
                    ret = process.wait()
                    if ret != 0:
                        raise subprocess.CalledProcessError(ret, cmd)

                    # get size
                    ma["distfiles"][i]["size"] = os.path.getsize(f_loc)

                    # calculate hash
                    sha256 = hashlib.sha256()
                    sha512 = hashlib.sha512()

                    with open(f_loc, "rb") as f:
                        while True:
                            c = f.read(4 * 1024)
                            if not c:
                                break

                            sha256.update(c)
                            sha512.update(c)

                    ma["distfiles"][i]["checksums"]["sha256"] = sha256.hexdigest()
                    ma["distfiles"][i]["checksums"]["sha512"] = sha512.hexdigest()

                # write toml
                ensure_dir(riko_manifests_dir / nv.get_category())
                ensure_dir(riko_manifests_dir / nv.get_category() / nv.get_combo())

                new_toml = riko_manifests_dir / nv.get_category() / nv.get_combo() / f"{str(nv.get_version())}.toml"
                with open(new_toml, "wb") as nt:
                    tomli_w.dump(ma, nt)

                cmd: List[str] = ["ruyi", "admin", "format-manifest", new_toml, ]
                env = os.environ.copy()

                process = subprocess.Popen(cmd, env=env)
                ret = process.wait()
                if ret != 0:
                    raise subprocess.CalledProcessError(ret, cmd)
            else:
                logger.warning(f"skip package {nv.get_combo()}")

                continue
