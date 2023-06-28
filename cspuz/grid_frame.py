import itertools
from typing import Iterator, Optional, Tuple, Union

from .array import BoolArray1D
from .expr import BoolExpr


class BoolGridFrame:
    """
    Frame of `height` * `width` grid, each of whose edges is associated with
    a bool variable.
    """

    def __init__(self, solver, height, width, horizontal=None, vertical=None):
        self.solver = solver
        self.height = height
        self.width = width

        if horizontal is None:
            self.horizontal = solver.bool_array((height + 1, width))
        else:
            self.horizontal = horizontal

        if vertical is None:
            self.vertical = solver.bool_array((height, width + 1))
        else:
            self.vertical = vertical

    def __getitem__(self, item: Tuple[int, int]) -> BoolExpr:
        y, x = item
        if not (0 <= y <= self.height * 2 and 0 <= x <= self.width * 2):
            raise IndexError("index out of range")
        if y % 2 == 0 and x % 2 == 1:
            return self.horizontal[y // 2, x // 2]
        elif y % 2 == 1 and x % 2 == 0:
            return self.vertical[y // 2, x // 2]
        else:
            raise IndexError("index does not specify a loop edge")

    def all_edges(self) -> BoolArray1D:
        return BoolArray1D(list(itertools.chain(self.horizontal, self.vertical)))

    def __iter__(self) -> Iterator[BoolExpr]:
        return itertools.chain(self.horizontal, self.vertical)

    def cell_neighbors(
        self, y: Union[int, Tuple[int, int]], x: Optional[int] = None
    ) -> BoolArray1D:
        if x is None:
            if isinstance(y, int):
                raise TypeError("two integers must be provided to 'cell_neighbors'")
            y2, x2 = y
        else:
            if x is None or isinstance(y, tuple):
                raise TypeError("two integers must be provided to 'cell_neighbors'")
            y2 = y
            x2 = x
        if not (0 <= y2 < self.height and 0 <= x2 < self.width):
            raise IndexError("index out of range")
        return BoolArray1D(
            [
                self.horizontal[y2, x2],
                self.horizontal[y2 + 1, x2],
                self.vertical[y2, x2],
                self.vertical[y2, x2 + 1],
            ]
        )

    def dual(self) -> "BoolInnerGridFrame":
        return BoolInnerGridFrame(
            solver=self.solver,
            height=self.height + 1,
            width=self.width + 1,
            horizontal=self.vertical,
            vertical=self.horizontal,
        )

    def single_loop(self):
        from . import graph

        return graph.active_edges_single_cycle(self.solver, self)


class BoolInnerGridFrame:
    def __init__(self, solver, height, width, horizontal=None, vertical=None):
        self.solver = solver
        self.height = height
        self.width = width

        if horizontal is None:
            self.horizontal = solver.bool_array((height - 1, width))
        else:
            self.horizontal = horizontal

        if vertical is None:
            self.vertical = solver.bool_array((height, width - 1))
        else:
            self.vertical = vertical

    def dual(self) -> BoolGridFrame:
        return BoolGridFrame(
            solver=self.solver,
            height=self.height - 1,
            width=self.width - 1,
            horizontal=self.vertical,
            vertical=self.horizontal,
        )
