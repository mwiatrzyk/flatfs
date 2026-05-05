import pytest

from flatfs._utils import normalize_path
from flatfs.exc import PathAccessError


@pytest.mark.parametrize(
    "path, expected_output",
    [
        ("/foo.txt", "/foo.txt"),
        ("foo.txt", "/foo.txt"),  # leading slash is implicitly added
        ("///foo///bar.txt", "/foo/bar.txt"),  # multiple slashes are replaced with one
        ("/spam/./foo.txt", "/spam/foo.txt"),  # paths relative to current are ignored
        (
            "/spam/./././foo.txt",
            "/spam/foo.txt",
        ),  # several paths relative to current are ignored
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
def test_normalize_raises_access_error_if_resulting_path_goes_outside_of_filesystem_bounds(
    path: str,
):
    with pytest.raises(PathAccessError) as excinfo:
        normalize_path(path)
    assert excinfo.value.path == path
