from enum import Enum

class ContextObjectTypes(Enum):
    """
    In order for context to compile each of the contextAwareObjects built inside
    of them they need to know what type of object it is. These values are
    expected to be found in the class's _type field. Using decorators found in
    contextObjectDecorators.py will automatically apply these to the classes
    """
    component = "component"
    process = "process"
    context = "context"