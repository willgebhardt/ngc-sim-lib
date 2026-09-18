from typing import Protocol, runtime_checkable, Any, Callable, Optional
from ngcsimlib._src.logger import error


@runtime_checkable
class CompilableObject(Protocol):
    """An object that compiles itself via .compile(). In the absence of
    the flag _is_compilable will always evaluate to false. However, all base
    classes have this flag set to true and a compile method stubbed out."""
    _is_compilable: Optional[bool]

    def compile(self) -> Any:
        ...


@runtime_checkable
class CompilableMethod(Protocol):
    """
    An instance method flagged for discovery by the compile step
    (_is_compilable=True). In the absence of the flag _is_compilable will always
    evaluate to false. Only meaningful on methods of a CompilableClass —
    flagging a method on a non-compilable class has no effect.
    """
    _is_compilable: Optional[bool]
    __call__: Callable[..., Any]


def compilable(target):
    """
    If target is an instance method, flags it for inclusion in the compiling
    step

    If target is a class, flags all instances of that class for inclusion in the
    compiling step

    If target is an object, flags it for inclusion in the compiling step.
    Regardless of class's flag.
    """
    if isinstance(target, (staticmethod, classmethod)):
        error(f"Failed to flag {target.__func__.__qualname__} as compilable as",
              "it is a",
              f"{'static' if isinstance(target, staticmethod) else 'class'}",
              "method, which are not supported.", errorCls=TypeError)
    target._is_compilable = True
    return target


def not_compilable(target):
    """
    If target is an instance method, flags it for exclusion in the compiling
    step

    If target is a class, flags all instances of that class for exclusion in the
    compiling step

    If target is an object, flags it for exclusion in the compiling step.
    Regardless of class's flag.
    """
    target._is_compilable = False
    return target

