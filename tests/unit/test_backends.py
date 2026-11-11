import pathlib
from typing import Callable, Optional

import pytest

from flatfs import _utils
from flatfs.backends import InMemoryFlatFs, LocalFlatFs
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

    @pytest.mark.parametrize(
        "path, expected_uri_func",
        [
            ("foo.txt", lambda root_dir: f"file://{root_dir}/foo.txt"),
            ("/bar/foo.txt", lambda root_dir: f"file://{root_dir}/bar/foo.txt"),
        ],
    )
    def test_uri(self, uut: FlatFsReaderWriter, path: str, expected_uri_func: Callable, tmp_path: pathlib.Path):
        assert uut.uri(path) == expected_uri_func(tmp_path)

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
            (lambda x: list(x.write_chunks("/.git/config", _utils.split_into_chunks(b"payload", 3))), "/.git/*"),
            (lambda x: x.remove("/.git/config"), "/.git/*"),
        ],
    )
    def test_methods_requiring_path_fail_with_access_error_for_excluded_paths(self, uut: FlatFsReaderWriter, func):
        with pytest.raises(PathAccessError):
            func(uut)

    @pytest.mark.parametrize("path", ["/foo/bar/baz/spam/more/spam.txt"])
    def test_deleting_a_file_also_removes_intermediate_empty_directories_from_a_backend_filesystem(
        self, uut: FlatFsReaderWriter, tmp_path: pathlib.Path, path: str
    ):
        segments = path.lstrip("/").split("/")
        write_bytes(uut, path, b"dummy data")
        assert tmp_path.joinpath(*segments).exists()
        uut.remove(path)
        assert not tmp_path.joinpath(*segments).exists()
        for i in range(1, len(segments)):
            assert not tmp_path.joinpath(*segments[:-i]).exists()

    def test_deleting_a_file_does_not_remove_common_intermediate_directories(
        self, uut: FlatFsReaderWriter, tmp_path: pathlib.Path
    ):
        write_bytes(uut, "/foo/bar/baz.txt", b"baz")
        write_bytes(uut, "/foo/bar/spam/more/spam.txt", b"spam")
        uut.remove("/foo/bar/spam/more/spam.txt")
        assert uut.exists("/foo/bar/baz.txt")
        assert not uut.exists("/foo/bar/spam/more/spam.txt")
        assert not tmp_path.joinpath("foo/bar/spam/more").exists()
        assert not tmp_path.joinpath("foo/bar/spam").exists()
        assert tmp_path.joinpath("foo/bar").exists()

    def test_scan_yields_nothing_if_root_dir_does_not_exist_yet(self, tmp_path: pathlib.Path):
        uut = LocalFlatFs(tmp_path / "not" / "exists" / "yet")
        assert [x for x in uut.scan()] == []


class TestInMemoryFlatFs:
    @pytest.fixture
    def uut(self):
        return InMemoryFlatFs()

    @pytest.mark.parametrize(
        "path, expected_uri",
        [
            ("foo.txt", "mem:///foo.txt"),
            ("/bar/foo.txt", "mem:///bar/foo.txt"),
        ],
    )
    def test_uri(self, uut: FlatFsReaderWriter, path: str, expected_uri: str):
        assert uut.uri(path) == expected_uri
