import json
from typing import List, Dict, Union, TypeAlias
from .context_manager import global_context_manager as gcm
from ngcsimlib.logger import warn
from ngcsimlib._src.utils.io import make_unique_path, make_safe_filename
from ngcsimlib._src.utils.priority import priority
from ngcsimlib._src.modules.modules_manager import modules_manager as modManager
from ngcsimlib._src.operations.BaseOp import BaseOp
from ngcsimlib._src.global_state.manager import global_state_manager, \
    DeferredConnection
from ngcsimlib._src.context.contextAwareObject import ContextAwareObject
from ngcsimlib._src.deprecators import deprecated

from ngcsimlib._src.typing import ContextObject, context, FilterResultFormat, FilterResult, ContextObjectGroups

import os, shutil

from ngcsimlib._src.compartment.compartment import Compartment


class _ObjectFilter:
    def __init__(self, sourceContext: "Context",
                 fallbackFormat: FilterResultFormat = FilterResultFormat.LIST):
        self.sourceContext = sourceContext
        self.fallbackFormat = fallbackFormat

    def __format(self, values: Dict[str, ContextObject | None],
                 resultFormat: FilterResultFormat,
                 requested_order: List[str] | None = None) -> FilterResult:
        match resultFormat:
            case FilterResultFormat.DICT:
                return values
            case FilterResultFormat.LIST:
                if requested_order is None:
                    return list(values.values())
                return [values.get(key, None) for key in requested_order]
            case FilterResultFormat.SINGLE:
                if len(values) == 1:
                    return next(iter(values.values()))
                return self.__format(values, self.fallbackFormat, requested_order)
            case _:
                return self.__format(values, self.fallbackFormat, requested_order)

    def by_group(self, obj_group: ContextObjectGroups | str,
                 resultFormat: FilterResultFormat = FilterResultFormat.DICT) -> FilterResult:
        """
        Filters the source context's registered objects by the provided group.
        :param obj_group: The group to filter by
        :param resultFormat: The format the output will try to match
        :return: All objects matching the provided group
        """
        found = {}
        for obj_name, obj in self.sourceContext.objects.items():
            _group = getattr(obj, "_group", ContextObjectGroups.unknown)
            if _group == obj_group:
                found[obj_name] = obj

        return self.__format(found, resultFormat)

    def by_name(self, *names: str,
                resultFormat: FilterResultFormat = FilterResultFormat.SINGLE) -> FilterResult:
        """
        Filters the source context's registered objects by the provided names.
        :param names: the names to filter by
        :param resultFormat: The format the output will try to match
        :return: All objects matching the provided names
        """
        found = {}
        for name in names:
            for obj_name, obj in self.sourceContext.objects.items():
                if obj_name == name:
                    found[name] = obj
                    break
            if name not in found:
                found[name] = None

        return self.__format(found, resultFormat, requested_order=list(names))

    def all(self, resultFormat: FilterResultFormat = FilterResultFormat.DICT) -> FilterResult:
        """
        Flattens and returns all objects
        :param resultFormat: The format the output will try to match
        :return: All objects
        """
        return self.__format(self.sourceContext.objects, resultFormat)


