from typing import Protocol, runtime_checkable
from .grouped import Grouped
from .named import Named
from .compilable import CompilableObject
from .priority import Prioritized

@runtime_checkable
class ContextObject(Named, Grouped, CompilableObject, Prioritized, Protocol):
    """
    The expected shape of any object registered in a Context. Every registered
    object should satisfy Named, Grouped, and CompilableObject.
    Individual optional fields (_group, _is_compilable, _priority) fall back to built in
    defaults if absent; however compile() has no such fallback and is
    expected to be implemented.

    All ngcsimlib base classes (component, process, and context) satisfy these
    requirements inherently. Their parent class ContextAwareObject contains the
    compile() method and generally should not be modified.
    """