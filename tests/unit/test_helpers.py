import pytest

from mockify.api import Mock, Iterate, Invoke, Any, satisfied

from flatfs.backends import InMemoryFlatFs
from flatfs.helpers import (
    BufferedTextReader,
    BufferedReader,
    BufferedWriter,
    read_bytes,
    write_bytes,
    write_text,
)


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
        for chunk in gen:
            chunks.append(chunk)
            yield len(chunk)

    fs.write_chunks.expect_call(path, Any()).will_once(Invoke(write_chunks))
    assert write_bytes(fs, path, data, chunk_size) == len(data)
    assert chunks == expected_chunks


class TestBufferedWriter:
    @pytest.fixture
    def path(self):
        return "foo.dat"

    @pytest.fixture
    def payload(self):
        return b"dummy file payload"

    @pytest.fixture
    def fs(self):
        return InMemoryFlatFs()

    def test_create_file_and_read_it_back_using_default_buffer_size(self, fs, path, payload):
        with BufferedWriter(fs, path) as writer:
            assert writer.write(payload) == len(payload)
        assert read_bytes(fs, path) == payload

    @pytest.mark.parametrize("buffer_size", [1, 3, 65535])
    def test_create_file_and_read_it_back_using_given_buffer_size(self, fs, path, payload, buffer_size):
        with BufferedWriter(fs, path, buffer_size=buffer_size) as writer:
            assert writer.write(payload) == len(payload)
        assert read_bytes(fs, path) == payload


class TestBufferedReader:
    @pytest.fixture
    def path(self):
        return "foo.dat"

    @pytest.fixture
    def fs(self):
        return InMemoryFlatFs()

    def test_write_file_and_read_it_in_one_chunk(self, fs, path):
        write_bytes(fs, path, b"foo bar baz")
        with BufferedReader(fs, path) as reader:
            assert reader.read(128) == b"foo bar baz"

    def test_write_file_and_read_it_several_chunks(self, fs, path):
        write_bytes(fs, path, b"foo bar baz")
        with BufferedReader(fs, path, buffer_size=4) as reader:
            assert reader.read(128) == b"foo "
            assert reader.read(128) == b"bar "
            assert reader.read(128) == b"baz"

    def test_after_close_reading_returns_empty_bytes(self, fs, path):
        write_bytes(fs, path, b"foo bar baz")
        reader = BufferedReader(fs, path, buffer_size=4)
        assert reader.read(128) == b"foo "
        reader.close()
        assert reader.read(123) == b""

    def test_after_context_manager_exit_reading_returns_empty_bytes(self, fs, path):
        write_bytes(fs, path, b"foo bar baz")
        with BufferedReader(fs, path, buffer_size=4) as reader:
            assert reader.read(128) == b"foo "
            reader.close()
            assert reader.read(123) == b""


class TestBufferedTextReader:
    @pytest.fixture
    def path(self):
        return "foo.dat"

    @pytest.fixture
    def fs(self):
        return InMemoryFlatFs()

    def test_write_file_and_read_it_in_one_chunk(self, fs, path):
        write_text(fs, path, "foo bar baz")
        with BufferedTextReader(fs, path) as reader:
            assert reader.read(128) == "foo bar baz"

    def test_write_file_and_read_using_count_greater_than_chunk_size(self, fs, path):
        write_text(fs, path, "foo bar baz")
        with BufferedTextReader(fs, path, buffer_size=4) as reader:
            assert reader.read(128) == "foo "
            assert reader.read(128) == "bar "
            assert reader.read(128) == "baz"

    def test_write_file_and_read_using_count_lower_than_chunk_size(self, fs, path):
        write_text(fs, path, "foo bar baz")
        with BufferedTextReader(fs, path, buffer_size=4) as reader:
            assert reader.read(3) == "foo"
            assert reader.read(3) == " "
            assert reader.read(3) == "bar"
            assert reader.read(3) == " "
            assert reader.read(3) == "baz"

    def test_write_file_and_iterate_over_rows(self, fs, path):
        write_text(fs, path, "this is\na multiline\ntext file")
        with BufferedTextReader(fs, path) as reader:
            assert list(reader) == ["this is", "a multiline", "text file"]

    @pytest.mark.parametrize("buffer_size", [1, 3, 128])
    def test_write_file_and_iterate_over_rows_with_given_buffer_size(self, fs, path, buffer_size):
        write_text(fs, path, "this is\na multiline\ntext file")
        with BufferedTextReader(fs, path, buffer_size=buffer_size) as reader:
            assert list(reader) == ["this is", "a multiline", "text file"]

    def test_after_close_reading_returns_empty_bytes(self, fs, path):
        write_text(fs, path, "foo bar baz")
        reader = BufferedTextReader(fs, path, buffer_size=4)
        assert reader.read(128) == "foo "
        reader.close()
        assert reader.read(123) == ""

    def test_after_context_manager_exit_reading_returns_empty_bytes(self, fs, path):
        write_text(fs, path, "foo bar baz")
        with BufferedTextReader(fs, path, buffer_size=4) as reader:
            assert reader.read(128) == "foo "
            reader.close()
            assert reader.read(123) == ""
