import math
import random
import sys
import copy

from cspuz.constraints import IntVar, BoolVar, Array


def default_score_calculator(*args):
    score = 0
    for arg in args:
        if isinstance(arg, (IntVar, BoolVar)):
            if arg.sol is not None:
                score += 1
        elif isinstance(arg, Array):
            for a in arg:
                if a.sol is not None:
                    score += 1
    return score


def default_uniqueness_checker(*args):
    for arg in args:
        if isinstance(arg, (IntVar, BoolVar)):
            if arg.sol is None:
                return False
        elif isinstance(arg, Array):
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
                     initial_problem,
                     neighbor_generator,
                     score=None,
                     clue_penalty=None,
                     uniqueness=None,
                     pretest=None,
                     initial_temperature=5.0,
                     temperature_decay=0.995,
                     max_steps=None,
                     verbose=False):
    if score is None:
        score = default_score_calculator
    if uniqueness is None:
        uniqueness = default_uniqueness_checker

    problem = initial_problem
    current_score = None
    temperature = initial_temperature

    if max_steps is None:
        max_steps = 1000

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


class Builder:
    def initial(self):
        raise NotImplementedError

    def candidates(self, current):
        raise NotImplementedError

    def copy_with_update(self, previous, update):
        raise NotImplementedError


class Choice(Builder):
    def __init__(self, choice, default):
        self.choice = list(choice)
        self.default = default

    def initial(self):
        return self.default

    def candidates(self, current):
        return [c for c in self.choice if c != current]

    def copy_with_update(self, previous, update):
        return update


class ArrayBuilder2D(Builder):
    def __init__(self, height, width, choice, default, disallow_adjacent=False, symmetry=False):
        self.height = height
        self.width = width
        self.choice = list(choice)
        self.default = default
        self.non_default = [c for c in self.choice if c != self.default]
        self.disallow_adjacent = disallow_adjacent
        self.symmetry = symmetry

    def initial(self):
        return [[self.default for _ in range(self.width)] for _ in range(self.height)]

    def candidates(self, current):
        ret = []
        for y in range(self.height):
            for x in range(self.width):
                if self.disallow_adjacent:
                    default_only = False
                    if 0 < y and current[y - 1][x] != self.default:
                        default_only = True
                    if 0 < x and current[y][x - 1] != self.default:
                        default_only = True
                    if y < self.height - 1 and current[y + 1][x] != self.default:
                        default_only = True
                    if x < self.width - 1 and current[y][x + 1] != self.default:
                        default_only = True
                else:
                    default_only = False
                if self.symmetry:
                    y2 = self.height - 1 - y
                    x2 = self.width - 1 - x
                    if abs(y2 - y) + abs(x2 - x) == 1:
                        default_only = True
                    if current[y][x] != self.default:
                        ret.append([(y, x, self.default), (y2, x2, self.default)])
                    if not default_only:
                        if current[y][x] == self.default:
                            for v in self.non_default:
                                v2 = random.choice(self.non_default)
                                if current[y][x] != v or current[y2][x2] != v2:
                                    ret.append([(y, x, v), (y2, x2, v2)])
                        else:
                            for v in self.non_default:
                                if v != current[y][x]:
                                    ret.append([(y, x, v)])
                else:
                    for v in self.choice:
                        if default_only and v != self.default:
                            continue
                        if v != current[y][x]:
                            ret.append([(y, x, v)])
        return ret

    def copy_with_update(self, previous, update):
        ret = copy.deepcopy(previous)
        for y, x, v in update:
            ret[y][x] = v
        return ret


def build_neighbor_generator(pattern):
    variables = []

    def enumerate_variables(pat, pos):
        if isinstance(pat, Builder):
            variables.append((pos, pat))
            return pat.initial()
        elif isinstance(pat, (list, tuple)):
            ret = []
            for i in range(len(pat)):
                ret.append(enumerate_variables(pat[i], pos + [i]))
            if isinstance(pat, list):
                return ret
            else:
                return tuple(ret)
        else:
            return pat

    initial = enumerate_variables(pattern, [])

    def get(pat, pos):
        if len(pos) == 0:
            return pat
        return get(pat[pos[0]], pos[1:])

    def with_update(problem, pat, pos, v):
        if len(pos) == 0:
            assert isinstance(pat, Builder)
            return pat.copy_with_update(problem, v)
        if isinstance(pat, (list, tuple)):
            ret = [with_update(problem[i], pat[i], pos[1:], v) if i == pos[0] else problem[i] for i in range(len(pat))]
            if isinstance(pat, tuple):
                ret = tuple(ret)
            return ret

    def generator(problem):
        cands = []
        for pos, choice in variables:
            subproblem = get(problem, pos)
            subpattern = get(pattern, pos)
            for v in subpattern.candidates(subproblem):
                cands.append((pos, v))
        random.shuffle(cands)
        for pos, val in cands:
            next_problem = with_update(problem, pattern, pos, val)
            yield next_problem

    return initial, generator
