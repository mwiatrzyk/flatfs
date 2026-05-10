import asyncio
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from queue import Queue
from types import TracebackType
from typing import Iterator, AsyncIterator

from . import _export, _utils
from .interface import SupportsAsyncReadChunks, SupportsAsyncWriteChunks, SupportsReadChunks, SupportsWriteChunks

__all__ = export = _export.Export()  # type: ignore


@export
def read_bytes(fs: SupportsReadChunks, path: str, chunk_size: int = 65535) -> bytes:
    """Read whole file and return as bytes.

    :param fs:
        FlatFS object to read from.

    :param path:
        Path to a file to read.

    :param chunk_size:
        The chunk size to use during read.

        This is the maximum number of bytes to read from a file per single read
        operation.

        Defaults to 64kB.
    """
    out = b""
    for chunk in fs.read_chunks(path, chunk_size):
        out += chunk
    return out


@export
async def async_read_bytes(fs: SupportsAsyncReadChunks, path: str, chunk_size: int = 65535) -> bytes:
    """Async variant of the :func:`read_bytes` helper."""
    out = b""
    async for chunk in fs.read_chunks(path, chunk_size):
        out += chunk
    return out


@export
def write_bytes(fs: SupportsWriteChunks, path: str, data: bytes, chunk_size: int = 65535) -> int:
    """Write given data to file at given path either creating the file, or
    replacing with new content.

    Returns the number of bytes written.

    :param fs:
        FlatFS object to write to.

    :param path:
        The path to a file to create or replace.

    :param data:
        The data to write.

    :param chunk_size:
        The chunk size to use during writing.

        If *data* length is greater, it will be split into chunks and written
        chunk by chunk, with each chunk having at most *chunk_size* bytes.

        Defaults to 64kB.
    """
    total_bytes = 0
    for byte_count in fs.write_chunks(path, _utils.split_into_chunks(data, chunk_size)):
        total_bytes += byte_count
    return total_bytes


@export
async def async_write_bytes(fs: SupportsAsyncWriteChunks, path: str, data: bytes, chunk_size: int = 65535) -> int:
    """Async variant of the :func:`write_bytes` helper."""
    total_bytes = 0
    async for byte_count in fs.write_chunks(path, _utils.async_split_into_chunks(data, chunk_size)):
        total_bytes += byte_count
    return total_bytes


@export
def read_text(fs: SupportsReadChunks, path: str, encoding: str = "utf-8", chunk_size: int = 65535) -> str:
    """Read whole text file and return as string.

    Uses :func:`read_bytes` underneath and then just decodes its output using
    provided *encoding*, which is ``utf-8`` by default.

    :param fs:
        FlatFS object to read from.

    :param path:
        The path to a file to read.

    :param encoding:
        The encoding to use.

    :param chunk_size:
        The chunk size to use during reading.

        This tells how many bytes can at most be read in single pass.
    """
    return read_bytes(fs, path, chunk_size).decode(encoding)


@export
async def async_read_text(
    fs: SupportsAsyncReadChunks, path: str, encoding: str = "utf-8", chunk_size: int = 65535
) -> str:
    """Async variant of the :func:`read_text` helper."""
    return (await async_read_bytes(fs, path, chunk_size)).decode(encoding)


@export
def write_text(fs: SupportsWriteChunks, path: str, data: str, encoding: str = "utf-8", chunk_size: int = 65535):
    """Create new text file or replace existing with given text data.

    Uses :func:`write_bytes` underneath and just encodes given *data* with
    provided *encoding*, which is ``utf-8`` by default.

    :param fs:
        FlatFS object to write to.

    :param path:
        The path to a file to create or replace.

    :param encoding:
        The encoding to use.

    :param chunk_size:
        The chunk size to use during writing.

        This tells how many bytes can at most be written in a single pass.
    """
    return write_bytes(fs, path, data.encode(encoding), chunk_size)


@export
async def async_write_text(
    fs: SupportsAsyncWriteChunks, path: str, data: str, encoding: str = "utf-8", chunk_size: int = 65535
):
    """Async variant of the :func:`write_text` helper."""
    await async_write_bytes(fs, path, data.encode(encoding), chunk_size)


