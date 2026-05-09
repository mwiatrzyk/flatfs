import pytest

from mockify.api import Mock, Iterate, YieldAsync, Invoke, InvokeAsync, Any, Return, satisfied

from flatfs.helpers import BinaryReader, async_read_bytes, async_write_bytes, read_bytes, write_bytes


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


class TestBinaryReader:
    def test_read_whole_file_with_one_chunk_read(self, fs):
        chunks_read = [b"foo bar baz"]
        fs.read_chunks.expect_call("foo.txt", 65535).will_once(Iterate(chunks_read))
        uut = BinaryReader(fs, "foo.txt")
        assert uut.read(4) == b"foo "
        assert uut.read(4) == b"bar "
        assert uut.read(4) == b"baz"
        assert uut.read(4) == b""

    def test_read_whole_file_when_two_chunks_read(self, fs):
        chunks_read = [b"foo bar", b" baz"]
        fs.read_chunks.expect_call("foo.txt", 7).will_once(Iterate(chunks_read))
        uut = BinaryReader(fs, "foo.txt", chunk_size=7)
        assert uut.read(4) == b"foo "
        assert uut.read(4) == b"bar"  # 1st chunk ends, so <4 bytes read
        assert uut.read(4) == b" baz"
        assert uut.read(4) == b""

    def test_when_reader_closed_then_generator_returned_by_read_chunks_is_also_closed(self, fs):
        def gen():
            yield b"first chunk"
            yield b"second chunk"

        running_gen = gen()
        fs.read_chunks.expect_call("foo.txt", 65535).will_once(Return(running_gen))
        uut = BinaryReader(fs, "foo.txt")
        uut.close()
        with pytest.raises(StopIteration):
            next(running_gen)

    def test_when_reader_closed_then_internal_read_buffer_is_cleared(self, fs):
        def gen():
            yield b"first chunk"
            yield b"second chunk"

        running_gen = gen()
        fs.read_chunks.expect_call("foo.txt", 65535).will_once(Return(running_gen))
        uut = BinaryReader(fs, "foo.txt")
        assert uut.read(5) == b"first"
        uut.close()
        assert uut.read(123) == b""

    def test_close_the_reader_twice(self, fs):
        def gen():
            yield b"first chunk"
            yield b"second chunk"

        running_gen = gen()
        fs.read_chunks.expect_call("foo.txt", 65535).will_once(Return(running_gen))
        uut = BinaryReader(fs, "foo.txt")
        assert uut.read(5) == b"first"
        uut.close()
        uut.close()
        assert uut.read(123) == b""
        with pytest.raises(StopIteration):
            next(running_gen)
