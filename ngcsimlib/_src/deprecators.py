from ngcsimlib._src.logger import warn


def deprecated(fn=None, *, replaced_by=None, custom_message=None):
    def decorator(_fn):
        def _wrapped(*args, **kwargs):
            message = "is deprecated" + ("" if custom_message is None
                                         else (". " + custom_message))

            if replaced_by:
                new_name = getattr(replaced_by, '__name__', str(replaced_by))
                message += f" (use {new_name} instead)"
            warn(_fn.__qualname__, message)
            return _fn(*args, **kwargs)
        _wrapped._is_deprecated = True
        _wrapped._original = fn 
        return _wrapped

    if fn is not None:
        return decorator(fn)

    return decorator


def deprecate_args(_rebind=True, **arg_list): ## argument deprecating decorator
    def _deprecate_args(fn):
        def _wrapped(*args, **kwargs):
            for kwarg in list(kwargs.keys()):
                if kwarg in arg_list.keys():
                    new_kwarg = arg_list[kwarg]
                    if new_kwarg is None:
                        warn(f"The argument \"{kwarg}\" is deprecated for {fn.__qualname__}, and will no longer be supported")
                    else:
                        warn(f"The argument \"{kwarg}\" is deprecated for {fn.__qualname__}, use \"{new_kwarg}\" instead")

                    if _rebind:
                        if new_kwarg is not None:
                            kwargs[new_kwarg] = kwargs[kwarg]
                        del kwargs[kwarg]

            return fn(*args, **kwargs)

        _wrapped._is_deprecated = True
        _wrapped._original = fn
        return _wrapped
    return _deprecate_args
