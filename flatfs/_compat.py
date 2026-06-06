from typing import Any, Coroutine, Generic, Optional, Protocol, TypeVar

T = TypeVar("T")
Tco = TypeVar("Tco", covariant=True)


class SupportsAnext(Protocol, Generic[Tco]):
    def __anext__(self) -> Coroutine[Any, Any, Tco]: ...


async def anext(obj: SupportsAnext[T], default: Optional[T] = None) -> T:
    try:
        return await obj.__anext__()
    except StopAsyncIteration:
        if default is not None:
            return default
        raise
