import logging
import re
import requests

from typing import List, ClassVar

from .upstream import Upstream


logger = logging.getLogger(__name__)


class RegexUpstream(Upstream):
    source: ClassVar[str] = "regex"

    def __init__(self, base_url: str, base_re: str) -> None:
        self._base_url = base_url
        self._base_regex = base_re
        self._file_dir: str = ""
        self._file_regex: str = ""

    def get_release_asserts(self, file_dir: str, file_regex: str) -> List[str]:
        self._file_regex = file_regex
        self._file_dir = file_dir

        resp = requests.get(self._base_url + self._file_dir)
        if resp.status_code != 200:
            raise RuntimeError(f"url {self._base_url + self._file_dir} returned status code {resp.status_code}")

        return re.findall(self._file_regex, resp.text)