@context
@priority(10)
class Context(ContextAwareObject):
    """
    The context object is the container that holds all the information for a
    model. Each context will keep track of all the contextAwareObjects built
    inside of it, and handle some general use cases involving them, such as
    saving and loading. The general pattern is to use a python with block with
    the context to automatically capture each of the contextAwareObjects built
    in side the block. The context will also automatically compile all the
    objects in the correct order (based on compile priority) when leaving the
    with block. This means that in order to use any of the compiled methods or
    processes defined the with block must first be left.
    """

    @classmethod
    def _existing_instance(cls, name: str, *args, **kwargs):
        """
        Uses a metaclass hook to enforce a singleton structure per path
        """
        targetPath = gcm.append_path(addition=name)
        return gcm.get_context(targetPath) if gcm.exists(targetPath) else None

    def __new__(cls, name: str, *args, **kwargs):
        """ Needs to exist as the metaclass will call __enter__ before the
        init thus all path related attributes need to exist
        """
        instance = super().__new__(cls)
        instance.path = gcm.append_path(addition=name)
        instance.__previous_path = None
        return instance

    def __init__(self, name: str):
        super().__init__(name)
        self.objects: Dict[str, ContextObject] = {}
        self._connections: Dict[str, Union["Compartment", "BaseOp"]] = {}
        self.__filter = _ObjectFilter(self)
        gcm.register_context_local(self)


    @property
    def object_filter(self) -> _ObjectFilter:
        """
        Provides access to the context's regirstered objects via a filter
        :return: The interface for the object filter
        """
        return self.__filter

    @property
    def components(self) -> Dict[str, ContextObject]:
        """
        A helper to filter all registered ContextObject in the `component`
        group

        :return: A dict of {path, ContextObject}
        """
        return self.object_filter.by_group(ContextObjectGroups.component)

    @property
    def processes(self) -> Dict[str, ContextObject]:
        """
        A helper to filter all registered ContextObject in the `process`
        group

        :return: A dict of {path, ContextObject}
        """
        return self.object_filter.by_group(ContextObjectGroups.process)

    @property
    def contexts(self) -> Dict[str, ContextObject]:
        """
        A helper to filter all registered ContextObject in the `context` group

        :return: A dict of {path, ContextObject}
        """
        return self.object_filter.by_group(ContextObjectGroups.context)

    def __enter__(self):
        self.__previous_path = gcm.current_path
        gcm.step_to(self.path)
        return self

    def __exit__(self, exc_group, exc_val, exc_tb):
        print("Exiting", self.name)
        gcm.step_to(self.__previous_path)
        self.__previous_path = None
        self.compile()

    def compile(self) -> None:
        """
        Attempts to compile all ContextObjects registered with the context.
        Compiling order is controlled by each object's priority.
        All objects that do not have a priority are assigned the default
        priority of zero.

        As not every ContextObject is required to be compilable, ensure that
        the "is_compilable" attribute is set to True.
        """
        priorities = {}

        for obj in self.objects.values():
            if (getattr(obj, "_is_compilable", False) and
                hasattr(obj, "compile") and callable(obj.compile)):
                p = getattr(obj, "_priority", None) or 0
                if p not in priorities:
                    priorities[p] = []

                priorities[p].append(obj)
        keys = sorted(priorities.keys(), reverse=True)
        for key in keys:
            for obj in priorities[key]:
                obj.compile()

    def recompile(self) -> None:
        self.compile()

    def registerObj(self, obj: ContextObject) -> bool:
        """
        Registers an object in the context. Will accept any object that follows
        the required protocol. For complete registration '_group' is required,
        if it is missing only certain

        Args:
            obj: The object to register in the context

        Returns:
            boolean: marks if the object was successfully registered in the
                context
        """

        obj_name = getattr(obj, 'name')
        if obj_name is None:
            warn("Trying to register and object without a name."
                 f"Broken object: {obj}"
                 f"\nAborting registration!")
            return False

        if self.objects.get(obj_name) is not None:
            warn(f"An object with the name {obj_name} is already exists in this"
                 f"context. Broken object: {obj}"
                 f"\nAborting registration!")
            return False

        self.objects[obj_name] = obj
        _group = getattr(obj, "_group", None)
        if _group is None:
            warn(f"Partial registration of {obj_name}! During registration no "
                 f"\"_group\" flag was found. Object will be grouped as "
                 f"\"unknown\" while saving, and this object will not appear "
                 f"in group filters. To handle this flag automatically "
                 f"ngcsimlib provides both decorators and base classes as a "
                 f"convenience.")
        return True

    @deprecated(custom_message="Use Context.object_filter.by_group instead")
    def get_objects_by_type(self, objectGroup: ContextObjectGroups | str) -> \
    Dict[
        str, ContextObject]:
        """
        Gets the group of objects of the designated group tracked by this
        context.

        Args:
            objectGroup: The object group to extract from the context

        Returns: A dictionary of str:obj pairs where each key is the name of
            object. Will return an empty dictionary if the given group is not
            found in the context.

        """
        _group = objectGroup.value if isinstance(objectGroup,
                                                 ContextObjectGroups) else objectGroup
        return self.objects.get(_group, {})

    @deprecated(custom_message="Use Context.object_filter instead")
    def get_objects(self, *object_names: str,
                    objectGroup: ContextObjectGroups | str,
                    unwrap: bool = True) \
        -> Union[None, ContextObject, List[Union[ContextObject, None]]]:
        """
        Gets a specific group of objects by name and group tracked by this
        context.

        Args:
            *object_names: Any number of object names to extract from the
                context

            objectGroup: The object group shared by these objects.
            unwrap: In the event that there is a single object found should the
                method return a list of length one or a single value. Will also
                change it from returning an empty list if no names are provided
                to returning None.

        Returns: None or empty list if no names are provided based on if unwrap
            is set to true. Will return either a single object or a list of
            length one if only one name is provided based on unwrap. If multiple
            names are provided, the method will return a list of objects found
            in the context with "None"s where it could not find an object of the
            given name.

        """

        if len(object_names) == 0:
            return None if unwrap else []

        _all_objects = self.get_objects_by_type(objectGroup)
        _objs = []
        for component_name in object_names:
            _objs.append(_all_objects.get(component_name, None))

        for name, obj in zip(object_names, _objs):
            if obj is None:
                warn(
                    f"Could not find an {objectGroup} with the name \"{name}\" in the context")

        if len(_objs) == 1 and unwrap:
            return _objs[0]
        return _objs

    @deprecated(custom_message="Replaced with Context.components and "
                               "Context.object_filter.by_name")
    def get_components(self, *component_names: str, unwrap: bool = True) -> \
        Union[None, ContextObject, List[Union[ContextObject, None]]]:
        return self.get_objects(*component_names,
                                objectGroup=ContextObjectGroups.component,
                                unwrap=unwrap)

    def add_connection(self, source: Union["Compartment", "BaseOp"],
                       destination: "Compartment"):
        self._connections[destination.root] = source

    def save_to_json(self, directory: str, model_name: Union[str, None] = None,
                     custom_save: bool = True, overwrite: bool = False) -> None:
        """
        Saves the context to a collection fo JSON files.

        Args:
            directory: The directory to save the context to
            model_name: The model name to save the context to if none will use
                the context's name
            custom_save: Should this context call the custom save methods on
                each object in the context.
            overwrite: Should this context overwrite a previously saved context
                if no it will append a uuid to the end of the model to ensure it
                doesn't overwrite.
        """
        if model_name is None:
            model_name = self.name
        model_name = make_safe_filename(model_name)

        if overwrite and os.path.isdir(directory + "/" + model_name):
            for filename in os.listdir(directory + "/" + model_name):
                file_path = os.path.join(directory + "/" + model_name, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            shutil.rmtree(directory + "/" + model_name)

        path = make_unique_path(directory, model_name)

        contextMeta = {"groups": list(self.objects.keys()),
                       "path": self.path}

        with open(f"{path}/contextData.json", "w") as f:
            f.write(json.dumps(contextMeta, indent=4))

        for _group in self.objects.keys():
            group_path = f"{path}/{make_safe_filename(_group)}"
            os.mkdir(group_path)

            _objs = self.get_objects_by_type(_group)

            made_custom = False
            data = {}

            if ((isinstance(_group,
                            str) and _group in ContextObjectGroups.context.value) or
                (isinstance(_group,
                            ContextObjectGroups) and _group == ContextObjectGroups.context)):
                for _obj_name, obj in _objs.items():
                    if hasattr(obj, "save_to_json") and callable(
                        getattr(obj, "save_to_json")):
                        obj.save_to_json(group_path)
                        data[_obj_name] = {
                            "priority": getattr(obj, "_priority", 0)}
            else:
                for obj_name, obj in _objs.items():
                    objData = {}
                    if hasattr(obj, "to_json") and callable(
                        getattr(obj, "to_json")):
                        objData.update(obj.to_json())

                    objData["modulePath"] = modManager.resolve_public_import(
                        obj)

                    data[obj_name] = objData

                    if custom_save:
                        if hasattr(obj, "save") and callable(
                            getattr(obj, "save")):
                            if not made_custom:
                                os.mkdir(group_path + "/custom")
                                made_custom = True
                            obj.save(group_path + "/custom")

            with open(f"{group_path}/roots.json", "w") as fp:
                json.dump(data, fp, indent=4)

        connections = {}
        for connectionRoot, source in self._connections.items():
            if isinstance(source, Compartment):
                connections[connectionRoot] = source.target
            else:
                connections[connectionRoot] = source.to_json()

        with open(f"{path}/connections.json", "w") as fp:
            json.dump(connections, fp, indent=4)

    @classmethod
    def load(cls, directory: str, module_name: str) -> "Context":
        if gcm.exists(gcm.append_path(module_name)):
            warn("Trying to load a context that already exists, returning "
                 "existing context")
            return gcm.get_context(gcm.append_path(module_name))

        path = directory + "/" + module_name
        with open(f"{path}/contextData.json", "r") as f:
            metaData = json.load(f)

        with cls(metaData.get("path", module_name)) as ctx:
            delayed_load = []

            for _group in metaData["groups"]:

                group_path = f"{path}/{make_safe_filename(_group)}"
                with open(f"{group_path}/roots.json", "r") as fp:
                    groupRoots = json.load(fp)

                for obj_name, objData in groupRoots.items():
                    objKlass = modManager.import_module(objData["modulePath"])
                    args = objData["args"]
                    kwargs = objData["kwargs"]
                    newObj = objKlass(*args, **kwargs)
                    _priority = objData.get("priority",
                                            getattr(newObj, "_priority", 0))
                    delayed_load.append((
                        _priority, newObj,
                        objData, group_path))

            delayed_load = sorted(delayed_load, key=lambda x: x[0],
                                  reverse=True)
            for _, obj, data, group_path in delayed_load:
                if hasattr(obj, "from_json") and callable(
                    getattr(obj, "from_json")):
                    obj.from_json(data)

                if hasattr(obj, "load") and callable(getattr(obj, "load")):
                    obj.load(f"{group_path}/custom")

            with open(f"{path}/connections.json", "r") as fp:
                connectionData = json.load(fp)
                for connectionRoot, target in connectionData.items():
                    neededPaths = set()
                    neededPaths.add(connectionRoot)
                    if isinstance(target, str):
                        neededPaths.add(target)
                    else:
                        neededPaths.union(BaseOp.get_requirements(target))
                global_state_manager.add_promise(
                    DeferredConnection(connectionRoot, target, neededPaths))

        if not global_state_manager.resolve_deferred_connections():
            warn(f"At the end of loading {module_name} the global state is"
                 "incomplete. If this is not the top level context this"
                 "warning can be safely ignored.")
        return ctx

    @classmethod
    def computeIfAbsent(cls, name: str, path: str | None = None) -> "Context":
        """
        Extends and wraps the constructor for the context, while conforming to
        a more standard naming scheme. Computes if there is a context existing
        at the provided name and path. If path is none, it will use the current
        path. Returns the context at that path if it exists, else it will make a
        new context at the provided path, with the provided name. If path is not
        None this is method has a side effect of changing the path of the
        global context manager to be the provided path.

        (This is identical to the default __new__ if path=None)

        :param name: The name of the context to use or make
        :param path:  (default=None) The path to search for existing contexts
        in, default behavior is current path.
        :return: If one exists the context at the provided name and path, else
        a new context is made at that name and path, and is returned.
        """
        target_path = gcm.append_path(path, str)
        if gcm.exists(target_path):
            return gcm.get_context(target_path)
        gcm.step_to(path)
        return cls(name)
