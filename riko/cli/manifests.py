
import ast
import copy
import hashlib
import importlib.util
import logging
import os
import re
import subprocess
import tomli_w
import traceback
import yaml

from typing import Dict, List, Tuple

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

    # nvchecker result
    result = get_riko().get_nvchecker_result(up_name)

    if result is None:
        logger.error("No such upstream %s", up_name)
        logger.error("No manifest generated")
        return

    # if no gen_vers given, let nvchecker deside
    if len(gen_vers) == 0:
        gen_vers.append(result["version"])

    if result["event"] == "updated":
        old_ver = result["old_version"]
    else:
        old_ver = result["version"]
        if not down_grade:
            logger.warning("Already updated")
            return

    # check list
    if old_ver in gen_vers:
        logger.warning(f"Remove old version `{old_ver}` from generate version list")
        gen_vers.remove(old_ver)

    if len(gen_vers) == 0:
        logger.warning("No version to be generated")
        return

    logger.info(f"Generate {up_name} manifests for versions {gen_vers}")

    # load riko.toml config
    riko_toml = get_riko().get_ruyi_package(up_name)
    if riko_toml is None:
        raise FileNotFoundError(f"No riko upstream package `{up_name}` found")

    # load old packages-index manifest
    gen_cbs: list[str] = riko_toml.get_combos()
    gen_cbs_ov: list[PackageVersion] = []
    for c in gen_cbs:
        pkg_ver = get_riko().get_packages_index_manifest(riko_toml.get_category(), c, old_ver)
        if pkg_ver is None:
            if "keep_back" in riko_toml.get_policy(c):
                pkg_ver = get_riko().get_packages_index_latest(riko_toml.get_category(), c)
                pkg_ver.add_policies(riko_toml.get_policy(c))
                logger.debug(f"no ruyi packages-index manifest for category `{riko_toml.get_category()}` "
                             f"package {c} version {old_ver} found")
                logger.debug(f"use `keep_back` policy, find ruyi packages-index manifest of category "
                             f"`{riko_toml.get_category()}` package {c} version {pkg_ver.upstream_version}")
                logger.info(f"{up_name} manifest {c} combo base on old version `{pkg_ver.upstream_version}`")
            else:
                logger.info(f"No ruyi packages-index manifest for category `{riko_toml.get_category()}` "
                            f"package {c} version {old_ver} found")
        gen_cbs_ov.append(pkg_ver)

    # output dir
    ensure_dir(riko_cache_dir)
    ensure_dir(riko_manifests_dir)

    riko_py_p = ruyi_pkgs_dir / riko_toml.get_category() / up_name / "riko.py"
    riko_yaml_p = ruyi_pkgs_dir / riko_toml.get_category() / up_name / "riko.yaml"

    if riko_yaml_p.exists():
        riko_yaml_orig: Dict = yaml.safe_load(riko_yaml_p.read_text())
        assert riko_yaml_orig["format"] == "v1"

        # riko.yaml parsing functions
        def tree_update_inner(key: str, value: Dict | List | str) -> Dict:
            if isinstance(value, Dict):
                tree_new = {}
                for k, v in value.items():
                    tree_new.update(tree_update_inner(k, v))

                return {key: tree_new}
            elif isinstance(value, List):
                list_new = []
                if isinstance(value[0], Dict):
                    for v in value:
                        list_new.append(tree_update_inner("k", v)["k"])
                elif isinstance(value[0], str):
                    for s in value:
                        list_new.append(tree_update_inner("k", s)["k"])
                else:
                    raise RuntimeError(f"Unexpected type {type(value)}")
                return {key: list_new}
            elif isinstance(value, str):
                if re.match(r"^[a-zA-Z0-9 ,\-+.]+$", value):
                    return {key: value}
                return {key: ast.parse(value, mode="eval")}
            elif value is None:
                return {key: ""}
            else:
                raise RuntimeError(f"Unexpected type {type(value)}")

        def tree_update(tree_old: Dict, tree_raw: Dict) -> Dict:
            """
            update tree_raw to tree_old, and turn str value to ast
            :param tree_old:
            :param tree_raw:
            :return:
            """
            tree_new = copy.deepcopy(tree_old)

            tree_new.update(tree_update_inner("k", tree_raw)["k"])

            return tree_new

        # riko.yaml ast check function
        def riko_yaml_ast_check(exp: ast.Expression, g_vars: Dict, g_calls: Dict) -> bool:
            _ast_allowed = (ast.Expression, ast.Call, ast.Name, ast.Load, ast.Constant, ast.Tuple)
            # TODO:
            return True

        # riko.yaml running functions
        def riko_yaml_run(_up, om: Dict, nm: Dict, ym: Dict) -> Dict:
            # riko.yaml vals
            _upstream_version = nm["metadata"]["upstream_version"]
            _old_upstream_version = om["metadata"]["upstream_version"]
            _files = {}
            _label = []

            # riko.yaml api
            def _assign(_parm) -> str:
                return str(_parm)

            def _substring(_sub: str) -> Tuple[str, str]:
                if _label[-1] == "name" and _label[-2] == "distfiles":
                    if isinstance(_up, GithubUpstream):
                        return _up.get_release_assert_substring(_sub)
                    elif isinstance(_up, RegexUpstream):
                        return _up.get_release_assert_substring(_sub)
                    else:
                        raise NotImplementedError(f"upstream source {_up.source} not supported")
                else:
                    raise NotImplementedError(f"substream not implemented for _label {_label}")

            def _regex(_pat: str) -> Tuple[str, str]:
                if _label[-1] == "name" and _label[-2] == "distfiles":
                    if isinstance(_up, GithubUpstream):
                        return _up.get_release_assert_regex(_pat)
                    elif isinstance(_up, RegexUpstream):
                        return _up.get_release_assert_regex(_pat)
                    else:
                        raise NotImplementedError(f"upstream source {_up.source} not supported")
                else:
                    raise NotImplementedError(f"substream not implemented for _label {_label}")

            def _replace(_old: str, _new: str) -> str:
                _orig = ""
                _tree = om
                for _l in _label:
                    if _l in om.keys():
                        _tree = om.get(_l)
                        if _tree is None:
                            raise RuntimeError(f"no such key in old version manifest {_l}")
                    else:
                        return ""

                if isinstance(_tree, str):
                    return _tree.replace(_old, _new)
                return ""

            def _file(_name_url: Tuple[str, str]) -> str:
                if _name_url[0] not in _files.keys():
                    _files[_name_url[0]] = {}

                _files[_name_url[0]]["url"] = _name_url[1]
                return _name_url[0]

            def _disk(_name_url: Tuple[str, str]) -> str:
                if _name_url[0] not in _files.keys():
                    _files[_name_url[0]] = {}

                _files[_name_url[0]]["map"] = "disk"
                return _file(_name_url)

            # bfs run ast
            def _ast_run(_ym_t: Dict):
                for k, v in _ym_t.items():
                    _label.append(k)

                    if isinstance(v, ast.Expression):
                        _g_vars = {"upstream_version": _upstream_version,
                                   "old_upstream_version": _old_upstream_version}
                        _g_calls = {"assign": _assign,
                                    "substring": _substring,
                                    "replace": _replace,
                                    "regex": _regex,
                                    "disk": _disk,}
                        if riko_yaml_ast_check(v, _g_vars, _g_calls):
                            _ym_t[k] = eval(compile(v, filename="<expr>", mode="eval"), _g_vars | _g_calls)
                            if not isinstance(_ym_t[k], str):
                                _ym_t[k] = f"value not str but {type(_ym_t[k])}"
                        else:
                            _ym_t[k] = "AST check failed"
                    elif isinstance(v, str):
                        pass
                    elif isinstance(v, Dict):
                        _ast_run(v)
                    elif isinstance(v, List):
                        for d in v:
                            _ast_run(d)
                    else:
                        raise RuntimeError(f"Unexpected type {type(v)}")

                    _label.pop()

            _ast_run(ym)

            # info in _files
            if "provisionable" not in ym.keys():
                ym["provisionable"] = {"partition_map": {}}
            for ff in ym["distfiles"]:
                ff["url"] = [_files[ff["name"]]["url"]]
                ym["provisionable"]["partition_map"][_files[ff["name"]]["map"]] = ff["name"]

            # info of _upstream_version
            ym["metadata"]["upstream_version"] = _upstream_version

            return ym

        # generating
        for gv in gen_vers:
            # get UpstreamLike from riko.toml
            riko_toml_nvdat = riko_toml.get_nvchecker_dat()
            riko_toml_source = riko_toml_nvdat["source"]
            if riko_toml_source == "github":
                riko_toml_upstream = GithubUpstream(riko_toml_nvdat["github"], gv)
            elif riko_toml_source == "regex":
                source = riko_toml.get_source()

                file_url = source["regex_file_url"]
                file_url = file_url.replace("{{nvchecker.url}}", riko_toml_nvdat["url"])
                file_url = file_url.replace("{{upstream_version}}", gv)

                riko_toml_upstream = RegexUpstream(riko_toml_nvdat["url"], riko_toml_nvdat["regex"], file_url, source["regex_file_regex"])
            else:
                raise NotImplementedError(f"upstream source {riko_toml_source} not supported")

            riko_yaml = copy.deepcopy(riko_yaml_orig)

            riko_yaml_source = {}
            riko_yaml_cbs = {}
            if "source" in riko_yaml.keys():
                riko_yaml_source = tree_update({"format": riko_yaml["format"]}, riko_yaml["source"])

            for i in range(0, len(gen_cbs)):
                if gen_cbs[i] in riko_yaml.keys():
                    riko_yaml_ast = tree_update(riko_yaml_source, riko_yaml[gen_cbs[i]])

                    old_manifests = gen_cbs_ov[i].get_manifest()
                    new_manifests = {"metadata": {"upstream_version": gv}}

                    manifest_stage1 = riko_yaml_run(riko_toml_upstream, old_manifests, new_manifests, riko_yaml_ast)
                    riko_yaml_cbs[gen_cbs[i]] = manifest_stage1

        logger.warning("Riko.yaml not implemented.")
    else:
        # riko v0.0.1
        # packaging with single riko.py
        # upgrade from old manfests
        logger.info(f"Generate {up_name} manifests base on old version `{old_ver}`")

        if not riko_py_p.exists():
            raise FileNotFoundError(f"{riko_py_p} not found")

        # old ver
        old_versions: List[RikoPkg] = []
        for i in range(0, len(gen_cbs_ov)):
            pkg = RikoPkg(riko_toml.get_category(), gen_cbs[i], riko_toml.get_name(), gen_cbs_ov[i].version, gen_cbs_ov[i].upstream_version)
            pkg.set_manifest(gen_cbs_ov[i].manifest)
            pkg.add_policies([p for p in gen_cbs_ov[i].policies])
            old_versions.append(pkg)

        # new ver
        nv_dat = riko_toml.get_nvchecker_dat()
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
                source = riko_toml.get_source()

                file_url = source["regex_file_url"]
                file_url = file_url.replace("{{nvchecker.url}}", nv_dat["url"])
                file_url = file_url.replace("{{upstream_version}}", gv)

                up = RegexUpstream(nv_dat["url"], nv_dat["regex"], file_url, source["regex_file_regex"])
            else:
                raise NotImplementedError(f"upstream source {up_source} not supported")

            # many combos
            for i in range(0, len(gen_cbs_ov)):

                pkg = RikoPkg(riko_toml.get_category(), gen_cbs[i], riko_toml.get_name(), gen_cbs_ov[i].version, gv, up)

                # before rikoring
                ma_cp = copy.deepcopy(gen_cbs_ov[i].manifest)

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

            # call riko.py
            spec = importlib.util.spec_from_file_location("riko_py", riko_py_p)
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
