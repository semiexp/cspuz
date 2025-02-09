import copy
import cspuz.generator.srandom as srandom


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
            ret = [
                with_update(problem[i], pat[i], pos[1:], v) if i == pos[0] else problem[i]
                for i in range(len(pat))
            ]
            if isinstance(pat, tuple):
                ret = tuple(ret)
            return ret

    def generator(problem):
        global _use_deterministic_prng
        cands = []
        for pos, choice in variables:
            subproblem = get(problem, pos)
            subpattern = get(pattern, pos)
            for v in subpattern.candidates(subproblem):
                cands.append((pos, v))
        srandom.shuffle(cands)
        for pos, val in cands:
            next_problem = with_update(problem, pattern, pos, val)
            yield next_problem

    return initial, generator


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
    def __init__(
        self,
        height,
        width,
        choice,
        default,
        disallow_adjacent=False,
        symmetry=False,
        initial=None,
        use_move=False,
    ):
        self.height = height
        self.width = width
        self.choice = list(choice)
        self.default = default
        self.non_default = [c for c in self.choice if c != self.default]
        if disallow_adjacent is True:
            self.disallow_adjacent = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        elif disallow_adjacent is False:
            self.disallow_adjacent = []
        else:
            self.disallow_adjacent = disallow_adjacent
        self.symmetry = symmetry
        self.initial_problem = initial
        self.use_move = use_move

    def initial(self):
        if self.initial_problem is not None:
            return self.initial_problem
        return [[self.default for _ in range(self.width)] for _ in range(self.height)]

    def candidates(self, current):
        global _use_deterministic_prng
        ret = []
        if self.use_move:
            if self.symmetry:
                for y1 in range(self.height):
                    for x1 in range(self.width):
                        for _ in range(10):
                            y2 = srandom.randint(0, self.height - 1)
                            x2 = srandom.randint(0, self.width - 1)
                            if (y1, x1) == (y2, x2):
                                continue

                            y1b = self.height - 1 - y1
                            x1b = self.width - 1 - x1
                            y2b = self.height - 1 - y2
                            x2b = self.width - 1 - x2
                            if (y1, x1) == (y1b, x1b):
                                continue
                            if (y1, x1) == (y2b, x2b):
                                continue

                            if current[y1][x1] != current[y2][x2]:
                                ret.append(
                                    [
                                        (y1, x1, current[y2][x2]),
                                        (y2, x2, current[y1][x1]),
                                        (y1b, x1b, current[y2b][x2b]),
                                        (y2b, x2b, current[y1b][x1b]),
                                    ]
                                )
            else:
                for y in range(self.height):
                    for x in range(self.width):
                        for _ in range(10):
                            y2 = srandom.randint(0, self.height - 1)
                            x2 = srandom.randint(0, self.width - 1)
                            if (y, x) == (y2, x2):
                                continue

                            if current[y][x] != current[y2][x2]:
                                ret.append(
                                    [
                                        (y, x, current[y2][x2]),
                                        (y2, x2, current[y][x]),
                                    ]
                                )

        for y in range(self.height):
            for x in range(self.width):
                default_only = False
                for dy, dx in self.disallow_adjacent:
                    y2 = y + dy
                    x2 = x + dx
                    if (
                        0 <= y2 < self.height
                        and 0 <= x2 < self.width
                        and current[y2][x2] != self.default
                    ):
                        default_only = True
                if self.symmetry:
                    y2 = self.height - 1 - y
                    x2 = self.width - 1 - x
                    if (y2 - y, x2 - x) in self.disallow_adjacent:
                        default_only = True
                    if current[y][x] != self.default:
                        ret.append([(y, x, self.default), (y2, x2, self.default)])
                    if not default_only:
                        if current[y][x] == self.default:
                            for v in self.non_default:
                                v2 = srandom.choice(self.non_default)
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
