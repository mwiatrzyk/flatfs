from . import _export
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

    def gen():
        data_left = data
        while True:
            chunk = data_left[:chunk_size]
            if not chunk:
                break
            data_left = data_left[chunk_size:]
            yield chunk

    return fs.write_chunks(path, gen())


@export
def read_text(fs: SupportsReadChunks, path: str, encoding: str = "utf-8", chunk_size: int = 65535) -> str:
    """Read whole text file and return as string.

    Uses :func:`read_bytes` underneath and then just decodes its output using
    provided *encoding*, which is ``utf-8`` by default.
    """
    return read_bytes(fs, path, chunk_size).decode(encoding)


@export
def write_text(fs: SupportsWriteChunks, path: str, data: str, encoding: str = "utf-8", chunk_size: int = 65535):
    """Create new text file or replace existing with given text data.

    Uses :func:`write_bytes` underneath and just encodes given *data* with
    provided *encoding*, which is ``utf-8`` by default.
    """
    return write_bytes(fs, path, data.encode(encoding), chunk_size)


@export
async def async_read_bytes(fs: SupportsAsyncReadChunks, path: str, chunk_size: int = 65535) -> bytes:
    """Same as :func:`read_bytes`, but for async code."""
    out = b""
    async for chunk in fs.read_chunks(path, chunk_size):
        out += chunk
    return out


@export
async def async_write_bytes(fs: SupportsAsyncWriteChunks, path: str, data: bytes, chunk_size: int = 65535) -> int:
    """Same as :func:`write_bytes`, but for async code."""

    async def gen():
        data_left = data
        while True:
            chunk = data_left[:chunk_size]
            if not chunk:
                break
            data_left = data_left[chunk_size:]
            yield chunk

    return await fs.write_chunks(path, gen())


@export
async def async_read_text(
    fs: SupportsAsyncReadChunks, path: str, encoding: str = "utf-8", chunk_size: int = 65535
) -> str:
    """Same as :func:`read_text`, but for async code."""
    return (await async_read_bytes(fs, path, chunk_size)).decode(encoding)


@export
async def async_write_text(
    fs: SupportsAsyncWriteChunks, path: str, data: str, encoding: str = "utf-8", chunk_size: int = 65535
):
    """Same as :func:`write_text`, but for async code."""
    await async_write_bytes(fs, path, data.encode(encoding), chunk_size)


@export
class BinaryReader:
    """Helper for reading bytes from a file."""

    def __init__(self, fs: SupportsReadChunks, path: str, chunk_size: int=65535):
        self.__chunk_gen = fs.read_chunks(path, chunk_size)
        self.__current_chunk = b""

    def read(self, count: int) -> bytes:
        """Read at most *count* bytes from an open file.

        :param count:
            The maximum number of bytes to read.
        """
        if not self.__current_chunk:
            self.__current_chunk = next(self.__chunk_gen, b"")
        fragment = self.__current_chunk[:count]
        self.__current_chunk = self.__current_chunk[count:]
        return fragment

    def close(self):
        """Close this reader.

        This also closes the underlying file that is opened by flat filesystem
        object given in the constructor.

        This method is idempotent.
        """
        self.__current_chunk = b""
        self.__chunk_gen.close()
