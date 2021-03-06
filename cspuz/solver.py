import cspuz
from cspuz import backend
from cspuz.constraints import BoolVar, IntVar, BoolVars, Array


def _get_default_backend():
    backend_name = cspuz.config.default_backend
    if backend_name == 'sugar':
        return backend.sugar
    elif backend_name == 'sugar_extended':
        return backend.sugar_extended
    elif backend_name == 'z3':
        return backend.z3
    else:
        raise ValueError('invalid default backend {}'.format(backend_name))


class Solver(object):
    def __init__(self):
        self.variables = []
        self.is_answer_key = []
        self.constraints = []

    def bool_var(self):
        v = BoolVar(len(self.variables))
        self.variables.append(v)
        self.is_answer_key.append(False)
        return v

    def int_var(self, lo, hi):
        v = IntVar(len(self.variables), lo, hi)
        self.variables.append(v)
        self.is_answer_key.append(False)
        return v

    def bool_array(self, shape):
        if isinstance(shape, int):
            size = shape
        elif len(shape) == 1:
            size, = shape
        else:
            h, w = shape
            size = h * w
        vars = [self.bool_var() for _ in range(size)]
        return Array(vars, shape=shape, dtype=bool)

    def int_array(self, shape, lo, hi):
        if isinstance(shape, int):
            size = shape
        elif len(shape) == 1:
            size, = shape
        else:
            h, w = shape
            size = h * w
        vars = [self.int_var(lo, hi) for _ in range(size)]
        return Array(vars, shape=shape, dtype=int)

    def ensure(self, constraint):
        if hasattr(constraint, '__iter__'):
            self.constraints += constraint
        else:
            self.constraints.append(constraint)

    def add_answer_key(self, variable):
        if hasattr(variable, '__iter__'):
            for v in variable:
                self.is_answer_key[v.id] = True
        else:
            self.is_answer_key[variable.id] = True

    def find_answer(self, backend=None):
        if backend is None:
            backend = _get_default_backend()
        csp_solver = backend.CSPSolver(self.variables)
        csp_solver.add_constraint(self.constraints)
        return csp_solver.solve()

    def solve(self, backend=None):
        if backend is None:
            backend = _get_default_backend()
        csp_solver = backend.CSPSolver(self.variables)
        csp_solver.add_constraint(self.constraints)

        if hasattr(csp_solver, 'solve_irrefutably'):
            return csp_solver.solve_irrefutably(self.is_answer_key)

        if not csp_solver.solve():
            # inconsistent problem
            return False

        n_var = len(self.variables)
        answer = [None] * n_var
        for i in range(n_var):
            if self.is_answer_key[i]:
                answer[i] = self.variables[i].sol

        while True:
            difference_cond = []
            for i in range(n_var):
                if self.is_answer_key[i] and answer[i] is not None:
                    difference_cond.append(self.variables[i] != answer[i])
            csp_solver.add_constraint(BoolVars(difference_cond).fold_or())
            if not csp_solver.solve():
                break

            for i in range(n_var):
                if self.is_answer_key[i] and answer[
                        i] is not None and answer[i] != self.variables[i].sol:
                    answer[i] = None

        for i in range(n_var):
            if self.is_answer_key[i]:
                self.variables[i].sol = answer[i]
        return True
