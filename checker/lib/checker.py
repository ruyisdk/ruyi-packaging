
from typing import List, Optional

from lib.github_checker import GitHubReleaseChecker
from lib.openwrt_checker import OpenWrtChecker
from lib.openeuler_lpi4a_checker import OpenEulerLpi4aChecker
from lib.revyos_checker import RevyOSChecker
from lib.db_models import *
def check_all(datas: List[CheckInfoElement]) -> List[CheckResultElement]:
    results = []
    
    for data in datas:
        url = data.check_path
        if data.check_type == CheckType.GITHUB:
            checker = GitHubReleaseChecker()
            result = checker.check(data)
            results.append(result)
        elif data.check_type == CheckType.OPENWRT:
            checker = OpenWrtChecker()
            result = checker.check(data)
            results.append(result)
        elif data.check_type == CheckType.OPENEULER_LPI4A:
            checker = OpenEulerLpi4aChecker()
            result = checker.check(data)
            results.append(result)
        elif data.check_type == CheckType.REVYOS:
            checker = RevyOSChecker()
            result = checker.check(data)
            results.append(result)
        elif False:  # Placeholder for additional conditions
            # todo
            pass
    
    return results
