import pytest

from flatfs.backends import InMemoryFlatFs
from flatfs.aio.backends import AsyncFlatFsAdapter
from flatfs.aio.interface import AsyncFlatFsReaderWriter


class TestAsyncFlatFsAdapter:
    @pytest.fixture
    def uut(self):
        return AsyncFlatFsAdapter(InMemoryFlatFs())

    @pytest.mark.parametrize(
        "path, expected_uri",
        [
            ("foo.txt", "mem:///foo.txt"),
            ("/bar/baz.txt", "mem:///bar/baz.txt"),
        ],
    )
    def test_uri(self, uut: AsyncFlatFsReaderWriter, path: str, expected_uri: str):
        assert uut.uri(path) == expected_uri
