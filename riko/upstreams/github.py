import logging
import re
import tomllib

from github import Auth, Github
from typing import ClassVar, Dict, List, Tuple

from .upstream import Upstream
from ..config.const import nvchecker_key


logger = logging.getLogger(__name__)


class GithubUpstream(Upstream):
    source: ClassVar[str] = "github"

    def __init__(self, repo: str, release: str) -> None:
        self._release = release

        if nvchecker_key.exists() and nvchecker_key.is_file():
            with open(nvchecker_key, "rb") as kf:
                key = tomllib.load(kf).get("keys")
                if key is not None:
                    key = key.get("github")

            if key is not None:
                self._github = Github(auth=Auth.Token(key))
            else:
                self._github = Github()

        else:
            logger.warning(f"nvchecker keyfile {nvchecker_key} not found.")
            self._github = Github()

        self._repo = self._github.get_repo(repo)

        # cache
        self._cache_asserts: Dict[str, List[Tuple[str, str]]] = {}

    def get_release_asserts_obj(self):
        release = self._repo.get_release(self._release)
        return release.get_assets()

    def get_release_asserts(self) -> List[Tuple[str, str]]:
        assets = self.get_release_asserts_obj()

        if self._release in self._cache_asserts:
            return self._cache_asserts[self._release]

        files: List[Tuple[str, str]] = []
        for asset in assets:
            files.append((asset.name, asset.browser_download_url))
        self._cache_asserts[self._release] = files

        return files

    def get_release_asserts_substring(self, substr: str) -> List[Tuple[str, str]]:
        r = []

        for f in self.get_release_asserts():
            if substr in f[0]:
                r.append(f)

        return r

    def get_release_assert_substring(self, substr: str) -> Tuple[str, str]:
        r = self.get_release_asserts_substring(substr)

        assert len(r) == 1
        return r[0]

    def get_release_asserts_regex(self, pattern: str) -> List[Tuple[str, str]]:
        r = []

        for f in self.get_release_asserts():
            if re.match(pattern, f[0]):
                r.append(f)

        return r

    def get_release_assert_regex(self, pattern: str) -> Tuple[str, str]:
        r = self.get_release_asserts_regex(pattern)

        assert len(r) == 1
        return r[0]
