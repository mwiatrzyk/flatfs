import asyncio
import datetime
import functools
import queue
from typing import AsyncGenerator, Callable, Generator, TypeVar

from flatfs.exc import PathAccessError

T = TypeVar("T")


def normalize_path(path: str) -> str:
    """Normalizes path by removing duplicated slash characters and by
    evaluating relative path components (e.g. ``../`` or ``./``).

    Returns normalized path, or raises :exc:`flatfs.exc.FileAccessError` if
    final path would go beyond filesystem bounds.

    :param path:
        The path to normalize.
    """
    parts: list[str] = []
    for part in path.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            if not parts:
                raise PathAccessError(path)
            parts.pop()
        else:
            parts.append(part)
    out = "/".join(parts)
    if out[0] == "/":
        return out
    return "/" + out


async def run_blocking(func: Callable[..., T], *args, **kwargs) -> T:
    """Run blocking (i.e. non-async) task in an event loop's default
    executor.

    On success, return *func*'s result, on failure raise *func*'s exception.

    :param func:
        The non-async callable to run.

    :param `*args`:
        Positional args to be passed to *func*.

    :param `**kwargs`:
        Named args to be passed to *func*.
    """
    wrapped_func = functools.partial(func, *args, **kwargs)
    return await asyncio.get_running_loop().run_in_executor(None, wrapped_func)


def utcnow() -> datetime.datetime:
    """Get the current date and time in UTC."""
    return datetime.datetime.now(datetime.timezone.utc)


def split_into_chunks(data: bytes, chunk_size: int) -> Generator[bytes, None, None]:
    """Generator that splits given binary data into chunks of provided maximum size.

    :param data:
        The data to split.

    :chunk_size:
        The maximum size of a single chunk.
    """
    while chunk := data[:chunk_size]:
        yield chunk
        data = data[chunk_size:]


async def async_split_into_chunks(data: bytes, chunk_size: int) -> AsyncGenerator[bytes, None]:
    """Async variant of the :func:`split_into_chunks` function.

    :param data:
        The data to split.

    :param chunk_size:
        The maximum size of a single chunk.
    """
    while chunk := data[:chunk_size]:
        yield chunk
        data = data[chunk_size:]


def generate_chunks_from_queue(chunk_queue: queue.Queue[bytes]) -> Generator[bytes, None, None]:
    """Generator that yields chunks it receives via provided queue until empty
    bytes object is received.

    :param chunk_queue:
        Chunk queue to adapt.
    """
    while True:
        chunk = chunk_queue.get()
        if not chunk:
            return
        yield chunk
