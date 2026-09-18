from ngcsimlib._src.operations.BaseOp import BaseOp
import ast


class Negate(BaseOp):
    """
    The product operation. This operation takes in any number of compartments
    and multiplies them together before passing the value off to the destination
    compartment.
    """
    def __init__(self, *compartments):
        super().__init__(*compartments)
        self.astOp = ast.Invert()
        if len(compartments) != 1:
            raise ValueError("Only one value can be negated.")

    def _get_value(self):
        return self._comps[0].get()


    def _to_ast(self, node, ctx):
        comp = self._comps[0]
        op = ast.UnaryOp(op=self.astOp, expr=comp._to_ast(node, ctx))
        return op
