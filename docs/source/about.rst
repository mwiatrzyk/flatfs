About
=====

What is FlatFS?
---------------

**FlatFS** is a minimalistic protocol-based key-value filesystem abstraction
layer for Python. This library allows you to:

* create files using generator of binary chunks as source of data,
* read files in chunks,
* checking if file exists,
* remove file from the filesystem,
* scan filesystem to get all available file paths.

The API from above is supplied with a rich set of helpers that can simplify
common actions, like writing/reading whole files in text or binary mode,
reading files line-by-line, reading exact amount of bytes etc.

**FlatFS** does not use directories; those are just used to organize paths (aka
keys) and some implementations may use real directories, and the other may not.

The library is implemented in a way allowing it to be used with large files
thanks to the generator-based core API. It also provides an async layer (via
:mod:`flatfs.aio` module) that will make it usable for :mod:`asyncio`
applications.

Rationale
---------

During developing of various systems and tools that follow clean architecture
and layered design (business logic, use case interactors, data ports and
gateways etc.) I found myself writing similar tool as one of the port/gateway
pair over and over again. This library was created to have such toolkit a bit
more advanced, based on chunk generators and producers, backed up with
comprehensive set of helpers, just to avoid writing it again for the (N+1)th
time.

Author
------

Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>

License
-------

This project is released under the terms of the MIT license.

See `LICENSE.txt <https://github.com/mwiatrzyk/flatfs/blob/main/LICENSE.txt>`_ for more details.
