import argparse
import sys
import subprocess

import cspuz
from cspuz import Solver, graph, count_true
from cspuz.puzzle import util
from cspuz.generator import (generate_problem, count_non_default_values,
                             ArrayBuilder2D)


def solve_nurikabe(height, width, problem, unknown_low=None):
    solver = Solver()
    clues = []
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 1 or problem[y][x] == -1:
                clues.append((y, x, problem[y][x]))
    division = solver.int_array((height, width), 0, len(clues))

    roots = [None] + list(map(lambda x: (x[0], x[1]), clues))
    graph.division_connected(solver, division, len(clues) + 1, roots=roots)
    is_white = solver.bool_array((height, width))
    solver.ensure(is_white == (division != 0))
    solver.add_answer_key(is_white)

    solver.ensure(
        (is_white[:-1, :]
         & is_white[1:, :]).then(division[:-1, :] == division[1:, :]))
    solver.ensure((is_white[:, :-1]
                   & is_white[:, 1:]).then(division[:, :-1] == division[:,
                                                                        1:]))
    solver.ensure(is_white[:-1, :-1] | is_white[:-1, 1:] | is_white[1:, :-1]
                  | is_white[1:, 1:])
    for i, (y, x, n) in enumerate(clues):
        if n > 0:
            solver.ensure(count_true(division == (i + 1)) == n)
        elif n == -1 and unknown_low is not None:
            solver.ensure(count_true(division == (i + 1)) >= unknown_low)

    is_sat = solver.solve()

    return is_sat, is_white


def resolve_unknown(height, width, problem, unknown_low=None):
    is_sat, sol = solve_nurikabe(height,
                                 width,
                                 problem,
                                 unknown_low=unknown_low)

    visited = [[False for _ in range(width)] for _ in range(height)]

    def visit(y, x):
        if not (0 <= y < height
                and 0 <= x < width) or visited[y][x] or not sol[y, x].sol:
            return 0
        visited[y][x] = True
        ret = 1 + visit(y - 1, x) + visit(y, x - 1) + visit(y + 1, x) + visit(
            y, x + 1)
        return ret

    ret = []
    for y in range(height):
        row = []
        for x in range(width):
            if problem[y][x] == -1:
                row.append(visit(y, x))
            else:
                row.append(problem[y][x])
        ret.append(row)
    return ret


def generate_nurikabe(height,
                      width,
                      min_clue=None,
                      max_clue=10,
                      verbose=False):
    disallow_adjacent = []
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if (dy, dx) != (0, 0):
                disallow_adjacent.append((dy, dx))
    generated = generate_problem(
        lambda problem: solve_nurikabe(
            height, width, problem, unknown_low=min_clue),
        builder_pattern=ArrayBuilder2D(height,
                                       width, [-1, 0] +
                                       list(range(min_clue or 1, max_clue)),
                                       default=0,
                                       disallow_adjacent=True,
                                       symmetry=False),
        clue_penalty=lambda problem: count_non_default_values(
            problem, default=0, weight=5),
        verbose=verbose)
    if generated is None:
        return None
    else:
        return resolve_unknown(height, width, generated, unknown_low=min_clue)


def main():
    if len(sys.argv) == 1:
        # https://twitter.com/semiexp/status/1222541993638678530
        height = 10
        width = 10
        problem = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 7, 0, 0, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0, 0, 9, 0],
            [0, 0, 0, 0, 0, 0, 0, 7, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 7, 0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        is_sat, is_white = solve_nurikabe(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(
                util.stringify_array(is_white, {
                    None: '?',
                    True: '.',
                    False: '#'
                }))
    else:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-h', '--height', type=int)
        parser.add_argument('-w', '--width', type=int)
        parser.add_argument('--min-clue', type=int, default=1)
        parser.add_argument('--max-clue', type=int, default=10)
        parser.add_argument('-v', '--verbose', action='store_true')
        args = parser.parse_args()

        height = args.height
        width = args.width
        min_clue = args.min_clue
        max_clue = args.max_clue
        verbose = args.verbose
        cspuz.config.solver_timeout = 1800.0
        while True:
            try:
                problem = generate_nurikabe(height,
                                            width,
                                            min_clue=min_clue,
                                            max_clue=max_clue,
                                            verbose=verbose)
                if problem is not None:
                    print(util.stringify_array(
                        problem, lambda x: '.'
                        if x == 0 else ('?' if x == -1 else str(x))),
                          flush=True)
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print('timeout', file=sys.stderr)


if __name__ == '__main__':
    main()