@export
class BufferedWriter(AbstractContextManager):
    """Buffered writer for creating new or replacing existing files.

    It allows efficient writing of arbitrary binary data thanks to the buffer
    being used. Once the length of buffered data exceeds given buffer size, the
    data is flushed to the underlying filesystem and buffer is cleared. This
    allows to limit actual write operations to minimum.

    This helper can be used as a context manager.

    :param fs:
        FlatFS object to write to.

    :param path:
        Path to a file to create or replace.

    :param buffer_size:
        The size of a buffer, in bytes.

        This is the maximum amount of data that can be buffered before it is
        flushed to the backend. This is equivalent to the maximum size of a
        single chunk that is written to the underlying filesystem.
    """

    def __init__(self, fs: SupportsWriteChunks, path: str, buffer_size: int = 65535):
        self.__chunk_queue: Queue[bytes] = Queue()
        self.__buffer_size = buffer_size
        self.__buffer = b""
        self.__writer = fs.write_chunks(path, _utils.generate_chunks_from_queue(self.__chunk_queue))

    def __enter__(self) -> "BufferedWriter":
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> bool | None:
        return self.close()

    def __write_chunk(self, chunk: bytes):
        self.__chunk_queue.put(chunk)
        next(self.__writer)

    def flush(self):
        """Flush the buffer and clear it.

        This is automatically called on close or context manager exit.
        """
        if not self.__buffer:
            return  # Nothing to do
        self.__write_chunk(self.__buffer)
        self.__buffer = b""

    def close(self):
        """Flush remaining data and close underlying file."""
        self.flush()
        return self.__writer.close()

    def write(self, data: bytes) -> int:
        """Write data to the buffer.

        If the buffer is full, it will be flushed and remaining data (if any)
        will be used to initialize emptied buffer.

        :param data:
            The data to write.
        """
        self.__buffer += data
        while len(self.__buffer) > self.__buffer_size:
            chunk = self.__buffer[: self.__buffer_size]
            self.__write_chunk(chunk)
            self.__buffer = self.__buffer[self.__buffer_size :]
        return len(data)


@export
class AsyncBufferedWriter(AbstractAsyncContextManager):
    """Async variant of the :class:`BufferedWriter` class."""

    def __init__(self, fs: SupportsAsyncWriteChunks, path: str, buffer_size: int = 65535):
        self.__chunk_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self.__buffer_size = buffer_size
        self.__buffer = b""
        self.__writer = fs.write_chunks(path, _utils.async_generate_chunks_from_queue(self.__chunk_queue))

    async def __aenter__(self) -> "AsyncBufferedWriter":
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> bool | None:
        return await self.close()

    async def __write_chunk(self, chunk: bytes):
        self.__chunk_queue.put_nowait(chunk)
        await anext(self.__writer)

    async def write(self, data: bytes) -> int:
        self.__buffer += data
        while len(self.__buffer) > self.__buffer_size:
            chunk = self.__buffer[: self.__buffer_size]
            await self.__write_chunk(chunk)
            self.__buffer = self.__buffer[self.__buffer_size :]
        return len(data)

    async def flush(self):
        if not self.__buffer:
            return  # Nothing to do
        await self.__write_chunk(self.__buffer)
        self.__buffer = b""

    async def close(self):
        await self.flush()
        await self.__writer.aclose()


@export
class BufferedReader(AbstractContextManager):
    """Helper for buffered reading from underlying flat filesystem.

    If reads from an underlying filesystem chunks of bytes of given maximum
    length and stores it locally for reading. When entire buffer is read, the
    next chunk is fetched from the filesystem. The whole operation is repeated
    until file is fully read or the reader is closed.

    This helper can be used via context manager.

    :param fs:
        The filesystem to read from.

    :param path:
        The path to a file to read.

    :param buffer_size:
        The size of a read buffer, in bytes.

        This is also the maximum size of a single chunk read from a file.
    """

    def __init__(self, fs: SupportsReadChunks, path: str, buffer_size: int = 65535):
        self.__reader = fs.read_chunks(path, chunk_size=buffer_size)
        self.__buffer = b""

    def __enter__(self) -> "BufferedReader":
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> bool | None:
        return self.close()

    def close(self):
        self.__buffer = b""
        self.__reader.close()

    def read(self, count: int) -> bytes:
        if not self.__buffer:
            self.__buffer = next(self.__reader, b"")
        data = self.__buffer[:count]
        self.__buffer = self.__buffer[count:]
        return data


