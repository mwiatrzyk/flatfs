import asyncio
from contextlib import AbstractAsyncContextManager
from typing import AsyncIterator, Optional

from flatfs import _export, _utils, _compat

from .interface import SupportsAsyncReadChunks, SupportsAsyncWriteChunks

__all__ = export = _export.Export()  # type: ignore


@export
async def async_read_bytes(fs: SupportsAsyncReadChunks, path: str, chunk_size: int = 65535) -> bytes:
    """Async variant of the :func:`read_bytes` helper."""
    out = b""
    async for chunk in fs.read_chunks(path, chunk_size):
        out += chunk
    return out


@export
async def async_write_bytes(fs: SupportsAsyncWriteChunks, path: str, data: bytes, chunk_size: int = 65535) -> int:
    """Async variant of the :func:`write_bytes` helper."""
    total_bytes = 0
    async for byte_count in fs.write_chunks(path, _utils.async_split_into_chunks(data, chunk_size)):
        total_bytes += byte_count
    return total_bytes


@export
async def async_read_text(
    fs: SupportsAsyncReadChunks, path: str, encoding: str = "utf-8", chunk_size: int = 65535
) -> str:
    """Async variant of the :func:`read_text` helper."""
    return (await async_read_bytes(fs, path, chunk_size)).decode(encoding)


@export
async def async_write_text(
    fs: SupportsAsyncWriteChunks, path: str, data: str, encoding: str = "utf-8", chunk_size: int = 65535
):
    """Async variant of the :func:`write_text` helper."""
    await async_write_bytes(fs, path, data.encode(encoding), chunk_size)


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

    async def __aexit__(self, exc_type, exc_value, traceback) -> Optional[bool]:
        return await self.close()

    async def __write_chunk(self, chunk: bytes):
        self.__chunk_queue.put_nowait(chunk)
        await _compat.anext(self.__writer)

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
class AsyncBufferedReader(AbstractAsyncContextManager):
    """Async variant of the :class:`BufferedReader` class."""

    def __init__(self, fs: SupportsAsyncReadChunks, path: str, buffer_size: int = 65535):
        self.__reader = fs.read_chunks(path, chunk_size=buffer_size)
        self.__buffer = b""

    async def __aenter__(self) -> "AsyncBufferedReader":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> Optional[bool]:
        return await self.close()

    async def close(self):
        self.__buffer = b""
        await self.__reader.aclose()

    async def read(self, count: int) -> bytes:
        if not self.__buffer:
            self.__buffer = await _compat.anext(self.__reader, b"")
        data = self.__buffer[:count]
        self.__buffer = self.__buffer[count:]
        return data


@export
class AsyncBufferedTextReader(AbstractAsyncContextManager):
    """Async variant of the :class:`BufferedTextReader` class."""

    def __init__(self, fs: SupportsAsyncReadChunks, path: str, encoding: str = "utf-8", buffer_size: int = 65535):
        self.__reader = fs.read_chunks(path, chunk_size=buffer_size)
        self.__encoding = encoding
        self.__buffer = ""

    async def __read_next_chunk(self) -> str:
        return (await _compat.anext(self.__reader, b"")).decode(self.__encoding)

    async def __aenter__(self) -> "AsyncBufferedTextReader":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> Optional[bool]:
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
