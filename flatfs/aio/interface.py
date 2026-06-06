from typing import AsyncGenerator, AsyncIterator, Protocol

from flatfs import _export
from flatfs.interface import Stat

__all__ = export = _export.Export()  # type: ignore


@export
class SupportsAsyncReadChunks(Protocol):
    """Async variant of the :class:`SupportsReadChunks` protocol."""

    def read_chunks(self, path: str, chunk_size: int = 65535) -> AsyncGenerator[bytes, None]:
        """Return a generator for reading file in chunks of given maximum size.

        This is the async version of :meth:`SupportsReadChunks.read_chunks`
        method.

        :param path:
            The path to a file to read.

        :param chunk_size:
            The maximum chunk size, in bytes.
        """
        ...


@export
class SupportsAsyncWriteChunks(Protocol):
    """Async variant of the :class:`SupportsWriteChunks` protocol."""

    def write_chunks(self, path: str, chunk_gen: AsyncGenerator[bytes, None]) -> AsyncGenerator[int, None]:
        """Generator for creating or overwriting files.

        This is the async version of :meth:`SupportsWriteChunks.write_chunks`
        method.

        :param path:
            The path to a file to create or replace.

        :param chunk_gen:
            Async generator yielding file chunks.
        """
        ...


@export
class AsyncFlatFsReader(SupportsAsyncReadChunks, Protocol):
    """Async variant of the :class:`FlatFsReader` protocol."""

    def scan(self) -> AsyncIterator[str]:
        """Return iterator that yields normalized paths to existing files.

        This is the async version of :meth:`FlatFsReader.scan` method.
        """
        ...

    async def stat(self, path: str) -> Stat:
        """Get stats of a file at given path.

        This is the async version of :meth:`FlatFsReader.stat` method.

        :param path:
            The path to a file.
        """
        ...

    async def exists(self, path: str) -> bool:
        """Check if file at given path exists.

        This is the async version of :meth:`FlatFsReader.exists` method.

        :param path:
            The path to check.
        """
        ...


@export
class AsyncFlatFsReaderWriter(AsyncFlatFsReader, SupportsAsyncWriteChunks, Protocol):
    """Async variant of the :class:`FlatFsReaderWriter` protocol."""

    async def remove(self, path: str):
        """Remove existing file.

        This is the async version of :meth:`FlatFsReaderWriter.remove` method.

        :param path:
            The path to a file to remove.
        """
        ...
