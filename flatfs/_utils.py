import asyncio
import functools
from typing import Callable, TypeVar

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
    parts = []
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
