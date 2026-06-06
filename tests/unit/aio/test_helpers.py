import pytest

from mockify.api import Mock, YieldAsync, Invoke, Any, satisfied

from flatfs.aio.backends import AsyncFlatFsAdapter
from flatfs.aio.helpers import (
    AsyncBufferedReader,
    AsyncBufferedTextReader,
    AsyncBufferedWriter,
    async_read_bytes,
    async_write_bytes,
    async_write_text,
)
from flatfs.backends import InMemoryFlatFs


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
        async for chunk in gen:
            chunks.append(chunk)
            yield len(chunk)

    fs.write_chunks.expect_call(path, Any()).will_once(Invoke(write_chunks))
    assert (await async_write_bytes(fs, path, data, chunk_size)) == len(data)
    assert chunks == expected_chunks


class TestAsyncBufferedWriter:
    @pytest.fixture
    def path(self):
        return "foo.dat"

    @pytest.fixture
    def payload(self):
        return b"dummy file payload"

    @pytest.fixture
    def fs(self):
        return AsyncFlatFsAdapter(InMemoryFlatFs())

    async def test_create_file_and_read_it_back_using_default_buffer_size(self, fs, path, payload):
        async with AsyncBufferedWriter(fs, path) as writer:
            assert await writer.write(payload) == len(payload)
        assert await async_read_bytes(fs, path) == payload

    @pytest.mark.parametrize("buffer_size", [1, 3, 65535])
    async def test_create_file_and_read_it_back_using_given_buffer_size(self, fs, path, payload, buffer_size):
        async with AsyncBufferedWriter(fs, path, buffer_size=buffer_size) as writer:
            assert await writer.write(payload) == len(payload)
        assert await async_read_bytes(fs, path) == payload


class TestAsyncBufferedReader:
    @pytest.fixture
    def path(self):
        return "foo.dat"

    @pytest.fixture
    def fs(self):
        return AsyncFlatFsAdapter(InMemoryFlatFs())

    async def test_write_file_and_read_it_in_one_chunk(self, fs, path):
        await async_write_bytes(fs, path, b"foo bar baz")
        async with AsyncBufferedReader(fs, path) as reader:
            assert await reader.read(128) == b"foo bar baz"

    async def test_write_file_and_read_it_several_chunks(self, fs, path):
        await async_write_bytes(fs, path, b"foo bar baz")
        async with AsyncBufferedReader(fs, path, buffer_size=4) as reader:
            assert await reader.read(128) == b"foo "
            assert await reader.read(128) == b"bar "
            assert await reader.read(128) == b"baz"

    async def test_after_close_reading_returns_empty_bytes(self, fs, path):
        await async_write_bytes(fs, path, b"foo bar baz")
        reader = AsyncBufferedReader(fs, path, buffer_size=4)
        assert await reader.read(128) == b"foo "
        await reader.close()
        assert await reader.read(123) == b""

    async def test_after_context_manager_exit_reading_returns_empty_bytes(self, fs, path):
        await async_write_bytes(fs, path, b"foo bar baz")
        async with AsyncBufferedReader(fs, path, buffer_size=4) as reader:
            assert await reader.read(128) == b"foo "
            await reader.close()
            assert await reader.read(123) == b""


class TestAsyncBufferedTextReader:
    @pytest.fixture
    def path(self):
        return "foo.dat"

    @pytest.fixture
    def fs(self):
        return AsyncFlatFsAdapter(InMemoryFlatFs())

    async def test_write_file_and_read_it_in_one_chunk(self, fs, path):
        await async_write_text(fs, path, "foo bar baz")
        async with AsyncBufferedTextReader(fs, path) as reader:
            assert await reader.read(128) == "foo bar baz"

    async def test_write_file_and_read_using_count_greater_than_chunk_size(self, fs, path):
        await async_write_text(fs, path, "foo bar baz")
        async with AsyncBufferedTextReader(fs, path, buffer_size=4) as reader:
            assert await reader.read(128) == "foo "
            assert await reader.read(128) == "bar "
            assert await reader.read(128) == "baz"

    async def test_write_file_and_read_using_count_lower_than_chunk_size(self, fs, path):
        await async_write_text(fs, path, "foo bar baz")
        async with AsyncBufferedTextReader(fs, path, buffer_size=4) as reader:
            assert await reader.read(3) == "foo"
            assert await reader.read(3) == " "
            assert await reader.read(3) == "bar"
            assert await reader.read(3) == " "
            assert await reader.read(3) == "baz"

    async def test_write_file_and_iterate_over_rows(self, fs, path):
        await async_write_text(fs, path, "this is\na multiline\ntext file")
        async with AsyncBufferedTextReader(fs, path) as reader:
            assert [x async for x in reader] == ["this is", "a multiline", "text file"]

    @pytest.mark.parametrize("buffer_size", [1, 3, 128])
    async def test_write_file_and_iterate_over_rows_with_given_buffer_size(self, fs, path, buffer_size):
        await async_write_text(fs, path, "this is\na multiline\ntext file")
        async with AsyncBufferedTextReader(fs, path, buffer_size=buffer_size) as reader:
            assert [x async for x in reader] == ["this is", "a multiline", "text file"]

    async def test_after_close_reading_returns_empty_bytes(self, fs, path):
        await async_write_text(fs, path, "foo bar baz")
        reader = AsyncBufferedTextReader(fs, path, buffer_size=4)
        assert await reader.read(128) == "foo "
        await reader.close()
        assert await reader.read(123) == ""

    async def test_after_context_manager_exit_reading_returns_empty_bytes(self, fs, path):
        await async_write_text(fs, path, "foo bar baz")
        async with AsyncBufferedTextReader(fs, path, buffer_size=4) as reader:
            assert await reader.read(128) == "foo "
            await reader.close()
            assert await reader.read(123) == ""
