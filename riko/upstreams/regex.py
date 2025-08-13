import logging
import re
import requests

from typing import List, ClassVar

from .upstream import Upstream


logger = logging.getLogger(__name__)


class RegexUpstream(Upstream):
    source: ClassVar[str] = "regex"

    def __init__(self, base_url: str, base_re: str, file_url: str, file_re: str) -> None:
        self._base_url = base_url
        self._base_regex = base_re
        self._file_url = file_url
        self._file_regex = file_re

        self._ready = False
        self._text = ""
        self._asserts: List[str] = []


    def get_release_asserts(self) -> List[str]:
        if self._ready:
            return self._asserts

        resp = requests.get(self._file_url)
        if resp.status_code != 200:
            raise RuntimeError(f"url {self._file_url} returned status code {resp.status_code}")

        self._text = resp.text
        self._asserts = re.findall(self._file_regex, self._text)
        self._ready = True

        return self._asserts

    def get_release_asserts_substring(self, substr: str) -> List[str]:
        r = []

        for f in self.get_release_asserts():
            if substr in f:
                r.append(f)

        return r

    def get_release_assert_substring(self, substr: str) -> str:
        r = self.get_release_asserts_substring(substr)

        assert len(r) == 1
        return r[0]

    def get_release_asserts_regex(self, pattern: str) -> List[str]:
        r = []

        for f in self.get_release_asserts():
            if re.match(pattern, f):
                r.append(f)

        return r

    def get_release_assert_regex(self, pattern: str) -> str:
        r = self.get_release_asserts_regex(pattern)

        assert len(r) == 1
        return r[0]
