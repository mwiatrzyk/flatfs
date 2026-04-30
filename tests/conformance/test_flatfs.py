import pathlib
from typing import Callable

import pytest

from flatfs.backends import InMemoryFlatFs, LocalFlatFs
from flatfs.exc import PathNotFoundError
from flatfs.interface import FlatFsReaderWriter

UUT = FlatFsReaderWriter


@pytest.fixture(params=[
    lambda root_dir: LocalFlatFs(root_dir),
    lambda root_dir: InMemoryFlatFs(),
])
def uut_factory(request):
    return request.param


@pytest.fixture
def uut(uut_factory: Callable[[pathlib.Path], UUT], tmp_path: pathlib.Path):
    return uut_factory(tmp_path)


@pytest.fixture(params=[
    ("foo.txt", "/foo.txt"),
    ("/bar.txt", "/bar.txt"),
    ("/spam/baz/dummy.txt", "/spam/baz/dummy.txt"),
    ("/spam/baz/../dummy.txt", "/spam/dummy.txt"),
])
def path_normalized_path(request):
    return request.param


@pytest.fixture(params=[
    b"the dummy file content"
])
def data(request):
    return request.param


@pytest.fixture(params=[
    [b"the", b" dummy", b" file", b" content"]
])
def chunked_data(request):
    return request.param


@pytest.fixture
def path(path_normalized_path: tuple):
    return path_normalized_path[0]


@pytest.fixture
def normalized_path(path_normalized_path: tuple):
    return path_normalized_path[1]


def test_create_file_and_read_it_back(uut: UUT, path: str, data: bytes):
    uut.write_bytes(path, data)
    assert uut.read_bytes(path) == data


def test_create_file_and_read_it_back_in_chunks(uut: UUT, path: str, data: bytes):
    uut.write_bytes(path, data)
    chunks = list(uut.read_chunks(path, chunk_size=5))
    assert len(chunks) > 1
    assert b"".join(chunks) == data


def test_create_file_from_chunks_and_read_it_back(uut: UUT, path: str, chunked_data: list[bytes]):
    uut.write_chunks(path, chunked_data)
    assert uut.read_bytes(path) == b"".join(chunked_data)


def test_check_if_file_exists(uut: UUT, path: str, data: bytes):
    assert uut.exists(path) is False
    uut.write_bytes(path, data)
    assert uut.exists(path) is True


def test_removed_file_no_longer_exists(uut: UUT, path: str, data: bytes):
    assert uut.exists(path) is False
    uut.write_bytes(path, data)
    assert uut.exists(path) is True
    uut.remove(path)
    assert uut.exists(path) is False


def test_scan_returns_normalized_path_to_existing_file(uut: UUT, path: str, data: bytes, normalized_path: str):
    uut.write_bytes(path, data)
    assert list(uut.scan()) == [normalized_path]


def test_read_bytes_raises_path_not_found_if_files_does_not_exist(uut: UUT, path: str):
    with pytest.raises(PathNotFoundError) as excinfo:
        uut.read_bytes(path)
    assert excinfo.value.path == path


def test_read_chunks_raises_path_not_found_if_files_does_not_exist(uut: UUT, path: str):
    with pytest.raises(PathNotFoundError) as excinfo:
        _ = list(uut.read_chunks(path))
    assert excinfo.value.path == path


def test_remove_raises_path_not_found_if_files_does_not_exist(uut: UUT, path: str):
    with pytest.raises(PathNotFoundError) as excinfo:
        uut.remove(path)
    assert excinfo.value.path == path


def test_double_read_bytes_returns_same_data(uut: UUT, path: str, data: bytes):
    uut.write_bytes(path, data)
    assert uut.read_bytes(path) == data
    assert uut.read_bytes(path) == data


def test_double_read_chunks_returns_same_data(uut: UUT, path: str, data: bytes):
    uut.write_bytes(path, data)
    assert b"".join(uut.read_chunks(path)) == data
    assert b"".join(uut.read_chunks(path)) == data