@export
class AsyncBufferedReader(AbstractAsyncContextManager):
    """Async variant of the :class:`BufferedReader` class."""

    def __init__(self, fs: SupportsAsyncReadChunks, path: str, buffer_size: int = 65535):
        self.__reader = fs.read_chunks(path, chunk_size=buffer_size)
        self.__buffer = b""

    async def __aenter__(self) -> "AsyncBufferedReader":
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> bool | None:
        return await self.close()

    async def close(self):
        self.__buffer = b""
        await self.__reader.aclose()

    async def read(self, count: int) -> bytes:
        if not self.__buffer:
            self.__buffer = await anext(self.__reader, b"")
        data = self.__buffer[:count]
        self.__buffer = self.__buffer[count:]
        return data


@export
class BufferedTextReader(AbstractContextManager):
    """Equivalent of :class:`BufferedReader` for text files.

    It reads at most *buffer_size* bytes from underlying file, stores in local
    buffer, and then streams from that buffer until it expires. Once it is
    expired and more data is needed, the next chunk of data is automatically
    read and stored in the buffer.

    :param fs:
        The filesystem reader object.

    :param path:
        The path to a text file to read.

    :param encoding:
        The encoding to use.

    :param buffer_size:
        The maximum amount of data to read from an underlying file in one pass,
        in bytes.
    """

    def __init__(self, fs: SupportsReadChunks, path: str, encoding: str = "utf-8", buffer_size: int = 65535):
        self.__reader = fs.read_chunks(path, chunk_size=buffer_size)
        self.__encoding = encoding
        self.__buffer = ""

    def __read_next_chunk(self) -> str:
        return next(self.__reader, b"").decode(self.__encoding)

    def __enter__(self) -> "BufferedTextReader":
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> bool | None:
        return self.close()

    def __iter__(self) -> Iterator[str]:
        while next_chunk := self.__read_next_chunk():
            self.__buffer += next_chunk
            lines = self.__buffer.splitlines()
            if len(lines) > 1:
                for line in lines[:-1]:
                    yield line
                self.__buffer = lines[-1]
        yield self.__buffer

    def read(self, count: int) -> str:
        """Read at most *count* characters.

        :param count:
            The maximum number of characters to read.
        """
        if not self.__buffer:
            self.__buffer = self.__read_next_chunk()
        out = self.__buffer[:count]
        self.__buffer = self.__buffer[count:]
        return out

    def close(self):
        """Close this reader.

        This also closes the underlying file.
        """
        self.__buffer = ""
        self.__reader.close()


@export
class AsyncBufferedTextReader(AbstractAsyncContextManager):
    """Async variant of the :class:`BufferedTextReader` class."""

    def __init__(self, fs: SupportsAsyncReadChunks, path: str, encoding: str = "utf-8", buffer_size: int = 65535):
        self.__reader = fs.read_chunks(path, chunk_size=buffer_size)
        self.__encoding = encoding
        self.__buffer = ""

    async def __read_next_chunk(self) -> str:
        return (await anext(self.__reader, b"")).decode(self.__encoding)

    async def __aenter__(self) -> "AsyncBufferedTextReader":
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> bool | None:
        return await self.close()

    async def __aiter__(self) -> AsyncIterator[str]:
        while next_chunk := await self.__read_next_chunk():
            self.__buffer += next_chunk
            lines = self.__buffer.splitlines()
            if len(lines) > 1:
                for line in lines[:-1]:
                    yield line
                self.__buffer = lines[-1]
        yield self.__buffer

    async def read(self, count: int) -> str:
        if not self.__buffer:
            self.__buffer = await self.__read_next_chunk()
        out = self.__buffer[:count]
        self.__buffer = self.__buffer[count:]
        return out

    async def close(self):
        self.__buffer = ""
        await self.__reader.aclose()
