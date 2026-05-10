import pathlib
import time
from typing import Callable

import pytest

from flatfs import _utils
from flatfs.api import (
    InMemoryFlatFs,
    LocalFlatFs,
    PathNotFoundError,
    FlatFsReaderWriter,
    read_bytes,
    read_text,
    write_bytes,
    write_text,
)

UUT = FlatFsReaderWriter


@pytest.fixture(
    params=[
        lambda root_dir: LocalFlatFs(root_dir),
        lambda root_dir: InMemoryFlatFs(),
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


def test_write_chunks_yields_number_of_bytes_written_for_each_chunk(uut: UUT, path: str):

    def chunk_gen():
        yield b"foo"
        yield b"spam"
        yield b"more spam"

    assert list(uut.write_chunks(path, chunk_gen())) == [3, 4, 9]


def test_write_bytes_and_read_bytes_back(uut: UUT, path: str, data: bytes):
    write_bytes(uut, path, data)
    assert read_bytes(uut, path) == data


def test_write_bytes_and_read_stats_of_created_file(uut: UUT, path: str, data: bytes):
    current_utc = _utils.utcnow()
    write_bytes(uut, path, data)
    stat = uut.stat(path)
    assert stat.size == len(data)
    assert abs(stat.modified - current_utc).total_seconds() <= 1


def test_stats_change_when_file_is_overwritten(uut: UUT, path: str):
    initial_count = write_bytes(uut, path, b"initial content")
    initial_stat = uut.stat(path)
    assert initial_stat.size == initial_count
    time.sleep(0.025)  # Let's wait a bit...
    modified_count = write_bytes(uut, path, b"modified content")
    modified_stat = uut.stat(path)
    assert modified_stat.size == modified_count
    assert initial_stat != modified_stat


def test_write_text_file_and_read_it_back(uut: UUT, path: str):
    write_text(uut, path, "some text")
    assert read_text(uut, path) == "some text"


def test_write_bytes_and_read_them_back_in_chunks(uut: UUT, path: str, data: bytes):
    write_bytes(uut, path, data)
    chunks = list(uut.read_chunks(path, chunk_size=5))
    assert len(chunks) > 1
    assert b"".join(chunks) == data


def test_check_if_file_exists(uut: UUT, path: str, data: bytes):
    assert uut.exists(path) is False
    write_bytes(uut, path, data)
    assert uut.exists(path) is True


def test_removed_file_no_longer_exists(uut: UUT, path: str, data: bytes):
    assert uut.exists(path) is False
    write_bytes(uut, path, data)
    assert uut.exists(path) is True
    uut.remove(path)
    assert uut.exists(path) is False


def test_scan_returns_normalized_path_to_existing_file(uut: UUT, path: str, data: bytes, normalized_path: str):
    write_bytes(uut, path, data)
    assert list(uut.scan()) == [normalized_path]


def test_read_chunks_raises_path_not_found_if_files_does_not_exist(uut: UUT, path: str):
    with pytest.raises(PathNotFoundError) as excinfo:
        _ = list(uut.read_chunks(path))
    assert excinfo.value.path == path


def test_remove_raises_path_not_found_if_files_does_not_exist(uut: UUT, path: str):
    with pytest.raises(PathNotFoundError) as excinfo:
        uut.remove(path)
    assert excinfo.value.path == path


def test_double_read_chunks_returns_same_data(uut: UUT, path: str, data: bytes):
    write_bytes(uut, path, data)
    assert b"".join(uut.read_chunks(path)) == data
    assert b"".join(uut.read_chunks(path)) == data
