import pytest

from flatfs._utils import async_split_into_chunks, normalize_path, split_into_chunks
from flatfs.exc import PathAccessError


@pytest.mark.parametrize(
    "path, expected_output",
    [
        ("/foo.txt", "/foo.txt"),
        ("foo.txt", "/foo.txt"),  # leading slash is implicitly added
        ("///foo///bar.txt", "/foo/bar.txt"),  # multiple slashes are replaced with one
        ("/spam/./foo.txt", "/spam/foo.txt"),  # paths relative to current are ignored
        ("/spam/./././foo.txt", "/spam/foo.txt"),  # several paths relative to current are ignored
        ("/spam/../foo.txt", "/foo.txt"),  # using .. in paths
        ("/spam/bar/../foo.txt", "/spam/foo.txt"),  # using .. in paths
        ("/spam/bar/../../foo.txt", "/foo.txt"),  # using .. in paths
    ],
)
def test_normalize_path(path: str, expected_output: str):
    assert normalize_path(path) == expected_output


@pytest.mark.parametrize(
    "path",
    [
        "../foo.txt",
        "/spam/../../foo.txt",
    ],
)
def test_normalize_raises_access_error_if_resulting_path_goes_outside_of_filesystem_bounds(path: str):
    with pytest.raises(PathAccessError) as excinfo:
        normalize_path(path)
    assert excinfo.value.path == path


@pytest.mark.parametrize(
    "data, chunk_size, expected_chunks",
    [
        (b"foo", 1, [b"f", b"o", b"o"]),
        (b"foo", 2, [b"fo", b"o"]),
        (b"foo", 3, [b"foo"]),
        (b"foo", 4, [b"foo"]),
    ],
)
def test_split_into_chunks(data: bytes, chunk_size: int, expected_chunks: list[bytes]):
    assert list(split_into_chunks(data, chunk_size)) == expected_chunks


@pytest.mark.parametrize(
    "data, chunk_size, expected_chunks",
    [
        (b"foo", 1, [b"f", b"o", b"o"]),
        (b"foo", 2, [b"fo", b"o"]),
        (b"foo", 3, [b"foo"]),
        (b"foo", 4, [b"foo"]),
    ],
)
async def test_async_split_into_chunks(data: bytes, chunk_size: int, expected_chunks: list[bytes]):
    assert [chunk async for chunk in async_split_into_chunks(data, chunk_size)] == expected_chunks
