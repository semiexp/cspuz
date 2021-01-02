import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.grid_frame import BoolGridFrame
from cspuz.constraints import fold_or
from cspuz.puzzle import util
from cspuz.generator import (generate_problem, count_non_default_values,
                             ArrayBuilder2D)


def solve_geradeweg(height, width, problem):
    def line_length(edges):
        edges = list(edges)
        if len(edges) == 0:
            return 0
        ret = edges[-1].cond(1, 0)
        for i in range(len(edges) - 2, -1, -1):
            ret = edges[i].cond(1 + ret, 0)
        return ret

    solver = Solver()
    grid_frame = BoolGridFrame(solver, height - 1, width - 1)
    solver.add_answer_key(grid_frame)
    is_passed = graph.active_edges_single_cycle(solver, grid_frame)

    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 1:
                solver.ensure(is_passed[y, x])
                solver.ensure(
                    fold_or(
                        ([grid_frame.horizontal[y, x - 1]] if x > 0 else []) +
                        ([grid_frame.horizontal[y,
                                                x]] if x < width - 1 else [])).
                    then(
                        line_length(
                            reversed(list(grid_frame.horizontal[y, :x]))) +
                        line_length(grid_frame.horizontal[y, x:]) == problem[y]
                        [x]))
                solver.ensure(
                    fold_or(
                        ([grid_frame.vertical[y - 1, x]] if y > 0 else []) +
                        ([grid_frame.vertical[y, x]] if y < height - 1 else [])
                    ).then(
                        line_length(reversed(list(grid_frame.vertical[:y,
                                                                      x]))) +
                        line_length(grid_frame.vertical[y:,
                                                        x]) == problem[y][x]))

    is_sat = solver.solve()
    return is_sat, grid_frame


def generate_geradeweg(height, width, symmetry=False, verbose=False):
    generated = generate_problem(
        lambda problem: solve_geradeweg(height, width, problem),
        builder_pattern=ArrayBuilder2D(height,
                                       width,
                                       range(0, 6),
                                       default=0,
                                       symmetry=symmetry),
        clue_penalty=lambda problem: count_non_default_values(
            problem, default=0, weight=10),
        verbose=verbose)
    return generated


def _main():
    if len(sys.argv) == 1:
        # https://puzsq.sakura.ne.jp/main/puzzle_play.php?pid=8864
        height = 10
        width = 10
        problem = [
            [5, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 5, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 2, 0, 0, 0, 3],
            [0, 0, 0, 0, 0, 0, 0, 0, 4, 0],
            [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
            [2, 0, 0, 0, 4, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 4, 0, 0, 0],
            [0, 0, 2, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 5],
        ]
        is_sat, is_line = solve_geradeweg(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(util.stringify_grid_frame(is_line))
    else:
        cspuz.config.solver_timeout = 600.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                problem = generate_geradeweg(height,
                                             width,
                                             symmetry=False,
                                             verbose=True)
                if problem is not None:
                    print(
                        util.stringify_array(
                            problem, lambda x: '.' if x == 0 else str(x)))
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print('timeout', file=sys.stderr)


if __name__ == '__main__':
    _main()
