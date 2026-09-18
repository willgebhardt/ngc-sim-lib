from typing import Protocol, runtime_checkable, Optional

@runtime_checkable
class ContextObject(Protocol):
    name: str
    _type: Optional[str]
