import itertools

from cspuz.constraints import Array, BoolVars
from cspuz.grid import BoolGrid


class BoolGridFrame(object):
    """
    Frame of `height` * `width` grid, each of whose edges is associated with a bool variable.
    """
    def __init__(self, solver, height, width):
        self.solver = solver
        self.height = height
        self.width = width
        self.horizontal = solver.bool_array((height + 1, width))
        self.vertical = solver.bool_array((height, width + 1))

    def __getitem__(self, item):
        y, x = item
        if not (0 <= y <= self.height * 2 and 0 <= x <= self.width * 2):
            raise IndexError('index out of range')
        if y % 2 == 0 and x % 2 == 1:
            return self.horizontal[y // 2, x // 2]
        elif y % 2 == 1 and x % 2 == 0:
            return self.vertical[y // 2, x // 2]
        else:
            raise IndexError('index does not specify a loop edge')

    def all_edges(self):
        return BoolVars(list(itertools.chain(self.horizontal, self.vertical)))

    def __iter__(self):
        return itertools.chain(self.horizontal, self.vertical)

    def cell_neighbors(self, *p):
        if len(p) == 1:
            y, x = p[0]
        else:
            y, x = p
        if not (0 <= y < self.height and 0 <= x < self.width):
            raise IndexError('index out of range')
        return Array([self.horizontal[y, x], self.horizontal[y + 1, x], self.vertical[y, x], self.vertical[y, x + 1]])

    def single_loop(self):
        from cspuz import graph
        return graph.active_edges_single_cycle(self.solver, self)
