import http.client
import logging
import re
import urllib.parse
import urllib.request

from typing import ClassVar, List, Tuple

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

    def _file_name_and_url(self, f: str) -> Tuple[str, str]:
        return f, urllib.parse.urljoin(self._file_url, f)

    def get_release_asserts(self) -> List[str]:
        if self._ready:
            return self._asserts

        resp: http.client.HTTPResponse = urllib.request.urlopen(self._file_url, timeout=30.0)
        if resp.status != http.client.OK:
            raise RuntimeError(f"url {self._file_url} returned status code {resp.status}: "
                               f"{http.client.responses[resp.status]}")

        self._text = resp.read().decode()
        self._asserts = re.findall(self._file_regex, self._text)
        self._ready = True

        return self._asserts

    def get_release_asserts_substring(self, substr: str) -> List[Tuple[str, str]]:
        r = []

        for f in self.get_release_asserts():
            if substr in f:
                r.append(self._file_name_and_url(f))

        return r

    def get_release_assert_substring(self, substr: str) -> Tuple[str, str]:
        r = self.get_release_asserts_substring(substr)

        assert len(r) == 1
        return r[0]

    def get_release_asserts_regex(self, pattern: str) -> List[Tuple[str, str]]:
        r = []

        for f in self.get_release_asserts():
            if re.search(pattern, f):
                r.append(self._file_name_and_url(f))

        return r

    def get_release_assert_regex(self, pattern: str) -> Tuple[str, str]:
        r = self.get_release_asserts_regex(pattern)

        assert len(r) == 1
        return r[0]
