# FlatFS

Minimal filesystem abstraction with pluggable backends, treating paths as keys
and file contents as values.

## About

FlatFS provides minimalistic protocol-based API for accessing files. The API
allows you to:

* create files using generator of binary chunks as source of data
* read files in chunks
* checking if file exists
* removing file from the filesystem
* scanning filesystem to retrieve all the files that are available

The API from above is supplied with a rich set of helpers that can simplify
common actions, like writing/reading whole files in text or binary mode,
reading files line-by-line, reading exact amount of bytes etc.

FlatFS does not use directories; those are just used to organize paths (aka
keys) and some implementations may use real directories, and the other may not.

The library is implemented in a way allowing it to be used with large files
thanks to the generator-based core API.

## Installation

The project can be installed directly from PyPI:

```shell
$ pip install flatfs
```

You can alternatively use any of the existing Python package management tools
(e.g. Poetry or uv) to install the library directly to your project.

## Examples

Here are some practical examples of how this library can be used:

1. Access ``/tmp`` directory:

    ```python
    import pathlib

    from flatfs.api import LocalFlatFs, FlatFsReaderWriter, write_text, read_text

    def make_temp_fs() -> FlatFsReaderWriter:
        return LocalFlatFs(pathlib.Path("/tmp"))

    temp_fs = make_temp_fs()
    write_text(temp_fs, "/foo/bar.txt", "content of file")  # Creates text file at /tmp/foo/bar.txt
    content = read_text(temp_fs, "/foo/bar.txt")  # Read the content back
    ```

2. Create in-memory flat filesystem (this implementation can be used during testing):

    ```python
    from flatfs.api import InMemoryFlatFs

    fs = InMemoryFlatFs()
    fs.write_chunks("foo.txt", [b"spam"])
    paths = list(fs.scan())  # Will return: ["/foo.txt"]
    ```

3. Wrap flat filesystem created earlier with async interface:

    ```python
    from flatfs.api import AsyncFlatFsAdapter, async_read_text

    async_temp_fs = AsyncFlatFsAdapter(temp_fs)
    content = await async_read_text(async_temp_fs, "foo/bar.txt")  # Paths are normalized and leading / is automatically added
    print(content)  # Would print: content of file
    ```

## Rationale

During developing of various systems and tools that follow clean architecture
and layered design (business logic, use case interactors, data ports and
gateways etc.) I found myself writing similar tool as one of the port/gateway
pair over and over again. This library was created to have such toolkit a bit
more advanced, based on chunk generators and producers, backed up with
comprehensive set of helpers, just to avoid writing it again for the (N+1)th
time.

## Author

Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>

## License

This project is released under the terms of the MIT license.

See LICENSE.txt for more details.
