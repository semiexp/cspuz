from cspuz.grid import IntGrid, BoolGrid
from cspuz.grid_frame import BoolGridFrame


class GridDivision(object):
    def __init__(self, solver, height, width, num_regions, roots=None):
        self.solver = solver
        self.height = height
        self.width = width
        self.num_regions = num_regions
        self.region_id = IntGrid(solver,
                                 height,
                                 width,
                                 low=0,
                                 high=num_regions - 1)

        self._add_constraints(roots)

    def __getitem__(self, item):
        return self.region_id[item]

    def _add_constraints(self, roots):
        solver = self.solver
        height = self.height
        width = self.width
        region_id = self.region_id
        rank = IntGrid(solver, height, width, low=0, high=height * width - 1)
        is_root = BoolGrid(solver, height, width)
        spanning_forest = BoolGridFrame(solver, height - 1, width - 1)

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
                solver.ensure(
                    sum([(spanning_forest[y + y2, x + x2]
                          & (rank[y, x] > rank[y2, x2])).cond(1, 0)
                         for y2, x2 in neighbors]) == is_root[y, x].cond(0, 1))

                if y > 0:
                    solver.ensure(spanning_forest[y * 2 - 1, x * 2].then(
                        (region_id[y, x] == region_id[y - 1, x])
                        & (rank[y, x] != rank[y - 1, x])))
                if x > 0:
                    solver.ensure(spanning_forest[y * 2, x * 2 - 1].then(
                        (region_id[y, x] == region_id[y, x - 1])
                        & (rank[y, x] != rank[y, x - 1])))
        for i in range(self.num_regions):
            solver.ensure(
                sum([(r & (n == i)).cond(1, 0)
                     for r, n in zip(is_root[:, :], region_id[:, :])]) == 1)

        if roots is not None:
            for i, (y, x) in enumerate(roots):
                solver.ensure(region_id[y, x] == i)
                solver.ensure(is_root[y, x])
