from multiprocessing import Pool
from typing import Any, List, Optional, Tuple, Union

from .solver import Solver, _get_backend
from .array import BoolArray2D, IntArray2D
from .expr import BoolExpr, BoolVar, IntVar
from .constraints import flatten_iterator


class Analyzer(Solver):
    answer_key_name: List[Optional[str]]
    axiom_constraints: List[int]
    optional_constraints: List[Tuple[str, List[int]]]

    def __init__(self):
        super(Analyzer, self).__init__()
        self.answer_key_name = []
        self.axiom_constraints = []
        self.optional_constraints = []

    def bool_var(self) -> BoolVar:
        self.answer_key_name.append(None)
        return super(Analyzer, self).bool_var()

    def int_var(self, lo, hi) -> IntVar:
        self.answer_key_name.append(None)
        return super(Analyzer, self).int_var(lo, hi)

    def add_answer_key(self, *variable: Any, name: Optional[str] = None):
        if len(variable) == 0:
            return
        elif len(variable) == 1:
            var = variable[0]
            if isinstance(var, (BoolVar, IntVar)):
                self.answer_key_name[var.id] = name
                super(Analyzer, self).add_answer_key(var)
                return

            if isinstance(var, (BoolArray2D, IntArray2D)):
                height, width = var.shape
                for y in range(height):
                    for x in range(width):
                        if name is None:
                            new_name = None
                        else:
                            new_name = name + "." + str(y) + "." + str(x)
                        self.add_answer_key(var[y, x], name=new_name)
            else:
                for i, elem in enumerate(var):
                    if name is None:
                        new_name = None
                    else:
                        new_name = name + "." + str(i)
                    self.add_answer_key(elem, name=new_name)
        else:
            for i, elem in enumerate(variable):
                if name is None:
                    new_name = None
                else:
                    new_name = name + "." + str(i)
                self.add_answer_key(elem, name=new_name)

    def ensure(self, *constraint: Any, name: Optional[str] = None):
        flat_constraints = []
        for x in flatten_iterator(constraint):
            if isinstance(x, (BoolExpr, bool)):
                flat_constraints.append(x)
            else:
                raise TypeError("each element in 'constraint' must be BoolExpr-like")
        new_ids = list(range(len(self.constraints), len(self.constraints) + len(flat_constraints)))
        if name is None:
            self.axiom_constraints += new_ids
        else:
            self.optional_constraints.append((name, new_ids))
        self.constraints += flat_constraints

    def _test_unlearnt_fact(self, i, unlearnt_facts, learnt_facts, backend):
        backend_type = _get_backend(backend)
        is_active_constraint = [True for _ in range(len(self.optional_constraints))]
        is_active_fact = [True for _ in range(len(learnt_facts))]

        def check():
            csp_solver = backend_type(self.variables)
            csp_solver.add_constraint([self.constraints[j] for j in self.axiom_constraints])
            for k in range(len(self.optional_constraints)):
                if is_active_constraint[k]:
                    _, cs = self.optional_constraints[k]
                    csp_solver.add_constraint([self.constraints[j] for j in cs])
            for k in range(len(learnt_facts)):
                if is_active_fact[k]:
                    vi, val = learnt_facts[k]
                    csp_solver.add_constraint(self.variables[vi] == val)
            vi, val = unlearnt_facts[i]
            csp_solver.add_constraint(self.variables[vi] != val)
            return not csp_solver.solve()

        for j in range(len(is_active_constraint)):
            is_active_constraint[j] = False
            if not check():
                is_active_constraint[j] = True

        for j in range(len(is_active_fact)):
            is_active_fact[j] = False
            if not check():
                is_active_fact[j] = True

        active_constraint_ids = [
            i for i in range(len(is_active_constraint)) if is_active_constraint[i]
        ]
        active_fact_ids = [i for i in range(len(is_active_fact)) if is_active_fact[i]]
        score = len(active_constraint_ids) + len(active_fact_ids)
        return score, active_constraint_ids, active_fact_ids

    def analyze(self, n_workers: int = 0, backend: Union[None, str, type] = None):
        backend_type = _get_backend(backend)
        csp_solver = backend_type(self.variables)
        csp_solver.add_constraint(self.constraints)

        if not csp_solver.solve_irrefutably(self.is_answer_key):
            return None

        unlearnt_facts = []
        for i, v in enumerate(self.variables):
            if self.is_answer_key[i] and self.variables[i].sol is not None:
                unlearnt_facts.append((i, self.variables[i].sol))
        learnt_facts: List[Tuple[int, Union[bool, int]]] = []

        res = []
        while len(unlearnt_facts) > 0:
            if n_workers >= 0:
                with Pool(None if n_workers == 0 else n_workers) as pool:
                    args = [
                        (i, unlearnt_facts, learnt_facts, backend)
                        for i in range(len(unlearnt_facts))
                    ]
                    cand_all = pool.starmap(self._test_unlearnt_fact, args)
            else:
                cand_all = [
                    self._test_unlearnt_fact(i, unlearnt_facts, learnt_facts, backend)
                    for i in range(len(unlearnt_facts))
                ]

            best_cand = min(cand_all)

            _, active_constraint_ids, active_fact_ids = best_cand
            csp_solver = backend_type(self.variables)
            csp_solver.add_constraint([self.constraints[i] for i in self.axiom_constraints])
            for k in active_constraint_ids:
                _, cs = self.optional_constraints[k]
                csp_solver.add_constraint([self.constraints[j] for j in cs])
            for k in active_fact_ids:
                vi, val = learnt_facts[k]
                csp_solver.add_constraint(self.variables[vi] == val)

            assert csp_solver.solve_irrefutably(self.is_answer_key)

            new_learnt_facts = []
            new_unlearnt_facts = []
            for vi, val in unlearnt_facts:
                if self.variables[vi].sol is not None:
                    assert self.variables[vi].sol is val
                    new_learnt_facts.append((vi, val))
                else:
                    new_unlearnt_facts.append((vi, val))

            res.append(
                (
                    [(self.answer_key_name[i], val) for i, val in new_learnt_facts],
                    [self.optional_constraints[i][0] for i in best_cand[1]],
                    [self.answer_key_name[learnt_facts[i][0]] for i in best_cand[2]],
                )
            )
            print(
                (
                    [(self.answer_key_name[i], val) for i, val in new_learnt_facts],
                    [self.optional_constraints[i][0] for i in best_cand[1]],
                    [self.answer_key_name[learnt_facts[i][0]] for i in best_cand[2]],
                )
            )
            learnt_facts += new_learnt_facts  # type: ignore
            unlearnt_facts = new_unlearnt_facts

        return res
