import inspect

from ngcsimlib.logger import error, warn
from .context_manager import global_context_manager as gcm
from collections.abc import Iterable


def extract_name(cls, args, kwargs):
    init = cls.__init__

    if getattr(init, "_is_deprecated", False):
        unwrapped = getattr(init, "_original", None)
        if unwrapped is None:
            error("Failed to find a non deprecated init method")
        init = unwrapped

    sig = inspect.signature(init)
    bound = sig.bind_partial(None, *args, **kwargs)
    bound.apply_defaults()

    if "name" in bound.arguments:
        return bound.arguments["name"]
    return None


class ContextAwareObjectMeta(type):
    def __new__(cls, name, bases, attrs):
        if '__enter__' not in attrs:
            def __enter__(self):
                gcm.step(self._inferred_name, catch_empty=False)

            attrs['__enter__'] = __enter__

        if '__exit__' not in attrs:
            def __exit__(self, type, value, traceback):
                gcm.step_back()

            attrs['__exit__'] = __exit__


        return super().__new__(cls, name, bases, attrs)

    """
    This is the metaclass for objects that want to interact with the context
    they were created in. Generally use the base class "ContextAwareObject" over
    this metaclass.
    """
    def __call__(cls, *args, **kwargs):
        obj = cls.__new__(cls, *args, **kwargs)
        obj._inferred_name = extract_name(cls, args, kwargs)

        with obj:
            cls.__init__(obj, *args, **kwargs)

            obj._args = args
            obj._kwargs = kwargs

            if not hasattr(obj, 'name'):
                error(f"Created context objects must have a name. "
                      f"Error occurred when making an object of class {cls.__name__}")

            if hasattr(obj, "compartments") and isinstance(obj.compartments, Iterable) and not isinstance(obj.compartments, (str, bytes)):
                for (comp_name, comp) in obj.compartments:
                    if hasattr(comp, "_setup") and callable(comp._setup):
                        comp._setup(comp_name, gcm.current_path)

        contextRef = gcm.current_context
        if contextRef is not None:
            contextRef.registerObj(obj)
        return obj
