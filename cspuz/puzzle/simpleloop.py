import random
import sys
import subprocess

import cspuz
from cspuz import Solver, BoolGridFrame, graph
from cspuz.puzzle import util
from cspuz.generator import generate_problem, ArrayBuilder2D, count_non_default_values


def solve_simpleloop(height, width, blocked, pivot):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height - 1, width - 1)
    solver.add_answer_key(grid_frame)
    is_passed = graph.active_edges_single_cycle(solver, grid_frame)

    for y in range(height):
        for x in range(width):
            if (y, x) != pivot:
                solver.ensure(is_passed[y, x] == (blocked[y][x] == 0))

    py, px = pivot
    n_pass = 0
    for y in range(height):
        for x in range(width):
            if (y, x) != pivot and blocked[y][x] == 0:
                n_pass += 1
    solver.ensure(is_passed[py, px] == (n_pass % 2 == 1))
    is_sat = solver.solve()
    return is_sat, grid_frame


def generate_simpleloop(height, width, verbose):
    pivot = (random.randint(0, height - 1), random.randint(0, width - 1))

    def pretest(problem):
        parity = [0, 0]
        for y in range(height):
            for x in range(width):
                if problem[y][x] == 1:
                    continue
                a = (y + x) % 2 * 2 - 1
                if (y, x) != pivot:
                    parity[0] += a
                parity[1] += a
        return parity[0] == 0 or parity[1] == 0
    generated = generate_problem(lambda problem: solve_simpleloop(height, width, problem, pivot),
                                 builder_pattern=ArrayBuilder2D(height, width, [0, 1], default=0, disallow_adjacent=True),
                                 clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=10),
                                 pretest=pretest, verbose=verbose)
    if generated is None:
        return None
    num_pass = 0
    for y in range(height):
        for x in range(width):
            if (y, x) != pivot and generated[y][x] == 0:
                num_pass += 1
    y, x = pivot
    generated[y][x] = 1 - num_pass % 2
    return generated


def _main():
    if len(sys.argv) == 1:
        pass
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                problem = generate_simpleloop(height, width, verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem, {0: '.', 1: '#'}), flush=True)
                    print('', flush=True)
            except subprocess.TimeoutExpired:
                print('timeout', file=sys.stderr)


if __name__ == '__main__':
    _main()
