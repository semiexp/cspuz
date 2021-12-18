import importlib

from .backend import Backend
from ..expr import Op, Expr, BoolVar, IntVar

z3 = None


def _convert_expr(e, variables_dict):
    if isinstance(e, (bool, int)):
        return e
    if not isinstance(e, Expr):
        raise TypeError()
    if isinstance(e, (BoolVar, IntVar)):
        return variables_dict[e.id]
    else:
        operands = list(map(lambda x: _convert_expr(x, variables_dict), e.operands))
        if e.op == Op.NEG:
            return -operands[0]
        elif e.op == Op.ADD:
            ret = operands[0]
            for i in range(1, len(operands)):
                ret = ret + operands[i]
            return ret
        elif e.op == Op.SUB:
            ret = operands[0]
            for i in range(1, len(operands)):
                ret = ret - operands[i]
            return ret
        elif e.op == Op.EQ:
            return operands[0] == operands[1]
        elif e.op == Op.NE:
            return operands[0] != operands[1]
        elif e.op == Op.LE:
            return operands[0] <= operands[1]
        elif e.op == Op.LT:
            return operands[0] < operands[1]
        elif e.op == Op.GE:
            return operands[0] >= operands[1]
        elif e.op == Op.GT:
            return operands[0] > operands[1]
        elif e.op == Op.NOT:
            return z3.Not(operands[0])
        elif e.op == Op.AND:
            return z3.And(operands)
        elif e.op == Op.OR:
            return z3.Or(operands)
        elif e.op == Op.XOR:
            return z3.Xor(operands[0], operands[1])
        elif e.op == Op.IFF:
            return operands[0] == operands[1]
        elif e.op == Op.IMP:
            return z3.Or(z3.Not(operands[0]), operands[1])
        elif e.op == Op.IF:
            return z3.If(operands[0], operands[1], operands[2])
        elif e.op == Op.ALLDIFF:
            return z3.Distinct(operands)


class Z3Backend(Backend):
    def __init__(self, variables):
        global z3
        if z3 is None:
            z3 = importlib.import_module("z3")

        self.variables = variables
        self.variables_dict = dict()
        id_last = 0
        for v in variables:
            if isinstance(v, BoolVar):
                self.variables_dict[v.id] = z3.Bool("b" + str(id_last))
            elif isinstance(v, IntVar):
                self.variables_dict[v.id] = z3.Int("i" + str(id_last))
            id_last += 1
        self.converted_constraints = []

    def add_constraint(self, constraint):
        if isinstance(constraint, list):
            self.converted_constraints += map(
                lambda e: _convert_expr(e, self.variables_dict), constraint
            )
        else:
            self.converted_constraints.append(_convert_expr(constraint, self.variables_dict))

    def solve(self):
        solver = z3.Solver()
        for var in self.variables:
            if isinstance(var, IntVar):
                var_z3 = self.variables_dict[var.id]
                solver.add(var.lo <= var_z3, var_z3 <= var.hi)
        solver.add(self.converted_constraints)

        if solver.check() == z3.unsat:
            return False

        model = solver.model()
        for var in self.variables:
            var_z3 = self.variables_dict[var.id]
            if isinstance(var, BoolVar):
                var.sol = z3.is_true(model[var_z3])
            elif isinstance(var, IntVar):
                var.sol = model[var_z3].as_long()
        return True
