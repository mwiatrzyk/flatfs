Quickstart
==========

Installation
------------

The project is available on PyPI and can be installed with any Python
dependency management tool.

Installing with **pip**::

    $ pip install flatfs

Installing with **poetry**::

    $ poetry add flatfs

Installation using other tools is similar.

Examples
--------

Basic usage
^^^^^^^^^^^

Let's create a flat filesystem using in-memory backend. It has exactly the same
API as the one used for real files (see :class:`flatfs.backends.LocalFlatFs`
class documentation) but creates files in memory rather than on the disk:

.. testcode::

    from flatfs.api import InMemoryFlatFs, write_text, read_text

    fs = InMemoryFlatFs()
    write_text(fs, "spam.txt", "content of spam.txt")
    write_text(fs, "foo/bar/baz.txt", "Hello World!")

We've created a filesystem with two files inside. The second file (``baz.txt``)
was created under a "subdirectory", which from **FlatFS** perspective is rather
a namespace than a real subdirectory.

.. note::

    If :class:`flats.backends.LocalFlatFs` was used instead, a real
    subdirectory would have been created, but this is implementation detail
    which is irrelevant from the **FlatFS** interface point of view.

Now, let's do some basic operations on just created filesystem:

1. Reading:

    .. doctest::

        >>> read_text(fs, "foo/bar/baz.txt")
        'Hello World!'

2. Listing files:

    .. doctest::

        >>> list(fs.scan())
        ['/spam.txt', '/foo/bar/baz.txt']

    .. note::

        The paths (or keys) were normalized; **FlatFS** only uses absolute
        paths that have leading slash (``/``) added after normalization. For
        reading/writing this leading slash is optional and is added
        automatically (unless provided explicitly).

3. Checking if file exists:

    .. doctest::

        >>> fs.exists("/spam.txt")
        True

4. Reading file stats:

    .. doctest::

        >>> stat = fs.stat("/spam.txt")
        >>> stat.size
        19

5. Overwriting files:

    .. doctest::

        >>> from flatfs.api import write_bytes, read_bytes
        >>> write_bytes(fs, "/spam.txt", b"\x00\x01\x02\x03")  # overwrite with binary file
        4
        >>> read_bytes(fs, "/spam.txt")
        b'\x00\x01\x02\x03'

6. Deleting files:

    .. doctest::

        >>> fs.remove("/spam.txt")
        >>> fs.exists("/spam.txt")
        False
        >>> list(fs.scan())
        ['/foo/bar/baz.txt']

Large file support
^^^^^^^^^^^^^^^^^^

Core API of the **FlatFS** library is implemented using generators, so the
library is able to handle large files in memory efficient way. Since the core
backend API is rather low-level, a higher level helpers are provided for both
text and binary file reading and writing.

Let's now create a large (~16MiB) file using
:class:`flatfs.helpers.BufferedWriter` helper:

.. testcode::

    from flatfs.api import BufferedWriter

    with BufferedWriter(fs, "large.bin") as writer:
        for _ in range(1000000):
            writer.write(b"0123456789abcdef")

The buffered writer used above is using an internal buffer for efficient
writing; it keeps caching data until a buffer size is exceeded, then flushes it
in one step to the underlying file.

You can use :meth:`flatfs.interface.FlatFsReader.stat` method to get basic
stats of a file, like size or modification time:

.. doctest::

    >>> fs.stat("large.bin").size
    16000000

Now let's read from the file. Since it is large, previously used helpers are
not the best choice, as those would have to read entire file to the RAM.
Luckily, **FlatFS** provides a counterpart
:class:`flatfs.helpers.BufferedReader` helper that can be used to read the file
in small chunks:

.. doctest::

    >>> from flatfs.api import BufferedReader
    >>> reader = BufferedReader(fs, "large.bin")
    >>> reader.read(16)
    b'0123456789abcdef'
    >>> reader.close()

Using async API
^^^^^^^^^^^^^^^

**FlatFS** supports async API, currently in form of blocking API adapters, but
with separate interfaces.

Async API can be provided on top of existing filesystem object. To do that,
simply use :class:`flatfs.aio.backends.AsyncFlatFsAdapter` and create async
adapter for existing filesystem:

.. testcode::

    from flatfs.aio.api import AsyncFlatFsAdapter

    async_fs = AsyncFlatFsAdapter(fs)

And now we have an async bridge to our blocking filesystem created earlier.
This is how it can be used:

.. testcode::

    async def list_files() -> list[str]:
        return [path async for path in async_fs.scan()]

.. doctest::

    >>> import asyncio
    >>> asyncio.run(list_files())
    ['/foo/bar/baz.txt', '/large.bin']

The async API definitions can be found in :mod:`flatfs.aio.interface` and it is
basically a mirror of non-async one from :mod:`flatfs.interface`. This makes a
pretty straightforward conversions possible between those two when needed.

Async API also provides async helpers. See :mod:`flatfs.aio.helpers` for more
details.
