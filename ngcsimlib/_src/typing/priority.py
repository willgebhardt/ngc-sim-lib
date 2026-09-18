from typing import Protocol, Optional, runtime_checkable

@runtime_checkable
class Prioritized(Protocol):
    """Optional flag. Non-flagged objects will have a priority of 0"""
    _priority: Optional[int]


def priority(value: int):
    def decorator(cls):
        cls._priority = value
        return cls
    return decorator
