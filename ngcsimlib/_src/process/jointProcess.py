import ast

from ngcsimlib._src.process.baseProcess import BaseProcess
from ngcsimlib._src.parser.utils import CompiledMethod
from ngcsimlib._src.context.context_manager import global_context_manager
from ngcsimlib._src.global_state.manager import global_state_manager
from ngcsimlib._src.context.context import ContextObjectTypes
from ngcsimlib._src.logger import error

from typing import List

class JointProcess(BaseProcess):
    def __init__(self, name):
        super().__init__(name)
        self.process_order: List[BaseProcess] = []

    def then(self, process: BaseProcess):
        if process._priority <= self._priority:
            self._priority = process._priority - 1

        self.process_order.append(process)
        return self

    def __rshift__(self, other):
        return self.then(other)

    def _parse(self):
        bodies = []
        extras = {}
        key_set = set()
        joint_watch_list = []
        namespace = {}

        for process in self.process_order:
            m: CompiledMethod = process.run.compiled
            obj_ast = m.ast
            if not isinstance(obj_ast, ast.Module):
                continue

            key_set.update(process.get_keywords())

            if len(process.get_keywords()) == 0:
                start = 0
            else:
                start = 1

            body = obj_ast.body[0].body[start:-1]
            bodies.extend(body)

            extras.update(m.auxiliary_ast)

            namespace.update(m.namespace)

            joint_watch_list.extend(process._watch_list)


        joint_watch_list.extend(self._watch_list)
        self._watch_list = joint_watch_list


        return bodies, extras, list(key_set), namespace

    def to_json(self):
        data = super().to_json()
        data.update({
                "process_order": [{
                    "name": p.name,
                    "path": global_context_manager.trim_last(p.context_path)
                } for p in self.process_order],
                "watch_list": [compartment.root for compartment in self._watch_list]
            })
        return data

    def from_json(self, data):
        process_order = data.get("process_order", [])
        for process in process_order:
            process_context = global_context_manager.get_context(process["path"])
            if process_context is None:
                error(f"Failed to find a context at {process['path']} while"
                      f"loading joint process {self.name}")

            # procs = ctx.get_objects(*process_order, objectType=ContextObjectTypes.process)
        # for proc in procs:
        #     if proc is not None and isinstance(proc, BaseProcess):
        #         self.then(proc)

        watch_list = data.get("watch_list", [])
        for compartment_root in watch_list:
            self.watch(global_state_manager.get_compartment(compartment_root))