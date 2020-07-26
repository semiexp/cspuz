import math
import random
import sys

from cspuz.constraints import IntVar, BoolVar, Array
from cspuz.grid_frame import BoolGridFrame
from cspuz.generator.builder import build_neighbor_generator


def default_score_calculator(*args):
    score = 0
    for arg in args:
        if isinstance(arg, (IntVar, BoolVar)):
            if arg.sol is not None:
                score += 1
        elif isinstance(arg, (Array, BoolGridFrame)):
            for a in arg:
                if a.sol is not None:
                    score += 1
    return score


def default_uniqueness_checker(*args):
    for arg in args:
        if isinstance(arg, (IntVar, BoolVar)):
            if arg.sol is None:
                return False
        elif isinstance(arg, (Array, BoolGridFrame)):
            for a in arg:
                if a.sol is None:
                    return False
    return True


def count_non_default_values(problem, default, weight=1):
    if isinstance(problem, (list, tuple)):
        ret = 0
        for v in problem:
            ret += count_non_default_values(v, default, weight)
        return ret
    else:
        if problem != default:
            return weight
        else:
            return 0


def generate_problem(solver,
                     initial_problem=None,
                     neighbor_generator=None,
                     builder_pattern=None,
                     score=None,
                     clue_penalty=None,
                     uniqueness=None,
                     pretest=None,
                     initial_temperature=5.0,
                     temperature_decay=0.995,
                     max_steps=None,
                     solve_initial_problem=False,
                     verbose=False):
    if builder_pattern is not None:
        if initial_problem is not None or neighbor_generator is not None:
            raise ValueError('initial_problem and neighbor_generator must not be specified if builder_pattern is specified')
        initial_problem, neighbor_generator = build_neighbor_generator(builder_pattern)
    else:
        if initial_problem is None or neighbor_generator is None:
            raise ValueError('initial_problem and neighbor_generator must be specified if builder_pattern is not specified')
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
            score_penalty = 0
        else:
            score_penalty = clue_penalty(problem)
        current_score = score_base - score_penalty

    for step in range(max_steps):
        for next_problem in neighbor_generator(problem):
            if pretest is not None and not pretest(next_problem):
                continue

            is_sat, *answer = solver(next_problem)
            if not is_sat:
                continue

            if uniqueness(*answer):
                print('generated', file=sys.stderr)
                return next_problem

            next_score_base = score(*answer)
            if clue_penalty is None:
                next_score_penalty = 0
            else:
                next_score_penalty = clue_penalty(next_problem)
            next_score = next_score_base - next_score_penalty

            update = current_score is None or current_score <= next_score or \
                     random.random() < math.exp((next_score - current_score) / temperature)
            if update:
                if verbose:
                    print('score: {} -> {} (base: {}, penalty: {})'.format(
                        current_score, next_score, next_score_base, next_score_penalty), file=sys.stderr)
                problem = next_problem
                current_score = next_score
                break
        temperature *= temperature_decay
    print('failed', file=sys.stderr)
    return None
