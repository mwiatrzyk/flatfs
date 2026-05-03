from typing import TypeVar

T = TypeVar("T")


class Export(list):
    """Helper for creating ``__all__`` module properties."""

    def __call__(self, func_or_cls: T) -> T:
        name = getattr(func_or_cls, "__name__")
        self.append(name)
        return func_or_cls
