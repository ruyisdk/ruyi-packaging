from checkers.github_checker import *
from typing import List, Optional
from checkers.db_models import *
def check_all(datas: List[CheckInfoElement]) -> List[CheckResultElement]:
    results = []
    
    for data in datas:
        url = data.check_path
        if data.check_type == CheckType.GITHUB:
            checker = GitHubReleaseChecker()
            result = checker.check(data)
            results.append(result)
        elif False:  # Placeholder for additional conditions
            # todo
            pass
    
    return results