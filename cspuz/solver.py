import functools
import warnings
from typing import Any, List, Tuple, Union, cast, overload

from . import backend
from .array import BoolArray1D, BoolArray2D, IntArray1D, IntArray2D
from .configuration import config
from .expr import BoolExpr, BoolExprLike, BoolVar, IntVar, Op
from .constraints import flatten_iterator


def _get_backend_by_name(backend_name: str) -> type:
    if backend_name == "sugar":
        return backend.sugar_like.SugarBackend
    elif backend_name == "sugar_extended":
        return backend.sugar_like.SugarExtendedBackend
    elif backend_name == "z3":
        return backend.z3.Z3Backend
    elif backend_name == "csugar":
        return backend.sugar_like.CSugarBackend
    elif backend_name == "enigma_csp":
        return backend.sugar_like.EnigmaCSPBackend
    else:
        raise ValueError("invalid backend {}".format(backend_name))


def _get_default_backend() -> type:
    backend_name = config.default_backend
    return _get_backend_by_name(backend_name)


def _get_backend(backend: Union[None, str, type]) -> type:
    if backend is None:
        return _get_default_backend()
    elif isinstance(backend, str):
        return _get_backend_by_name(backend)
    else:
        return backend


class Solver(object):
    variables: List[Union[BoolVar, IntVar]]
    is_answer_key: List[bool]
    constraints: List[BoolExprLike]

    def __init__(self):
        self.variables = []
        self.is_answer_key = []
        self.constraints = []

    def bool_var(self) -> BoolVar:
        v = BoolVar(len(self.variables))
        self.variables.append(v)
        self.is_answer_key.append(False)
        return v

    def int_var(self, lo, hi) -> IntVar:
        v = IntVar(len(self.variables), lo, hi)
        self.variables.append(v)
        self.is_answer_key.append(False)
        return v

    @overload
    def bool_array(self, shape: Union[int, Tuple[int]]) -> BoolArray1D:
        ...

    @overload
    def bool_array(self, shape: Tuple[int, int]) -> BoolArray2D:
        ...

    def bool_array(
        self, shape: Union[int, Tuple[int], Tuple[int, int]]
    ) -> Union[BoolArray1D, BoolArray2D]:
        if isinstance(shape, int):
            shape = (shape,)
        size = functools.reduce(lambda x, y: x * y, shape, 1)
        vars = [self.bool_var() for _ in range(size)]

        if len(shape) == 1:
            return BoolArray1D(vars)
        else:
            return BoolArray2D(vars, cast(Tuple[int, int], shape))

    @overload
    def int_array(self, shape: Union[int, Tuple[int]], lo: int, hi: int) -> IntArray1D:
        ...

    @overload
    def int_array(self, shape: Tuple[int, int], lo: int, hi: int) -> IntArray2D:
        ...

    def int_array(
        self, shape: Union[int, Tuple[int], Tuple[int, int]], lo: int, hi: int
    ) -> Union[IntArray1D, IntArray2D]:
        if lo > hi:
            raise ValueError("'hi' must be at least 'lo'")

        if isinstance(shape, int):
            shape = (shape,)
        size = functools.reduce(lambda x, y: x * y, shape, 1)
        vars = [self.int_var(lo, hi) for _ in range(size)]

        if len(shape) == 1:
            return IntArray1D(vars)
        else:
            return IntArray2D(vars, cast(Tuple[int, int], shape))

    def ensure(self, *constraint: Any):
        for x in flatten_iterator(*constraint):
            if isinstance(x, (BoolExpr, bool)):
                self.constraints.append(x)
            else:
                raise TypeError("each element in 'constraint' must be BoolExpr-like")

    def add_answer_key(self, *variable: Any):
        for x in flatten_iterator(*variable):
            if isinstance(x, (BoolVar, IntVar)):
                if self.is_answer_key[x.id]:
                    raise ValueError(f"variable #{x.id} is already an answer key")
                self.is_answer_key[x.id] = True
            else:
                raise TypeError("each element in 'variable' must be BoolVar or IntVar")

    def find_answer(self, backend: Union[None, str, type] = None) -> bool:
        backend_type = _get_backend(backend)
        csp_solver = backend_type(self.variables)  # type: ignore
        csp_solver.add_constraint(self.constraints)
        return csp_solver.solve()

    def solve(self, backend: Union[None, str, type] = None) -> bool:
        if not any(self.is_answer_key):
            warnings.warn("no answer key is given")
        backend_type = _get_backend(backend)
        csp_solver = backend_type(self.variables)  # type: ignore
        csp_solver.add_constraint(self.constraints)

        try:
            return csp_solver.solve_irrefutably(self.is_answer_key)
        except NotImplementedError:
            pass

        if not csp_solver.solve():
            # inconsistent problem
            return False

        n_var = len(self.variables)
        answer: List[Union[None, bool, int]] = [None] * n_var
        for i in range(n_var):
            if self.is_answer_key[i]:
                answer[i] = self.variables[i].sol

        while True:
            difference_cond = []
            for i in range(n_var):
                a = answer[i]
                if self.is_answer_key[i] and a is not None:
                    difference_cond.append(self.variables[i] != a)
            csp_solver.add_constraint(BoolExpr(Op.OR, difference_cond))
            if not csp_solver.solve():
                break

            for i in range(n_var):
                if (
                    self.is_answer_key[i]
                    and answer[i] is not None
                    and answer[i] != self.variables[i].sol
                ):
                    answer[i] = None

        for i in range(n_var):
            if self.is_answer_key[i]:
                self.variables[i].sol = answer[i]
        return True
