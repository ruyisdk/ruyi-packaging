
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
from ..upstreams.regex import RegexUpstream

logger = logging.getLogger(__name__)


def manifests(up_name: str, gen_vers: list[str], down_grade: bool):
    """
    Generate packages-index manifests
    :param up_name: upstream name
    :param gen_vers: will generate versions
    :param down_grade: will generate downgrade manifests
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

    if result["event"] == "updated":
        old_ver = result["old_version"]
    else:
        old_ver = result["version"]
        if not down_grade:
            logger.warning("Already updated")
            return

    logger.info(f"Generate {up_name} manifests for versions {gen_vers}")
    logger.info(f"Generate {up_name} manifests base on old version `{old_ver}`")

    # check list
    if old_ver in gen_vers:
        logger.warning(f"Remove old version `{old_ver}` from generate version list")
        gen_vers.remove(old_ver)

    if len(gen_vers) == 0:
        logger.warning("No version to be generated")
        return

    # load riko.toml config
    up_cfg = get_riko().get_ruyi_package(up_name)
    if up_cfg is None:
        raise FileNotFoundError(f"No riko upstream package `{up_name}` found")

    # load old packages-index manifest
    cbs: list[str] = up_cfg.get_combos()
    vers: list[PackageVersion] = []
    for c in cbs:
        pkg_ver = get_riko().get_packages_index_manifest(up_cfg.get_category(), c, old_ver)
        if pkg_ver is None:
            if "keep_back" in up_cfg.get_policy(c):
                pkg_ver = get_riko().get_packages_index_latest(up_cfg.get_category(), c)
                pkg_ver.add_policies(up_cfg.get_policy(c))
                logger.debug(f"no ruyi packages-index manifest for category `{up_cfg.get_category()}` "
                             f"package {c} version {old_ver} found")
                logger.debug(f"use `keep_back` policy, find ruyi packages-index manifest of category "
                             f"`{up_cfg.get_category()}` package {c} version {pkg_ver.upstream_version}")
                logger.info(f"{up_name} manifest {c} combo base on old version `{pkg_ver.upstream_version}`")
            else:
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
        pkg.add_policies([p for p in vers[i].policies])
        old_versions.append(pkg)

    # new ver
    nv_dat = up_cfg.get_nvchecker_dat()
    up_source = nv_dat["source"]

    for gv in gen_vers:
        # gv is upstream version str

        # this version
        new_versions: List[RikoPkg] = []

        # get UpstreamLike for different nvchecker source
        # one upstream to many combos, package splitting
        if up_source == "github":
            up = GithubUpstream(nv_dat["github"], gv)
        elif up_source == "regex":
            source = up_cfg.get_source()

            file_url = source["regex_file_url"]
            file_url = file_url.replace("{{nvchecker.url}}", nv_dat["url"])
            file_url = file_url.replace("{{upstream_version}}", gv)

            up = RegexUpstream(nv_dat["url"], nv_dat["regex"], file_url, source["regex_file_regex"])
        else:
            raise NotImplementedError(f"upstream source {up_source} not supported")

        # many combos
        for i in range(0, len(vers)):

            pkg = RikoPkg(up_cfg.get_category(), cbs[i], up_cfg.get_name(), vers[i].version, gv, up)

            # before rikoring
            ma_cp = copy.deepcopy(vers[i].manifest)

            # automatically set upstream_version
            ma_cp["metadata"]["upstream_version"] = gv

            # automatically remove service_level
            # this value should be set by support-matrix
            if ma_cp["metadata"].get("service_level") is not None:
                ma_cp["metadata"]["service_level"] = {}

            # finish prepare rikoring
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
            for i in range(0, len(old_versions)):
                if new_versions[i].get_manifest_ready() and not down_grade:
                    assert new_versions[i].version.compare(old_versions[i].version) > 0
        except Exception as e:
            logger.error(e)
            traceback.print_exc()
            logger.error(f"Skip version `{gv}` due to previous error")
            # skip this version
            continue

        # check manifests
        for j in range(0, len(new_versions)):
            nv = new_versions[j]
            ov = old_versions[j]
            ma, rdy = nv.get_manifest()
            oma, _ = ov.get_manifest()

            if rdy:

                # final state
                # automatically set new values
                # after rikoring

                # assign disk partition map for dd-v1
                tp = ma["provisionable"]["strategy"]
                if tp == "dd-v1":
                    ma["provisionable"]["partition_map"]["disk"] = ma["blob"]["distfiles"][0]
                elif tp == "fastboot-v1":
                    pass
                elif tp == "fastboot-v1(lpi4a-uboot)":
                    ma["provisionable"]["partition_map"]["uboot"] = ma["blob"]["distfiles"][0]
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
                            ma["provisionable"]["partition_map"]["root"] = ma["provisionable"]["partition_map"]["root"][:-len(tar)]
                    elif tp == "fastboot-v1(lpi4a-uboot)":
                        if ma["provisionable"]["partition_map"]["uboot"].endswith(tar):
                            ma["provisionable"]["partition_map"]["uboot"] = ma["provisionable"]["partition_map"]["uboot"][:-len(tar)]

                # download files
                for i in range(0, len(ma["distfiles"])):
                    url: str = ma["distfiles"][i]["urls"][0]
                    f_loc = riko_cache_dir / ma["distfiles"][i]["name"]
                    cmd: List[str] = ["curl", "-C", "-", "--retry", "3", "--retry-delay", "2", "--retry-all-errors",
                                      "-L", url, "-o", str(f_loc), ]
                    env = os.environ.copy()

                    if f_loc.exists():
                        f_loc.unlink()

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

                # check `keep_back` policy
                if ov.accept_policy("keep_back"):
                    if len(ma["distfiles"]) == 1:
                        if (ma["distfiles"][0]["checksums"]["sha256"] == oma["distfiles"][0]["checksums"]["sha256"] and
                            ma["distfiles"][0]["checksums"]["sha512"] == oma["distfiles"][0]["checksums"]["sha512"]):
                            logger.info(f"`keep_back` for package {nv.get_combo()}, version "
                                           f"{ma["metadata"]["upstream_version"]} and version "
                                           f"{oma["metadata"]["upstream_version"]} have same checksums")
                            continue
                    else:
                        logger.warning("`keep_back` set but manifest has multiple distfiles")

                # write toml
                ensure_dir(riko_manifests_dir / nv.get_category())
                ensure_dir(riko_manifests_dir / nv.get_category() / nv.get_combo())

                new_toml = riko_manifests_dir / nv.get_category() / nv.get_combo() / f"{str(nv.get_version())}.toml"
                with open(new_toml, "wb") as nt:
                    tomli_w.dump(ma, nt)

                cmd: List[str] = ["ruyi", "admin", "format-manifest", str(new_toml), ]
                env = os.environ.copy()

                process = subprocess.Popen(cmd, env=env)
                ret = process.wait()
                if ret != 0:
                    raise subprocess.CalledProcessError(ret, cmd)

                logger.info(f"new manifest for package {nv.get_combo()} version {ma["metadata"]["upstream_version"]}")
            else:
                logger.warning(f"skip package {nv.get_combo()}")

                continue
