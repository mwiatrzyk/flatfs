import pathlib
from typing import Optional

import pytest

from flatfs.backends import LocalFlatFs
from flatfs.exc import PathAccessError
from flatfs.interface import FlatFsReaderWriter


class TestLocalFlatFs:

    @pytest.fixture
    def exclude(self):
        return None

    @pytest.fixture
    def include(self):
        return None

    @pytest.fixture
    def uut(self, tmp_path: pathlib.Path, exclude: Optional[set[str]], include: Optional[set[str]]):
        return LocalFlatFs(tmp_path, exclude=exclude, include=include)

    @pytest.fixture(
        params=[
            "foo.txt",
            "/bar.txt",
        ]
    )
    def path(self, request: pytest.FixtureRequest):
        return request.param

    @pytest.mark.parametrize("data", [b"dummy file content"])
    def test_write_file_and_read_it_back(self, uut: FlatFsReaderWriter, path: str, data: bytes):
        uut.write_bytes(path, data)
        assert uut.read_bytes(path) == data

    def test_write_file_and_read_it_back_in_chunks(self, uut: FlatFsReaderWriter, path: str):
        uut.write_bytes(path, b"foo bar baz spam")
        assert list(uut.read_chunks(path, 3)) == [b"foo", b" ba", b"r b", b"az ", b"spa", b"m"]

    def test_write_file_in_chunks_and_read_it_back(self, uut: FlatFsReaderWriter, path: str):
        uut.write_chunks(path, [b"foo ", b"bar ", b"baz"])
        assert uut.read_bytes(path) == b"foo bar baz"

    def test_check_file_existence(self, uut: FlatFsReaderWriter, path: str):
        assert uut.exists(path) is False
        uut.write_bytes(path, b"spam")
        assert uut.exists(path) is True

    def test_remove_existing_file(self, uut: FlatFsReaderWriter, path: str):
        uut.write_bytes(path, b"spam")
        assert uut.exists(path) is True
        uut.remove(path)
        assert uut.exists(path) is False

    def test_scan_returns_normalized_paths_to_existing_files(self, uut: FlatFsReaderWriter):
        uut.write_bytes("foo.txt", b"content of foo.txt")
        uut.write_bytes("spam/bar.txt", b"content of bar.txt")
        assert set(uut.scan()) == {"/foo.txt", "/spam/bar.txt"}

    def test_scan_returns_nothing_for_empty_filesystem(self, uut: FlatFsReaderWriter):
        assert list(uut.scan()) == []

    @pytest.mark.parametrize("exclude", [
        {"/.git/*"},
    ])
    def test_scan_does_not_include_excluded_paths(self, uut: FlatFsReaderWriter, tmp_path: pathlib.Path):
        tmp_fs = LocalFlatFs(tmp_path)
        tmp_fs.write_bytes(".git/config", b"")
        tmp_fs.write_bytes(".git/HEAD", b"")
        tmp_fs.write_bytes("foo.txt", b"")
        tmp_fs.write_bytes("spam/bar.txt", b"")
        assert set(uut.scan()) == {"/foo.txt", "/spam/bar.txt"}

    @pytest.mark.parametrize("include", [
        {"/foo.txt", "/spam/*"},
    ])
    def test_scan_does_only_include_included_paths(self, uut: FlatFsReaderWriter, tmp_path: pathlib.Path):
        tmp_fs = LocalFlatFs(tmp_path)
        tmp_fs.write_bytes(".git/config", b"")
        tmp_fs.write_bytes(".git/HEAD", b"")
        tmp_fs.write_bytes("foo.txt", b"")
        tmp_fs.write_bytes("spam/bar.txt", b"")
        assert set(uut.scan()) == {"/foo.txt", "/spam/bar.txt"}

    @pytest.mark.parametrize("func, exclude", [
        (lambda x: x.exists("/.git/config"), "/.git/*"),
        (lambda x: x.read_bytes("/.git/config"), "/.git/*"),
        (lambda x: list(x.read_chunks("/.git/config")), "/.git/*"),
        (lambda x: x.write_bytes("/.git/config", b"spam"), "/.git/*"),
        (lambda x: x.write_chunks("/.git/config", [b"spam"]), "/.git/*"),
        (lambda x: x.remove("/.git/config"), "/.git/*"),
    ])
    def test_methods_requiring_path_fail_with_access_error_for_excluded_paths(self, uut: FlatFsReaderWriter, func):
        with pytest.raises(PathAccessError):
            func(uut)
