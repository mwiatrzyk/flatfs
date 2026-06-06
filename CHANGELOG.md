## 0.5.0 (2026-06-06)

### BREAKING CHANGES

- extract async layer into a separate `flatfs.aio` module

## 0.4.0 (2026-06-06)

### Feat

- add support for legacy Py39

## 0.3.0 (2026-05-12)

### BREAKING CHANGES

- refactor `(async_)read_chunks` and `(async_)write_chunks` methods to use generators in a more flexible way

### Feat

- add helpers for buffered stream-based reading and writing

## 0.2.0 (2026-05-09)

### Fix

- `FlatFsReaderWriter.stat()` raise `PathNotFoundError` if file does not exist at given path

### Feat

- add `BinaryReader` helper class for reading files in more feasible way

## 0.1.0 (2026-05-09)

### Feat

- add `(Async)FlatFsReader.stat()` method for getting basic file stats: modification time in UTC and file size

## 0.0.1 (2026-05-09)

Initial release.

