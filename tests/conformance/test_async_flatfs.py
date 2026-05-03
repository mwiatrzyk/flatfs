import pathlib
from typing import Callable

import pytest

from flatfs.api import (
    AsyncFlatFsAdapter,
    InMemoryFlatFs,
    LocalFlatFs,
    PathNotFoundError,
    AsyncFlatFsReaderWriter,
    async_read_bytes,
    async_read_text,
    async_write_bytes,
    async_write_text,
)

UUT = AsyncFlatFsReaderWriter


@pytest.fixture(
    params=[
        lambda root_dir: AsyncFlatFsAdapter(LocalFlatFs(root_dir)),
        lambda root_dir: AsyncFlatFsAdapter(InMemoryFlatFs()),
    ]
)
def uut_factory(request):
    return request.param


@pytest.fixture
def uut(uut_factory: Callable[[pathlib.Path], UUT], tmp_path: pathlib.Path):
    return uut_factory(tmp_path)


@pytest.fixture(
    params=[
        ("foo.txt", "/foo.txt"),
        ("/bar.txt", "/bar.txt"),
        ("/spam/baz/dummy.txt", "/spam/baz/dummy.txt"),
        ("/spam/baz/../dummy.txt", "/spam/dummy.txt"),
    ]
)
def path_normalized_path(request):
    return request.param


@pytest.fixture(params=[b"the dummy file content"])
def data(request):
    return request.param


@pytest.fixture(params=[[b"the", b" dummy", b" file", b" content"]])
def chunked_data(request):
    return request.param


@pytest.fixture
def path(path_normalized_path: tuple):
    return path_normalized_path[0]


@pytest.fixture
def normalized_path(path_normalized_path: tuple):
    return path_normalized_path[1]


async def test_binary_file_and_read_it_back(uut: UUT, path: str, data: bytes):
    await async_write_bytes(uut, path, data)
    assert await async_read_bytes(uut, path) == data


async def test_text_file_and_read_it_back(uut: UUT, path: str):
    await async_write_text(uut, path, "some text")
    assert await async_read_text(uut, path) == "some text"


async def test_create_file_and_read_it_back_in_chunks(uut: UUT, path: str, data: bytes):
    await async_write_bytes(uut, path, data)
    chunks = [c async for c in uut.read_chunks(path, chunk_size=5)]
    assert len(chunks) > 1
    assert b"".join(chunks) == data


async def test_create_file_from_chunks_and_read_it_back(uut: UUT, path: str, chunked_data: list[bytes]):
    async def gen():
        for chunk in chunked_data:
            yield chunk

    await uut.write_chunks(path, gen())
    assert await async_read_bytes(uut, path) == b"".join(chunked_data)


async def test_check_if_file_exists(uut: UUT, path: str, data: bytes):
    assert await uut.exists(path) is False
    await async_write_bytes(uut, path, data)
    assert await uut.exists(path) is True


async def test_removed_file_no_longer_exists(uut: UUT, path: str, data: bytes):
    assert await uut.exists(path) is False
    await async_write_bytes(uut, path, data)
    assert await uut.exists(path) is True
    await uut.remove(path)
    assert await uut.exists(path) is False


async def test_scan_returns_normalized_path_to_existing_file(uut: UUT, path: str, data: bytes, normalized_path: str):
    await async_write_bytes(uut, path, data)
    assert list([x async for x in uut.scan()]) == [normalized_path]


async def test_read_chunks_raises_path_not_found_if_files_does_not_exist(uut: UUT, path: str):
    with pytest.raises(PathNotFoundError) as excinfo:
        _ = list([x async for x in uut.read_chunks(path)])
    assert excinfo.value.path == path


async def test_remove_raises_path_not_found_if_files_does_not_exist(uut: UUT, path: str):
    with pytest.raises(PathNotFoundError) as excinfo:
        await uut.remove(path)
    assert excinfo.value.path == path


async def test_double_read_chunks_returns_same_data(uut: UUT, path: str, data: bytes):
    await async_write_bytes(uut, path, data)
    assert b"".join([x async for x in uut.read_chunks(path)]) == data
    assert b"".join([x async for x in uut.read_chunks(path)]) == data
