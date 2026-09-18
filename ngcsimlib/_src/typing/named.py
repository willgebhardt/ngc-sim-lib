from typing import Protocol, runtime_checkable


@runtime_checkable
class Named(Protocol):
    name: str
