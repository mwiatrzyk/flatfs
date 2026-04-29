from flatfs.exc import PathAccessError


def normalize_path(path: str) -> str:
    """Normalizes path by removing duplicated slash characters and by
    evaluating relative path components (e.g. ``../`` or ``./``).

    Returns normalized path, or raises :exc:`flatfs.exc.FileAccessError` if
    final path would go beyond filesystem bounds.

    :param path:
        The path to normalize.
    """
    parts = []
    for part in path.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            if not parts:
                raise PathAccessError(path)
            parts.pop()
        else:
            parts.append(part)
    out = "/".join(parts)
    if out[0] == "/":
        return out
    return "/" + out
