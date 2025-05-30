from enum import Enum
import json

import requests
import pathlib
from lib.db_models import CheckInfoElement, CheckType
import tomli
import os
from dataclasses import dataclass
import semver

root_path = "..\\packages-index\\manifests\\board-image\\"

@dataclass
class DistFileInfo:
    name: str
    url: str
    path: str

def main():
    # get all files in path
    files = get_files()

    check_info = []
    
    for file in files:
        urls = parse_single_file(file)
        for url in urls:
            check_info.append(CheckInfoElement(name=url.name, check_path=url.url, check_type=filter_check_type(url.url)))
    
    accessible_count = 0
    unknown_count = 0
    unknown_and_accessible_count = 0
    # for each check_info, check if url is accessible
    for item in check_info:
        if item.check_type == CheckType.UNKNOWN:
            unknown_count += 1
            if check_if_url_is_accessible(item.check_path):
                unknown_and_accessible_count += 1
                accessible_count += 1
            else:
                item.check_type = CheckType.UNKNOWN_AND_INACCESSIBLE
            continue
        if check_if_url_is_accessible(item.check_path):
            accessible_count += 1
    
    json_str = json.dumps([{
        "name": item.name,
        "check_path": item.check_path,
        "check_type": item.check_type.value
    } for item in check_info], indent=4)

    with open("check_info.json", "w") as f:
        f.write(json_str)

    print(f"Total: {len(check_info)}, \nAccessible: {accessible_count}, \nUnknown: {unknown_count}, \nImplemented Rate: {(len(check_info)-unknown_count)/len(check_info) * 100:.1f}%, \nRequired Implemented Rate: {((1-(unknown_and_accessible_count/len(check_info))) * 100):.1f}%")

def get_files():
    files = []
    for root, dirs, filenames in os.walk(root_path):
        # if filenames count > 1 then filter the newest version file using semver
        # if filenames count == 1 then add the file to files
        if len(filenames) > 1:
            # filter the filenames using semver
            semver_filenames = []
            for filename in filenames:
                if filename.endswith(".toml"):
                    semver_filenames.append(filename)
            # sort the filenames using semver
            semver_filenames.sort(key=lambda x: semver.VersionInfo.parse(x.split(".toml")[0]))
            # get the newest version file
            files.append(os.path.join(root, semver_filenames[-1]))
        elif len(filenames) == 1:
            for filename in filenames:
                if filename.endswith(".toml"):
                    files.append(os.path.join(root, filename))
    return files

def check_if_url_is_accessible(url: str) -> bool:
    try:
        response = requests.head(url, allow_redirects=True)
        if response.status_code == 200:
            return True
        elif response.status_code in [301, 302]:
            return True
        else:
            return False
    except requests.RequestException as e:
        print(f"Error accessing URL: {e}")
        return False

def filter_check_type(url: str):
    # if startwith https://github.com
    if url.startswith("https://github.com"):
        return CheckType.GITHUB
    elif url.startswith("https://mirrors.tuna.tsinghua.edu.cn/openwrt"):
        return CheckType.OPENWRT
    elif url.startswith("https://mirror.iscas.ac.cn/openeuler-sig-riscv/openEuler-RISC-V/preview/openEuler-23.09-V1-riscv64/lpi4a/"):
        return CheckType.OPENEULER_LPI4A
    elif url.startswith("https://mirror.iscas.ac.cn/revyos"):
        return CheckType.REVYOS
    else:
        return CheckType.UNKNOWN

def filter_mirror(s: str) -> str:
    if s.startswith("mirror://ruyi-3rdparty-canaan/"):
        return s.replace("mirror://ruyi-3rdparty-canaan/", "https://mirror.iscas.ac.cn/ruyisdk/3rdparty/canaan/")
    elif s.startswith("mirror://ruyi-3rdparty-milkv/"):
        return s.replace("mirror://ruyi-3rdparty-milkv/", "https://mirror.iscas.ac.cn/ruyisdk/3rdparty/milkv/")
    else:
        return s

def parse_single_file(path) -> list[DistFileInfo]:
    with open(path, 'rb') as f:  # tomli requires binary mode
        data = f.read()
    relative_path = str(pathlib.Path(path).relative_to(pathlib.Path(root_path)))
    
    toml = tomli.loads(data.decode('utf-8'))
    urls_result = []
    
    node = toml.get("distfiles", [])
    desc = toml.get("metadata", {}).get("desc", None)
    for o in node:
        name = o["name"]
        if "fetch_restriction" in o:
            fetch_restriction = o["fetch_restriction"]
            ver = fetch_restriction["params"]["version"]
            restricted_software_name = toml["metadata"]["desc"]
            assert restricted_software_name == "Kingsoft WPS Office", f"new restricted software has been added, not WPS, name: {restricted_software_name}"

            urls_result.append(DistFileInfo(name=desc, url=f"wps://{ver}", path=path))
            continue
        
        urls = o.get("urls", None)
        
        if urls is not None:
            urls1 = [url for url in urls]
            
            if len(urls1) > 1:
                original_length = len(urls1)
                if any("openwrt" in x for x in urls1):
                    urls1 = [x for x in urls1 if "openwrt.org" not in x]
                else:
                    urls1 = [x for x in urls1 if "mirror" not in x]
                assert original_length - len(urls1) == 1
                urls_result.append(DistFileInfo(name=desc, url=urls1[0], path=relative_path))
            elif urls1:
                urls_result.append(DistFileInfo(name=desc, url=filter_mirror(urls1[0]), path=relative_path))
        else:
            urls_result.append(DistFileInfo(name=desc, url=name, path=relative_path))
    
    return urls_result

if __name__ == "__main__":
    main()