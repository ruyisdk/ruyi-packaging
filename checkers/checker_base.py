from abc import ABC, abstractmethod
from github import Github
from checkers.db_models import *
from typing import List, Optional
from checkers.github_checker import *

class CheckerBase(ABC):
    @abstractmethod
    def check(self, data: CheckInfoElement) -> CheckResultElement:
        pass

    @staticmethod
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