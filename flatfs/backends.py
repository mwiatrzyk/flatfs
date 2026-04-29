import fnmatch
import os
import pathlib
from typing import Iterable, Iterator, Optional

from flatfs.exc import PathAccessError

from . import _utils


class LocalFlatFs:
    """FlatFS implementation that adapts local filesystem and uses
    :mod:`pathlib` Python module as a backend.

    :param root_dir:
        The path to the FlatFS root directory.

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

    def exists(self, path: str) -> bool:
        abspath = self.__make_abspath(path)
        return abspath.is_file()

    def read_bytes(self, path: str) -> bytes:
        abspath = self.__make_abspath(path)
        return abspath.read_bytes()

    def read_chunks(self, path: str, chunk_size: int = 65535) -> Iterator[bytes]:
        abspath = self.__make_abspath(path)
        with abspath.open("rb") as fd:
            while True:
                chunk = fd.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def write_bytes(self, path: str, data: bytes):
        abspath = self.__make_abspath(path)
        abspath.parent.mkdir(parents=True, exist_ok=True)
        abspath.write_bytes(data)

    def write_chunks(self, path: str, chunks: Iterable[bytes]):
        abspath = self.__make_abspath(path)
        abspath.parent.mkdir(parents=True, exist_ok=True)
        with abspath.open("wb") as fd:
            for chunk in chunks:
                fd.write(chunk)

    def remove(self, path: str):
        abspath = self.__make_abspath(path)
        abspath.unlink()
