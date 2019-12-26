from cspuz import backend
from cspuz.constraints import BoolVar, IntVar


DEFAULT_BACKEND = backend.sugar


class Solver(object):
    def __init__(self):
        self.variables = []
        self.constraints = []

    def bool_var(self):
        v = BoolVar(len(self.variables))
        self.variables.append(v)
        return v

    def int_var(self, lo, hi):
        v = IntVar(len(self.variables), lo, hi)
        self.variables.append(v)
        return v

    def ensure(self, constraint):
        if isinstance(constraint, list):
            self.constraints += list
        else:
            self.constraints.append(constraint)

    def find_answer(self, backend=None):
        if backend is None:
            backend = DEFAULT_BACKEND
        csp_solver = backend.CSPSolver(self.variables)
        csp_solver.add_constraint(self.constraints)
        return csp_solver.solve()
