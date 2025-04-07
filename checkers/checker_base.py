from abc import ABC, abstractmethod
from github import Github
from checkers.db_models import *
from typing import List, Optional


class CheckerBase(ABC):
    @abstractmethod
    def check(self, data: CheckInfoElement) -> CheckResultElement:
        pass

