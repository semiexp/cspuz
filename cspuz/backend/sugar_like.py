"""
CSP backend using the Sugar CSP solver (http://bach.istc.kobe-u.ac.jp/sugar/).
"""

import multiprocessing
import pickle
import subprocess
import tempfile
from typing import Any, BinaryIO, Callable, Optional, TypeVar

from ..configuration import config
from ..expr import Op, Expr, BoolVar, IntVar

from .backend import Backend
from ._subproc import run_subprocess

T = TypeVar("T")


def _subprocess_worker(func: Callable[..., Any], args: tuple, result_file: BinaryIO) -> None:
    try:
        result = (True, func(*args))
    except BaseException as exc:
        result = (False, exc)
    pickle.dump(result, result_file)
    result_file.flush()


def _run_with_timeout(func: Callable[..., T], *args: Any, timeout: Optional[float]) -> T:
    """Run a function with a timeout, inheriting Python and native library configuration.

    A fork context is required to preserve settings such as cspuz_core.set_config().
    Call this from a single-threaded process: native locks may not be safe after fork.
    With no timeout, call the function directly without serializing its result.
    """
    if timeout is None:
        return func(*args)

    context = multiprocessing.get_context("fork")
    # A pipe can fill up and block the child while the parent waits for it to exit.
    # A temporary file lets us wait with a timeout even for large results.
    with tempfile.TemporaryFile() as result_file:
        process = context.Process(target=_subprocess_worker, args=(func, args, result_file))
        process.start()
        try:
            process.join(timeout)
            if process.is_alive():
                raise subprocess.TimeoutExpired(getattr(func, "__name__", repr(func)), timeout)
            if process.exitcode != 0:
                raise RuntimeError(f"Solver subprocess exited with code {process.exitcode}")
            result_file.seek(0)
            try:
                success, result = pickle.load(result_file)
            except EOFError as exc:
                raise RuntimeError("Solver subprocess exited without returning a result") from exc
            if not success:
                raise result
            return result
        finally:
            if process.is_alive():
                process.kill()
            process.join()
            process.close()


OP_TO_OPNAME = {
    Op.NEG: "-",
    Op.ADD: "+",
    Op.SUB: "-",
    Op.EQ: "=",
    Op.NE: "!=",
    Op.LE: "<=",
    Op.LT: "<",
    Op.GE: ">=",
    Op.GT: ">",
    Op.NOT: "!",
    Op.AND: "&&",
    Op.OR: "||",
    Op.IFF: "iff",
    Op.XOR: "xor",
    Op.IMP: "=>",
    Op.IF: "if",
    Op.ALLDIFF: "alldifferent",
    Op.GRAPH_ACTIVE_VERTICES_CONNECTED: "graph-active-vertices-connected",
    Op.GRAPH_DIVISION: "graph-division",
}


def _convert_variable(v):
    if isinstance(v, BoolVar):
        return "(bool b{})".format(v.id)
    elif isinstance(v, IntVar):
        return "(int i{} {} {})".format(v.id, v.lo, v.hi)
    else:
        raise TypeError()


def _convert_expr(e):
    if e is None:
        return "*"
    if isinstance(e, bool):
        return "true" if e else "false"
    if isinstance(e, int):
        return str(e)
    if not isinstance(e, Expr):
        raise TypeError()

    if isinstance(e, BoolVar):
        return "b{}".format(e.id)
    elif isinstance(e, IntVar):
        return "i{}".format(e.id)
    elif e.op == Op.BOOL_CONSTANT:
        return "true" if e.operands[0] else "false"
    elif e.op == Op.INT_CONSTANT:
        return str(e.operands[0])
    else:
        if e.op == Op.AND and len(e.operands) == 0:
            return "true"
        elif e.op == Op.OR and len(e.operands) == 0:
            return "false"
        return "({} {})".format(OP_TO_OPNAME[e.op], " ".join(map(_convert_expr, e.operands)))


