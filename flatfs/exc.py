from typing import Optional

from . import _export

__all__ = export = _export.Export()  # type: ignore


@export
class FlatFsError(Exception):
    """Base class for exceptions raised by this library."""

    #: Message template or ``None`` to use default ``__str__`` implementation.
    __message_template__: Optional[str] = None

    def __str__(self) -> str:
        if self.__message_template__ is None:
            return super().__str__()
        return self.__message_template__.format(self=self)


@export
class PathError(FlatFsError):
    """Base class for path-related errors."""

    __message_template__ = "{self.path}"

    #: Path that caused error.
    path: str

    def __init__(self, path: str):
        super().__init__()
        self.path = path


@export
class PathNotFoundError(PathError):
    """Raised when file was not found."""


@export
class PathAccessError(PathError):
    """Raised when file that is tried to be accessed lays beyond filesystem bounds."""
