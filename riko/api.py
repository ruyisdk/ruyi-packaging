import semver

from typing import Dict, Tuple, Union

from .upstreams.github import GithubUpstream

__all__ = ("RikoPkg", "GithubUpstream", )
_UpstreamLike = Union[GithubUpstream]


class RikoPkg:
    def __init__(self, version: semver.Version, upstream_version: str, upstream: _UpstreamLike) -> None:
        self._version = version
        self._upstream_version = upstream_version
        self._manifest: Dict = {}
        self._manifest_ready: bool = False

        self._upstream: _UpstreamLike = upstream

    def set_manifest(self, manifest: Dict) -> None:
        self._manifest = manifest
        self._manifest_ready = True

    def set_manifest_ready(self) -> None:
        self._manifest_ready = True

    def get_manifest(self) -> Tuple[Dict, bool]:
        return self._manifest, self._manifest_ready

    def get_version(self) -> semver.Version:
        return self._version

    def get_upstream_version(self) -> str:
        return self._upstream_version

    def get_upstream(self) -> _UpstreamLike:
        return self._upstream
