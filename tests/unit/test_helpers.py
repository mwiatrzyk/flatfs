import pytest

from mockify.api import Mock, Iterate, YieldAsync, Invoke, InvokeAsync, Any, satisfied

from flatfs.helpers import async_read_bytes, async_write_bytes, read_bytes, write_bytes


@pytest.fixture
def fs():
    fs = Mock("fs")
    with satisfied(fs):
        yield fs


@pytest.mark.parametrize(
    "path, chunk_size, chunks",
    [
        ("foo.txt", 123, [b"foo", b"bar"]),
    ],
)
def test_read_bytes(fs, path, chunk_size, chunks):
    fs.read_chunks.expect_call(path, chunk_size).will_once(Iterate(chunks))
    assert read_bytes(fs, path, chunk_size) == b"".join(chunks)


@pytest.mark.parametrize(
    "path, chunk_size, data, expected_chunks",
    [
        ("foo.txt", 3, b"spam", [b"spa", b"m"]),
    ],
)
def test_write_bytes(fs, path, chunk_size, data, expected_chunks):
    chunks = []

    def write_chunks(path, gen):
        chunks.extend(gen)

    fs.write_chunks.expect_call(path, Any()).will_once(Invoke(write_chunks))
    write_bytes(fs, path, data, chunk_size)
    assert chunks == expected_chunks


@pytest.mark.parametrize(
    "path, chunk_size, chunks",
    [
        ("foo.txt", 123, [b"foo", b"bar"]),
    ],
)
async def test_async_read_bytes(fs, path, chunk_size, chunks):
    fs.read_chunks.expect_call(path, chunk_size).will_once(YieldAsync(chunks))
    assert await async_read_bytes(fs, path, chunk_size) == b"".join(chunks)


@pytest.mark.parametrize(
    "path, chunk_size, data, expected_chunks",
    [
        ("foo.txt", 3, b"spam", [b"spa", b"m"]),
    ],
)
async def test_async_write_bytes(fs, path, chunk_size, data, expected_chunks):
    chunks = []

    async def write_chunks(path, gen):
        chunks.extend([x async for x in gen])

    fs.write_chunks.expect_call(path, Any()).will_once(InvokeAsync(write_chunks))
    await async_write_bytes(fs, path, data, chunk_size)
    assert chunks == expected_chunks
