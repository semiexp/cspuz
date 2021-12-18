import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, Choice


def solve_creek(height, width, problem):
    solver = Solver()
    is_white = solver.bool_array((height, width))
    solver.add_answer_key(is_white)
    graph.active_vertices_connected(solver, is_white)
    for y in range(0, height + 1):
        for x in range(0, width + 1):
            if problem[y][x] >= 0:
                solver.ensure(
                    count_true(
                        ~is_white[
                            max(y - 1, 0) : min(y + 1, height), max(x - 1, 0) : min(x + 1, width)
                        ]
                    )
                    == problem[y][x]
                )
    is_sat = solver.solve()
    return is_sat, is_white


def generate_creek(height, width, no_easy=False, verbose=False):
    pattern = []
    for y in range(height + 1):
        row = []
        for x in range(width + 1):
            nmax = (1 if y in (0, height) else 2) * (1 if x in (0, width) else 2)
            row.append(
                Choice(
                    [-1] + list(range(1 if no_easy else 0, nmax if no_easy else nmax + 1)),
                    default=-1,
                )
            )
        pattern.append(row)

    def pretest(problem):
        if not no_easy:
            return True
        for y in range(height + 1):
            for x in range(width + 1):
                if y < height and (problem[y][x], problem[y + 1][x]) in ((1, 3), (3, 1)):
                    return False
                if x < width and (problem[y][x], problem[y][x + 1]) in ((1, 3), (3, 1)):
                    return False
        return True

    generated = generate_problem(
        lambda problem: solve_creek(height, width, problem),
        builder_pattern=pattern,
        clue_penalty=lambda problem: count_non_default_values(problem, default=-1, weight=3),
        pretest=pretest,
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        pass
    else:
        height, width = map(int, sys.argv[1:])
        cspuz.config.solver_timeout = 1200.0
        while True:
            try:
                problem = generate_creek(height, width, no_easy=True, verbose=True)
                if problem is not None:
                    print(
                        util.stringify_array(problem, lambda x: "." if x == -1 else str(x)),
                        flush=True,
                    )
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
