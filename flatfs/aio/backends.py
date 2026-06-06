import asyncio
from queue import Queue
from typing import AsyncGenerator, AsyncIterator, Union

from flatfs import _export, _utils
from flatfs.interface import FlatFsReaderWriter, Stat

__all__ = export = _export.Export()  # type: ignore


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
        queue: asyncio.Queue[str] = asyncio.Queue()
        while True:
            path = await queue.get()
            if not path:
                break
            yield path

    async def exists(self, path: str) -> bool:
        return await _utils.run_blocking(self.__target.exists, path)

    async def stat(self, path: str) -> Stat:
        return await _utils.run_blocking(self.__target.stat, path)

    async def read_chunks(self, path: str, chunk_size: int = 65535) -> AsyncIterator[bytes]:

        def reader():
            try:
                for chunk in self.__target.read_chunks(path, chunk_size):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
                loop.call_soon_threadsafe(queue.put_nowait, b"")
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, e)

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[Union[bytes, Exception]] = asyncio.Queue()
        asyncio.create_task(_utils.run_blocking(reader))
        while True:
            chunk_or_exc = await queue.get()
            if not chunk_or_exc:
                break
            if isinstance(chunk_or_exc, Exception):
                raise chunk_or_exc
            yield chunk_or_exc

    async def write_chunks(self, path: str, chunk_gen: AsyncGenerator[bytes, None]) -> AsyncGenerator[int, None]:

        def blocking_writer():
            for write_count in self.__target.write_chunks(path, _utils.generate_chunks_from_queue(chunk_queue)):
                loop.call_soon_threadsafe(ack_queue.put_nowait, write_count)

        loop = asyncio.get_running_loop()
        chunk_queue: Queue[bytes] = Queue()
        ack_queue: asyncio.Queue[int] = asyncio.Queue()
        task = asyncio.create_task(_utils.run_blocking(blocking_writer))
        try:
            async for chunk in chunk_gen:
                chunk_queue.put(chunk)
                yield await ack_queue.get()
        finally:
            chunk_queue.put(b"")
            await task

    async def remove(self, path: str):
        await _utils.run_blocking(self.__target.remove, path)
