import math
import sys
from typing import Any, Callable, Optional, TypeVar
from collections.abc import Iterator

from ..array import Array1D, Array2D
from cspuz.expr import BoolExpr, IntExpr
from cspuz.grid_frame import BoolGridFrame
from cspuz.generator.builder import build_neighbor_generator
import cspuz.generator.srandom as srandom


def default_score_calculator(*args: Any) -> float:
    score = 0.0
    for arg in args:
        if isinstance(arg, (BoolExpr, IntExpr)) and arg.is_variable():
            if arg.sol is not None:
                score += 1
        elif isinstance(arg, (Array1D, Array2D, BoolGridFrame)):
            for a in arg:
                if a.sol is not None:
                    score += 1
        elif isinstance(arg, list):
            for a in arg:
                score += default_score_calculator(a)
    return score


def default_uniqueness_checker(*args: Any) -> bool:
    for arg in args:
        if isinstance(arg, (BoolExpr, IntExpr)) and arg.is_variable():
            if arg.sol is None:
                return False
        elif isinstance(arg, (Array1D, Array2D, BoolGridFrame)):
            for a in arg:
                if a.sol is None:
                    return False
        elif isinstance(arg, list):
            for a in arg:
                if not default_uniqueness_checker(a):
                    return False
    return True


def count_non_default_values(problem: Any, default: Any, weight: float = 1.0) -> float:
    if isinstance(problem, (list, tuple)):
        ret = 0.0
        for v in problem:
            ret += count_non_default_values(v, default, weight)
        return ret
    else:
        if problem != default:
            return weight
        else:
            return 0.0


Problem = TypeVar("Problem")


def generate_problem(
    solver: Callable[[Problem], tuple[Any, ...]],
    initial_problem: Optional[Problem] = None,
    neighbor_generator: Optional[Callable[[Problem], Iterator[Problem]]] = None,
    builder_pattern: Any = None,
    score: Optional[Callable[..., float]] = None,
    clue_penalty: Optional[Callable[[Problem], float]] = None,
    uniqueness: Optional[Callable[..., bool]] = None,
    pretest: Optional[Callable[[Problem], bool]] = None,
    initial_temperature: float = 5.0,
    temperature_decay: float = 0.995,
    max_steps: Optional[int] = None,
    solve_initial_problem: bool = False,
    verbose: bool = False,
) -> Optional[Problem]:
    global _use_deterministic_prng

    if builder_pattern is not None:
        if initial_problem is not None or neighbor_generator is not None:
            raise ValueError(
                "initial_problem and neighbor_generator must not be "
                "specified if builder_pattern is specified"
            )
        initial_problem, neighbor_generator = build_neighbor_generator(builder_pattern)
    else:
        if initial_problem is None or neighbor_generator is None:
            raise ValueError(
                "initial_problem and neighbor_generator must be specified "
                "if builder_pattern is not specified"
            )
    if score is None:
        score = default_score_calculator
    if uniqueness is None:
        uniqueness = default_uniqueness_checker

    problem = initial_problem
    current_score = None
    temperature = initial_temperature

    if max_steps is None:
        max_steps = 1000

    if solve_initial_problem:
        is_sat, *answer = solver(problem)
        if not is_sat:
            return None
        score_base = score(*answer)
        if clue_penalty is None:
            score_penalty = 0.0
        else:
            score_penalty = clue_penalty(problem)
        current_score = score_base - score_penalty

    for _step in range(max_steps):
        for next_problem in neighbor_generator(problem):
            if pretest is not None and not pretest(next_problem):
                continue

            is_sat, *answer = solver(next_problem)
            if not is_sat:
                continue

            if uniqueness(*answer):
                if verbose:
                    print("generated", file=sys.stderr)
                return next_problem

            next_score_base = score(*answer)
            if clue_penalty is None:
                next_score_penalty = 0.0
            else:
                next_score_penalty = clue_penalty(next_problem)
            next_score = next_score_base - next_score_penalty

            update = (
                current_score is None
                or current_score <= next_score
                or srandom.random() < math.exp((next_score - current_score) / temperature)
            )
            if update:
                if verbose:
                    print(
                        "score: {} -> {} (base: {}, penalty: {})".format(
                            current_score, next_score, next_score_base, next_score_penalty
                        ),
                        file=sys.stderr,
                    )
                problem = next_problem
                current_score = next_score
                break
        temperature *= temperature_decay
    if verbose:
        print("failed", file=sys.stderr)
    return None
