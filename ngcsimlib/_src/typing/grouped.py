from typing import Protocol, Optional, runtime_checkable, Union
from .contextObjectGroups import ContextObjectGroups


@runtime_checkable
class Grouped(Protocol):
    """Optional flag. Non-flagged objects will be grouped into "Unknown" """
    _group: Optional[str]


def group(value: Union[ContextObjectGroups, str]):
    def decorator(cls):
        print("Decorating", cls, "with", value)
        cls._group = value
        return cls
    return decorator


component = group(ContextObjectGroups.component)
process = group(ContextObjectGroups.process)
context = group(ContextObjectGroups.context)
