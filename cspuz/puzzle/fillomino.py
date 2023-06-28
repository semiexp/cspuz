import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D


def solve_fillomino(height, width, problem, checkered=False):
    solver = Solver()
    size = solver.int_array((height, width), 1, height * width)
    solver.add_answer_key(size)
    border = graph.BoolInnerGridFrame(solver, height, width)
    graph.division_connected_variable_groups_with_borders(solver, group_size=size, is_border=border)
    solver.ensure(border.vertical == (size[:, :-1] != size[:, 1:]))
    solver.ensure(border.horizontal == (size[:-1, :] != size[1:, :]))
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 1:
                solver.ensure(size[y, x] == problem[y][x])
    if checkered:
        color = solver.bool_array((height, width))
        solver.ensure(border.vertical == (color[:, :-1] != color[:, 1:]))
        solver.ensure(border.horizontal == (color[:-1, :] != color[1:, :]))
    is_sat = solver.solve()
    return is_sat, size


def generate_fillomino(
    height, width, checkered=False, disallow_adjacent=False, symmetry=False, verbose=False
):
    generated = generate_problem(
        lambda problem: solve_fillomino(height, width, problem, checkered=checkered),
        builder_pattern=ArrayBuilder2D(
            height,
            width,
            range(0, 9),
            default=0,
            disallow_adjacent=disallow_adjacent,
            symmetry=symmetry,
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=5),
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        # https://twitter.com/semiexp/status/1227192389120356353
        height = 8
        width = 8
        problem = [
            [0, 0, 0, 5, 4, 0, 0, 0],
            [0, 0, 0, 4, 1, 3, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 4],
            [6, 0, 4, 0, 0, 0, 0, 7],
            [0, 5, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 2],
            [1, 0, 0, 0, 4, 0, 0, 7],
            [7, 0, 0, 6, 2, 0, 7, 0],
        ]
        #        """
        is_sat, ans = solve_fillomino(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(ans, str))
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                problem = generate_fillomino(
                    height, width, disallow_adjacent=True, symmetry=True, verbose=True
                )
                if problem is not None:
                    print(
                        util.stringify_array(problem, lambda x: "." if x == 0 else str(x)),
                        flush=True,
                    )
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
