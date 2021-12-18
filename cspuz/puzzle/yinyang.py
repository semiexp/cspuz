import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D


def solve_yinyang(height, width, problem):
    solver = Solver()
    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)

    graph.active_vertices_connected(solver, is_black)
    graph.active_vertices_connected(solver, ~is_black)
    solver.ensure(is_black[:-1, :-1] | is_black[:-1, 1:] | is_black[1:, :-1] | is_black[1:, 1:])
    solver.ensure(~(is_black[:-1, :-1] & is_black[:-1, 1:] & is_black[1:, :-1] & is_black[1:, 1:]))

    # auxiliary constraint
    solver.ensure(
        ~(is_black[:-1, :-1] & is_black[1:, 1:] & ~is_black[1:, :-1] & ~is_black[:-1, 1:])
    )
    solver.ensure(
        ~(~is_black[:-1, :-1] & ~is_black[1:, 1:] & is_black[1:, :-1] & is_black[:-1, 1:])
    )

    circ = []
    for y in range(height):
        circ.append(is_black[y, 0])
    for x in range(1, width):
        circ.append(is_black[-1, x])
    for y in reversed(range(0, height - 1)):
        circ.append(is_black[y, -1])
    for x in reversed(range(1, width - 1)):
        circ.append(is_black[0, x])
    circ_switching = []
    for i in range(len(circ)):
        circ_switching.append(circ[i] != circ[(i + 1) % len(circ)])
    solver.ensure(count_true(circ_switching) <= 2)

    for y in range(height):
        for x in range(width):
            if problem[y][x] == 1:
                solver.ensure(~is_black[y, x])
            elif problem[y][x] == 2:
                solver.ensure(is_black[y, x])

    is_sat = solver.solve()
    return is_sat, is_black


def generate_yinyang(
    height, width, disallow_adjacent=False, no_clue_on_circumference=False, verbose=False
):
    def pretest(problem):
        for y in range(height):
            if problem[y][0] != 0 or problem[y][-1] != 0:
                return False
        for x in range(width):
            if problem[0][x] != 0 or problem[-1][x] != 0:
                return False
        return True

    generated = generate_problem(
        lambda problem: solve_yinyang(height, width, problem),
        builder_pattern=ArrayBuilder2D(
            height, width, range(0, 3), default=0, disallow_adjacent=disallow_adjacent
        ),
        clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=5),
        pretest=pretest if no_clue_on_circumference else None,
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        # generated example: http://pzv.jp/p.html?yinyang/6/6/0j40j0060220
        height = 6
        width = 6
        problem = [
            [0, 0, 0, 2, 0, 1],
            [0, 1, 1, 0, 0, 0],
            [2, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 2, 0],
            [0, 0, 0, 0, 0, 2],
            [0, 0, 2, 0, 0, 0],
        ]
        is_sat, is_black = solve_yinyang(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", True: "#", False: "o"}))
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                problem = generate_yinyang(height, width, disallow_adjacent=False, verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem, {0: ".", 1: "o", 2: "#"}), flush=True)
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
