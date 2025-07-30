import tomllib

from github import Auth, Github
from typing import ClassVar

from .upstream import Upstream
from ..config.const import nvchecker_key


class GithubUpstream(Upstream):
    source: ClassVar[str] = "github"

    def __init__(self, repo: str) -> None:

        if nvchecker_key.exists() and nvchecker_key.is_file():
            with open(nvchecker_key, "rb") as kf:
                key = tomllib.load(kf).get("key")
                if key is not None:
                    key = key.get("github")

            if key is not None:
                self._github = Github(auth=Auth.Token(key))
            else:
                self._github = Github()

        self._repo = self._github.get_repo(repo)

    def get_release_asserts(self, release: str):
        release = self._repo.get_release(release)
        return release.get_assets()