class SugarLikeBackend(Backend):
    def __init__(self, variables):
        self.variables = variables
        max_var_id = -1
        for v in self.variables:
            if isinstance(v, (BoolVar, IntVar)):
                max_var_id = max(max_var_id, v.id)
            else:
                raise TypeError()
        self.max_var_id = max_var_id
        self.converted_variables = list(map(_convert_variable, self.variables))
        self.converted_constraints = []

    def add_constraint(self, constraint):
        if isinstance(constraint, list):
            self.converted_constraints += map(_convert_expr, constraint)
        else:
            self.converted_constraints.append(_convert_expr(constraint))

    def solve(self):
        csp_description = "\n".join(self.converted_variables + self.converted_constraints)
        out = self._call_solver(csp_description).split("\n")
        if "UNSATISFIABLE" in out[0]:
            for v in self.variables:
                v.sol = None
            return False

        assignment = [None] * (self.max_var_id + 1)
        for line in out[1:]:
            if len(line) <= 2:
                break
            var, val = line[2:].strip().split("\t")
            if val == "true":
                converted_val = True
            elif val == "false":
                converted_val = False
            else:
                converted_val = int(val)
            assignment[int(var[1:])] = converted_val
        for v in self.variables:
            v.sol = assignment[v.id]
        return True

    def solve_irrefutably(self, is_answer_key):
        answer_keys = []
        for i in range(len(self.variables)):
            if is_answer_key[i]:
                if isinstance(self.variables[i], BoolVar):
                    answer_keys.append("b{}".format(self.variables[i].id))
                elif isinstance(self.variables[i], IntVar):
                    answer_keys.append("i{}".format(self.variables[i].id))
                else:
                    raise TypeError()
        answer_keys_desc = "#" + " ".join(answer_keys)
        csp_description = "\n".join(
            self.converted_variables + self.converted_constraints + [answer_keys_desc]
        )
        out = self._call_solver(csp_description).split("\n")
        for v in self.variables:
            v.sol = None

        if "unsat" in out[0]:
            return False

        assignment = [None] * (self.max_var_id + 1)
        for line in out[1:]:
            if len(line) <= 2:
                break
            var, val = line.split(" ")
            if val == "true":
                converted_val = True
            elif val == "false":
                converted_val = False
            else:
                converted_val = int(val)
            assignment[int(var[1:])] = converted_val
        for v in self.variables:
            v.sol = assignment[v.id]
        return True

    def _call_solver(self, csp_description: str) -> str:
        raise NotImplementedError


class SugarBackend(SugarLikeBackend):
    def solve_irrefutably(self, is_answer_key):
        raise NotImplementedError

    def _call_solver(self, csp_description: str) -> str:
        sugar_path = config.backend_path or "sugar"
        out = run_subprocess(
            [sugar_path, "/dev/stdin"], csp_description, timeout=config.solver_timeout
        )
        return out


class SugarExtendedBackend(SugarLikeBackend):
    def _call_solver(self, csp_description: str) -> str:
        sugar_path = config.backend_path or "sugar"
        out = run_subprocess(
            [sugar_path, "/dev/stdin"], csp_description, timeout=config.solver_timeout
        )
        return out


class CSugarBackend(SugarLikeBackend):
    def _call_solver(self, csp_description: str) -> str:
        import pycsugar  # type: ignore

        return _run_with_timeout(pycsugar.solver, csp_description, timeout=config.solver_timeout)


class EnigmaCSPBackend(SugarLikeBackend):
    def _call_solver(self, csp_description: str) -> str:
        import enigma_csp  # type: ignore

        return _run_with_timeout(enigma_csp.solver, csp_description, timeout=config.solver_timeout)


class CspuzCoreBackend(SugarLikeBackend):
    def __init__(self, variables):
        super().__init__(variables)
        self._perf_stats: Optional[dict] = None

    def _call_solver(self, csp_description: str) -> str:
        import cspuz_core  # type: ignore

        desc, perf = _run_with_timeout(
            cspuz_core.solver_with_perf, csp_description, timeout=config.solver_timeout
        )
        self._perf_stats = perf  # type: ignore
        return desc

    def perf_stats(self) -> Optional[dict]:
        return self._perf_stats
