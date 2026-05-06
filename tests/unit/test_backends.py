import pathlib
from typing import Optional

import pytest

from flatfs.backends import LocalFlatFs
from flatfs.exc import PathAccessError
from flatfs.helpers import write_bytes
from flatfs.interface import FlatFsReaderWriter


class TestLocalFlatFs:
    @pytest.fixture
    def exclude(self):
        return None

    @pytest.fixture
    def include(self):
        return None

    @pytest.fixture
    def uut(
        self,
        tmp_path: pathlib.Path,
        exclude: Optional[set[str]],
        include: Optional[set[str]],
    ):
        return LocalFlatFs(tmp_path, exclude=exclude, include=include)

    @pytest.fixture(
        params=[
            "foo.txt",
            "/bar.txt",
        ]
    )
    def path(self, request: pytest.FixtureRequest):
        return request.param

    def test_scan_returns_normalized_paths_to_existing_files(self, uut: FlatFsReaderWriter):
        write_bytes(uut, "foo.txt", b"content of foo.txt")
        write_bytes(uut, "spam/bar.txt", b"content of bar.txt")
        assert set(uut.scan()) == {"/foo.txt", "/spam/bar.txt"}

    def test_scan_returns_nothing_for_empty_filesystem(self, uut: FlatFsReaderWriter):
        assert list(uut.scan()) == []

    @pytest.mark.parametrize(
        "exclude",
        [
            {"/.git/*"},
        ],
    )
    def test_scan_does_not_include_excluded_paths(self, uut: FlatFsReaderWriter, tmp_path: pathlib.Path):
        tmp_fs = LocalFlatFs(tmp_path)
        write_bytes(tmp_fs, ".git/config", b"")
        write_bytes(tmp_fs, ".git/HEAD", b"")
        write_bytes(tmp_fs, "foo.txt", b"")
        write_bytes(tmp_fs, "spam/bar.txt", b"")
        assert set(uut.scan()) == {"/foo.txt", "/spam/bar.txt"}

    @pytest.mark.parametrize(
        "include",
        [
            {"/foo.txt", "/spam/*"},
        ],
    )
    def test_scan_does_only_include_included_paths(self, uut: FlatFsReaderWriter, tmp_path: pathlib.Path):
        tmp_fs = LocalFlatFs(tmp_path)
        write_bytes(tmp_fs, ".git/config", b"")
        write_bytes(tmp_fs, ".git/HEAD", b"")
        write_bytes(tmp_fs, "foo.txt", b"")
        write_bytes(tmp_fs, "spam/bar.txt", b"")
        assert set(uut.scan()) == {"/foo.txt", "/spam/bar.txt"}

    @pytest.mark.parametrize(
        "func, exclude",
        [
            (lambda x: x.exists("/.git/config"), "/.git/*"),
            (lambda x: list(x.read_chunks("/.git/config")), "/.git/*"),
            (lambda x: x.write_chunks("/.git/config", [b"spam"]), "/.git/*"),
            (lambda x: x.remove("/.git/config"), "/.git/*"),
        ],
    )
    def test_methods_requiring_path_fail_with_access_error_for_excluded_paths(self, uut: FlatFsReaderWriter, func):
        with pytest.raises(PathAccessError):
            func(uut)
