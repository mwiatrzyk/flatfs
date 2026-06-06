import dataclasses
import datetime
import fnmatch
import os
import pathlib
from typing import Generator, Iterator, Optional

from flatfs.exc import PathAccessError, PathNotFoundError
from flatfs.interface import Stat

from . import _utils, _export

__all__ = export = _export.Export()  # type: ignore


@export
class LocalFlatFs:
    """FlatFS implementation using local filesystem to store files.

    You can use this to access files from an existing directory (the paths are
    then relative to *root_dir*), or to create a completely new filesystem
    inside an empty directory.

    :param root_dir:
        The path to the root directory where files will be stored.

    :param exclude:
        The glob patterns of paths to exclude.

        For example, you may want to exclude ``.git`` directory when you use
        FlatFS to access content of some Git repository.

        For more details on pattern syntax used check :mod:`fnmatch` which is
        used underneath.

    :param include:
        The glob patterns of paths to include.

        These can only be paths from inside root directory. For example, you
        may wish to allow just ``src`` and ``test`` dirs, not all files.

        For more details on pattern syntax used check :mod:`fnmatch` which is
        used underneath.
    """

    def __init__(self, root_dir: pathlib.Path, exclude: Optional[set[str]] = None, include: Optional[set[str]] = None):
        self.__root_dir = root_dir
        self.__exclude = exclude or set()
        self.__include = include or set()

    def __is_excluded(self, normalized_path: str) -> bool:
        for pattern in self.__exclude:
            if fnmatch.fnmatch(normalized_path, pattern):
                return True
        return False

    def __is_included(self, normalized_path: str) -> bool:
        if not self.__include:
            return True
        for pattern in self.__include:
            if fnmatch.fnmatch(normalized_path, pattern):
                return True
        return False

    def __make_abspath(self, path: str) -> pathlib.Path:
        normalized_path = _utils.normalize_path(path)
        if self.__is_excluded(normalized_path):
            raise PathAccessError(path)
        return self.__root_dir / normalized_path[1:]

    def __walk(self, path: pathlib.Path, relpath: str):
        for name in os.listdir(path):
            fullpath = path / name
            fullrelpath = f"{relpath}/{name}"
            if fullpath.is_dir():
                yield from self.__walk(fullpath, fullrelpath)
            elif not self.__is_excluded(fullrelpath) and self.__is_included(fullrelpath):
                yield fullrelpath

    def scan(self) -> Iterator[str]:
        return self.__walk(self.__root_dir, "")

    def stat(self, path: str) -> Stat:
        abspath = self.__make_abspath(path)
        if not abspath.is_file():
            raise PathNotFoundError(path)
        stat_result = abspath.stat()
        return Stat(
            modified=datetime.datetime.fromtimestamp(stat_result.st_mtime, datetime.timezone.utc),
            size=stat_result.st_size,
        )

    def exists(self, path: str) -> bool:
        abspath = self.__make_abspath(path)
        return abspath.is_file()

    def read_chunks(self, path: str, chunk_size: int = 65535) -> Generator[bytes, None, None]:
        abspath = self.__make_abspath(path)
        if not abspath.is_file():
            raise PathNotFoundError(path)
        with abspath.open("rb") as fd:
            while True:
                chunk = fd.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def write_chunks(self, path: str, chunk_gen: Generator[bytes, None, None]) -> Generator[int, None, None]:
        abspath = self.__make_abspath(path)
        abspath.parent.mkdir(parents=True, exist_ok=True)
        with abspath.open("wb") as fd:
            for chunk in chunk_gen:
                yield fd.write(chunk)

    def remove(self, path: str):
        abspath = self.__make_abspath(path)
        if not abspath.is_file():
            raise PathNotFoundError(path)
        abspath.unlink()


@export
class InMemoryFlatFs:
    """In-memory FlatFS implementation.

    This is mostly suitable for use during testing to avoid unnecessary I/O and
    disk usage.
    """

    @dataclasses.dataclass
    class _File:
        payload: bytes
        stat: Stat

    def __init__(self) -> None:
        self.__storage: dict[str, InMemoryFlatFs._File] = {}

    def __make_key(self, path: str) -> str:
        normalized_key = _utils.normalize_path(path)
        return normalized_key

    def scan(self) -> Iterator[str]:
        return iter(self.__storage.keys())

    def stat(self, path: str) -> Stat:
        key = self.__make_key(path)
        if key not in self.__storage:
            raise PathNotFoundError(path)
        return self.__storage[key].stat

    def exists(self, path: str) -> bool:
        return self.__make_key(path) in self.__storage

    def read_chunks(self, path: str, chunk_size: int = 65535) -> Generator[bytes, None, None]:
        key = self.__make_key(path)
        if key not in self.__storage:
            raise PathNotFoundError(path)
        data_left = self.__storage[key].payload
        while len(data_left) > 0:
            chunk = data_left[:chunk_size]
            data_left = data_left[chunk_size:]
            yield chunk

    def write_chunks(self, path: str, chunk_gen: Generator[bytes, None, None]) -> Generator[int, None, None]:
        now = _utils.utcnow()
        stat = Stat(
            modified=now,
            size=0,
        )
        self.__storage[self.__make_key(path)] = file = self._File(b"", stat)
        for chunk in chunk_gen:
            file.payload += chunk
            write_count = len(chunk)
            file.stat.size += write_count
            yield write_count

    def remove(self, path: str):
        key = self.__make_key(path)
        if key not in self.__storage:
            raise PathNotFoundError(path)
        del self.__storage[key]
