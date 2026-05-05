import asyncio
import fnmatch
import os
import pathlib
from queue import Queue
from typing import (
    AsyncGenerator,
    AsyncIterable,
    Generator,
    Iterable,
    Iterator,
    Optional,
)

from flatfs.exc import PathAccessError, PathNotFoundError
from flatfs.interface import FlatFsReaderWriter

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

    def __init__(
        self,
        root_dir: pathlib.Path,
        exclude: Optional[set[str]] = None,
        include: Optional[set[str]] = None,
    ):
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

    def read_chunks(self, path: str, chunk_size: int = 65535) -> Iterator[bytes]:
        abspath = self.__make_abspath(path)
        if not abspath.is_file():
            raise PathNotFoundError(path)
        with abspath.open("rb") as fd:
            while True:
                chunk = fd.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    def write_chunks(self, path: str, chunks: Iterable[bytes]):
        abspath = self.__make_abspath(path)
        abspath.parent.mkdir(parents=True, exist_ok=True)
        with abspath.open("wb") as fd:
            for chunk in chunks:
                fd.write(chunk)

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

    def __init__(self):
        self.__storage: dict[str, bytes] = {}

    def __make_key(self, path: str) -> str:
        normalized_key = _utils.normalize_path(path)
        return normalized_key

    def scan(self) -> Iterator[str]:
        return iter(self.__storage.keys())

    def exists(self, path: str) -> bool:
        return self.__make_key(path) in self.__storage

    def read_chunks(self, path: str, chunk_size: int = 65535) -> Iterator[bytes]:
        key = self.__make_key(path)
        if key not in self.__storage:
            raise PathNotFoundError(path)
        data_left = self.__storage[key]
        while len(data_left) > 0:
            chunk = data_left[:chunk_size]
            data_left = data_left[chunk_size:]
            yield chunk

    def write_chunks(self, path: str, chunks: Iterable[bytes]):
        self.__storage[self.__make_key(path)] = b"".join(chunks)

    def remove(self, path: str):
        key = self.__make_key(path)
        if key not in self.__storage:
            raise PathNotFoundError(path)
        del self.__storage[key]


@export
class AsyncFlatFsAdapter:
    """Adapter that wraps given :class:`flatfs.interface.FlatFsReaderWriter`
    with async interface.

    You can use this to adapt e.g. :class:`LocalFlatFs` or
    :class:`InMemoryFlatFs` objects with async interface allowing for
    convenient use with async code. The blocking calls are dispatched to
    background worker which communicates with the caller using queues.

    :param target:
        The target FlatFS reader-writer to wrap.
    """

    def __init__(self, target: FlatFsReaderWriter):
        self.__target = target

    async def scan(self) -> AsyncGenerator[str, None]:

        def scanner():
            for path in self.__target.scan():
                loop.call_soon_threadsafe(queue.put_nowait, path)
            loop.call_soon_threadsafe(queue.put_nowait, "")

        loop = asyncio.get_running_loop()
        asyncio.create_task(_utils.run_blocking(scanner))
        queue = asyncio.Queue()
        while True:
            path = await queue.get()
            if not path:
                break
            yield path

    async def exists(self, path: str) -> bool:
        return await _utils.run_blocking(self.__target.exists, path)

    async def read_chunks(self, path: str, chunk_size: int = 65535) -> AsyncGenerator[bytes, None]:

        def reader():
            try:
                for chunk in self.__target.read_chunks(path, chunk_size):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
                loop.call_soon_threadsafe(queue.put_nowait, b"")
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, e)

        loop = asyncio.get_running_loop()
        queue = asyncio.Queue()
        asyncio.create_task(_utils.run_blocking(reader))
        while True:
            chunk_or_exc = await queue.get()
            if not chunk_or_exc:
                break
            if isinstance(chunk_or_exc, Exception):
                raise chunk_or_exc
            yield chunk_or_exc

    async def write_chunks(self, path: str, chunks: AsyncIterable[bytes]):

        def gen() -> Generator[bytes, None, None]:
            while True:
                chunk = queue.get()
                if not chunk:
                    return
                yield chunk

        queue = Queue()
        task = asyncio.create_task(_utils.run_blocking(self.__target.write_chunks, path, gen()))
        async for chunk in chunks:
            queue.put(chunk)
        queue.put(b"")
        await task

    async def remove(self, path: str):
        await _utils.run_blocking(self.__target.remove, path)
