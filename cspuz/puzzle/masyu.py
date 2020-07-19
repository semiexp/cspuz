import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.grid_frame import BoolGridFrame
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D


def solve_masyu(height, width, problem):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height - 1, width - 1)
    solver.add_answer_key(grid_frame)
    graph.active_edges_single_cycle(solver, grid_frame)

    def get_edge(y, x, neg=False):
        if 0 <= y <= 2 * (height - 1) and 0 <= x <= 2 * (width - 1):
            if y % 2 == 0:
                r = grid_frame.horizontal[y // 2][x // 2]
            else:
                r = grid_frame.vertical[y // 2][x // 2]
            if neg:
                return ~r
            else:
                return r
        else:
            return neg

    for y in range(height):
        for x in range(width):
            if problem[y][x] == 1:
                solver.ensure((get_edge(y * 2, x * 2 - 1) & get_edge(y * 2, x * 2 + 1) & (get_edge(y * 2, x * 2 - 3, True) | get_edge(y * 2, x * 2 + 3, True)))
                            | (get_edge(y * 2 - 1, x * 2) & get_edge(y * 2 + 1, x * 2) & (get_edge(y * 2 - 3, x * 2, True) | get_edge(y * 2 + 3, x * 2, True))))
            elif problem[y][x] == 2:
                dirs = [
                    get_edge(y * 2, x * 2 - 1) & get_edge(y * 2, x * 2 - 3),
                    get_edge(y * 2 - 1, x * 2) & get_edge(y * 2 - 3, x * 2),
                    get_edge(y * 2, x * 2 + 1) & get_edge(y * 2, x * 2 + 3),
                    get_edge(y * 2 + 1, x * 2) & get_edge(y * 2 + 3, x * 2),
                ]
                solver.ensure((dirs[0] | dirs[2]) & (dirs[1] | dirs[3]))

    is_sat = solver.solve()
    return is_sat, grid_frame


def generate_masyu(height, width, symmetry=False, verbose=False):
    generated = generate_problem(lambda problem: solve_masyu(height, width, problem),
                                 builder_pattern=ArrayBuilder2D(height, width, [0, 1, 2], default=0, symmetry=symmetry),
                                 clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=10),
                                 verbose=verbose)
    return generated


def _main():
    if len(sys.argv) == 1:
        # https://puzsq.jp/main/puzzle_play.php?pid=9833
        height = 10
        width = 10
        problem = [
            [0, 0, 0, 0, 2, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [0, 2, 0, 0, 0, 0, 0, 0, 2, 0],
            [1, 0, 2, 0, 0, 1, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 1, 0, 1, 0, 0],
            [0, 0, 0, 2, 0, 0, 0, 0, 0, 0],
            [0, 2, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 1, 0, 0],
        ]
        is_sat, is_line = solve_masyu(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(util.stringify_grid_frame(is_line))
    else:
        cspuz.config.solver_timeout = 600.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                problem = generate_masyu(height, width, symmetry=False, verbose=False)
                if problem is not None:
                    print(util.stringify_array(problem, {0: '.', 1: 'O', 2: '#'}))
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print('timeout', file=sys.stderr)


if __name__ == '__main__':
    _main()
