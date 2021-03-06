import functools

from cspuz.constraints import BoolVars, IntVars


def parse_range(r, lim):
    if isinstance(r, slice):
        lo = r.start
        hi = r.stop
        if lo is None:
            lo = 0
        if hi is None:
            hi = lim
    else:
        lo = r
        hi = r + 1
    return max(0, lo), min(hi, lim)


class BoolGrid(object):
    def __init__(self, solver, height, width, variables=None):
        self.solver = solver
        self.height = height
        self.width = width
        if variables is not None:
            self.variables = variables
        else:
            self.variables = [solver.bool_var() for _ in range(height * width)]

    def __getitem__(self, pos):
        y, x = pos

        if isinstance(y, int) and isinstance(x, int):
            if not (0 <= y < self.height and 0 <= x < self.width):
                raise ValueError(
                    'position ({}, {}) is out of range of a {} * {} grid'.
                    format(y, x, self.height, self.width))
            return self.variables[y * self.width + x]
        ylo, yhi = parse_range(y, self.height)
        xlo, xhi = parse_range(x, self.width)

        ret = []
        for i in range(ylo, yhi):
            for j in range(xlo, xhi):
                ret.append(self.variables[i * self.width + j])

        return BoolVars(ret)

    def forbid_adjacent_true_cells(self):
        solver = self.solver
        height = self.height
        width = self.width

        for y in range(height):
            for x in range(width):
                if y > 0:
                    solver.ensure(~(self[y - 1, x] & self[y, x]))
                if x > 0:
                    solver.ensure(~(self[y, x - 1] & self[y, x]))

    def connect_false_cells(self):
        solver = self.solver
        height = self.height
        width = self.width
        ranks = [[solver.int_var(0, height * width - 1) for _ in range(width)]
                 for _ in range(height)]
        is_root = [[solver.bool_var() for _ in range(width)]
                   for _ in range(height)]

        root_count = None
        for y in range(height):
            for x in range(width):
                neighbors = []
                if y > 0:
                    neighbors.append((y - 1, x))
                if y < height - 1:
                    neighbors.append((y + 1, x))
                if x > 0:
                    neighbors.append((y, x - 1))
                if x < width - 1:
                    neighbors.append((y, x + 1))
                less_ranks = [
                    ((ranks[y2][x2] < ranks[y][x]) & ~self[y2, x2]).cond(1, 0)
                    for y2, x2 in neighbors
                ]
                solver.ensure((~self[y, x]).then(
                    functools.reduce(lambda a, b: a + b, less_ranks, is_root[y]
                                     [x].cond(1, 0)) >= 1))

                if root_count is None:
                    root_count = is_root[y][x].cond(1, 0)
                else:
                    root_count = root_count + is_root[y][x].cond(1, 0)

        solver.ensure(root_count <= 1)

    def forbid_adjacent_true_cells_and_connect_false_cells(self):
        self.forbid_adjacent_true_cells()
        solver = self.solver
        height = self.height
        width = self.width

        ranks = [[
            solver.int_var(0, (height * width - 1) // 2) for _ in range(width)
        ] for _ in range(height)]
        for y in range(height):
            for x in range(width):
                less_ranks = []
                nonzero = False
                for dy in [-1, 1]:
                    for dx in [-1, 1]:
                        y2 = y + dy
                        x2 = x + dx
                        if 0 <= y2 < height and 0 <= x2 < width:
                            less_ranks.append(((ranks[y2][x2] < ranks[y][x])
                                               & self[y2, x2]).cond(1, 0))
                            if (y2, x2) < (y, x):
                                solver.ensure(ranks[y2][x2] != ranks[y][x])
                        else:
                            nonzero = True
                solver.ensure(
                    self[y, x].then(sum(less_ranks) <= (0 if nonzero else 1)))


class IntGrid(object):
    def __init__(self,
                 solver,
                 height,
                 width,
                 low=None,
                 high=None,
                 variables=None):
        self.solver = solver
        self.height = height
        self.width = width
        if variables is not None:
            self.variables = list(variables)
        else:
            if low is None or high is None:
                raise ValueError('range of int variables should be specified')
            self.variables = [
                solver.int_var(low, high) for _ in range(height * width)
            ]

    def __getitem__(self, pos):
        y, x = pos

        if isinstance(y, int) and isinstance(x, int):
            if not (0 <= y < self.height and 0 <= x < self.width):
                raise ValueError(
                    'position ({}, {}) is out of range of a {} * {} grid'.
                    format(y, x, self.height, self.width))
            return self.variables[y * self.width + x]
        ylo, yhi = parse_range(y, self.height)
        xlo, xhi = parse_range(x, self.width)

        ret = []
        for i in range(ylo, yhi):
            for j in range(xlo, xhi):
                ret.append(self.variables[i * self.width + j])

        return IntVars(ret)

    def alldifferent_every_row(self):
        for y in range(self.height):
            self.solver.ensure(self[y, :].alldifferent())

    def alldifferent_every_column(self):
        for x in range(self.width):
            self.solver.ensure(self[:, x].alldifferent())


def latin_square(solver, size):
    grid = IntGrid(solver, size, size, low=1, high=size)
    grid.alldifferent_every_row()
    grid.alldifferent_every_column()
    return grid
