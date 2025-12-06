import inspect
import ast, textwrap
from .contextTransformer import ContextTransformer
from .kwargsTransformer import KwargsTransformer
from ngcsimlib._src.context.contextAwareObjectMeta import ContextAwareObjectMeta


def compilable(fn):
    """
    A decorator that can be used to mark methods and class as compilable. The
    priority is used to order which methods are compiled first. The higher the
    priority the earlier the method will be compiled. (-1 is generally used by
    processes as they need to go after everything else)
    """
    fn._is_compilable = True
    return fn


class CompiledMethod:
    def __init__(self, fn, fn_ast, auxiliary_ast, namespace, extra_globals):
        self._fn = fn
        self._fn_ast = fn_ast
        self._auxiliary_ast = auxiliary_ast or {}
        self._namespace = namespace
        self._extra_globals = extra_globals


    @property
    def auxiliary_ast(self):
        return self._auxiliary_ast

    @property
    def ast(self):
        return self._fn_ast

    @property
    def extra_globals(self):
        return self._extra_globals

    @property
    def namespace(self):
        return self._namespace

    @property
    def code(self):
        blocks = [ast.unparse(aast) for _, aast in list(self._auxiliary_ast.items())[::-1]]
        blocks.append(ast.unparse(self._fn_ast))
        return "\n\n".join(blocks)

    def __call__(self, *args, **kwargs):
        return self._fn(*args, **kwargs)

def _bind(obj, method, ast_obj, namespace=None, auxiliary_ast=None, extra_globals=None):
    try:
        code = compile(ast_obj, filename=f"{method.__name__}_compiled", mode='exec')
    except Exception as e:
        raise e
    namespace = method.__globals__.copy() if namespace is None else namespace
    exec(code, namespace)

    transformed_func = namespace[ast_obj.body[0].name]

    compiled_method = CompiledMethod(
        fn=transformed_func,
        fn_ast=ast_obj,
        auxiliary_ast=auxiliary_ast,
        namespace=namespace,
        extra_globals=extra_globals
    )

    setattr(obj, method.__name__, _methodWrapper(method, compiled_method))


def convert_kwargs(tree: ast.FunctionDef):
    """
    Converts all instances of kwarg[KEY] in the tree to just KEY
    Args:
        tree: the tree to parse

    Returns: the updated tree
    """
    transformer = KwargsTransformer()
    transformed = transformer.visit(tree)
    ast.fix_missing_locations(transformed)
    return transformer.transformed_kwargs


def parse_method(obj, method):
    """
    Parses a method into a pure method that takes in just ctx and kwargs. The
    new method is found at method.compiled() and additional metadata can be
    found at method.compiled.DATA where data is one of the various pieces of
    metadata.

    Metadata:
        .code: for a human-readable version of the parsed method
        .ast: for the ast tree of the parsed method
        .namespace: for the namespace used for the method

    Args:
        obj: The object for which the method is being compiled (relevant when
            values need to be pulled from the global state)
        method: The method to compile
    """
    transformed, additional_modules, extra_globals = _sub_parse(obj, method)
    namespace = method.__globals__.copy()
    namespace.update(extra_globals)
    for method_name, module in additional_modules.items():
        code = compile(module, filename=f"{method_name}_compiled", mode='exec')
        exec(code, namespace)

    _bind(obj, method, transformed, namespace,
          additional_modules, extra_globals)


def _sub_parse(obj, method, sub=False):
    source = textwrap.dedent(inspect.getsource(method))
    tree = ast.parse(source)
    transformer = ContextTransformer(obj, method, subMethod=sub)
    transformed = transformer.visit(tree)
    ast.fix_missing_locations(transformed)

    extra_globals = transformer.needed_globals.copy()
    additional_modules = transformer.auxiliary_ast.copy()


    for bound_name, method_name in transformer.needed_methods.items():
        method, adm, g = _sub_parse(obj, getattr(obj, method_name), sub=True)
        additional_modules[bound_name] = method
        additional_modules.update(adm)
        extra_globals.update(g)

    return transformed, additional_modules, extra_globals


def compileObject(obj):
    """
    Compiles the given object parsing every method that is decorated with the
    @compilable() decorator

    Args:
        obj: The object to compile
    """

    deferred_compile = []
    for name in dir(obj):
        attr = getattr(obj, name)
        if isinstance(attr, _methodWrapper):
            attr = attr._method
        if hasattr(attr, "_is_compilable") and not inspect.isclass(attr):
            if isinstance(type(attr), ContextAwareObjectMeta):
                compileObject(attr)
            else:
                deferred_compile.append(attr)

    for attr in deferred_compile:
        parse_method(obj, attr)



class _methodWrapper:
    def __init__(self, bound_method, compiled):
        self._method = bound_method
        self.compiled = compiled

    def __call__(self, *args, **kwargs):
        return self._method(*args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self._method, attr)
