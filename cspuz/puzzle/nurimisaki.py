import sys

from cspuz import Solver, graph
from cspuz.constraints import count_true, fold_and, fold_or
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D
from cspuz.problem_serializer import (
    Grid,
    OneOf,
    Spaces,
    HexInt,
    Dict,
    serialize_problem_as_url,
    deserialize_problem_as_url,
)


def solve_nurimisaki(height, width, problem):
    solver = Solver()
    is_white = solver.bool_array((height, width))
    solver.add_answer_key(is_white)

    graph.active_vertices_connected(solver, is_white)

    solver.ensure(is_white[:-1, :-1] | is_white[1:, :-1] | is_white[:-1, 1:] | is_white[1:, 1:])
    solver.ensure(~(is_white[:-1, :-1] & is_white[1:, :-1] & is_white[:-1, 1:] & is_white[1:, 1:]))

    for y in range(height):
        for x in range(width):
            if problem[y][x] == -1:
                solver.ensure(is_white[y, x].then(count_true(is_white.four_neighbors(y, x)) != 1))
            else:
                solver.ensure(is_white[y, x])
                solver.ensure(count_true(is_white.four_neighbors(y, x)) == 1)
                if problem[y][x] != 0:
                    n = problem[y][x]
                    cand = []
                    if y == n - 1:
                        cand.append(fold_and(is_white[(y - n + 1) : y, x]))
                    elif y > n - 1:
                        cand.append(fold_and(is_white[(y - n + 1) : y, x], ~is_white[y - n, x]))
                    if y == height - n:
                        cand.append(fold_and(is_white[(y + 1) : (y + n), x]))
                    elif y < height - n:
                        cand.append(fold_and(is_white[(y + 1) : (y + n), x], ~is_white[y + n, x]))
                    if x == n - 1:
                        cand.append(fold_and(is_white[y, (x - n + 1) : x]))
                    elif x > n - 1:
                        cand.append(fold_and(is_white[y, (x - n + 1) : x], ~is_white[y, x - n]))
                    if x == width - n:
                        cand.append(fold_and(is_white[y, (x + 1) : (x + n)]))
                    elif x < width - n:
                        cand.append(fold_and(is_white[y, (x + 1) : (x + n)], ~is_white[y, x + n]))
                    solver.ensure(fold_or(cand))

    is_sat = solver.solve()
    return is_sat, is_white


def generate_fillomino(height, width, verbose=False):
    generated = generate_problem(
        lambda problem: solve_nurimisaki(height, width, problem),
        builder_pattern=ArrayBuilder2D(height, width, [-1, 0], default=-1),
        clue_penalty=lambda problem: count_non_default_values(problem, default=-1, weight=7),
        verbose=verbose,
    )
    return generated


NURIMISAKI_COMBINATOR = Grid(OneOf(Dict([0], ["."]), Spaces(-1, "g"), HexInt()))


def serialize_nurimisaki(problem):
    height = len(problem)
    width = len(problem[0])
    return serialize_problem_as_url(NURIMISAKI_COMBINATOR, "nurimisaki", height, width, problem)


def deserialize_nurimisaki(url):
    return deserialize_problem_as_url(NURIMISAKI_COMBINATOR, url, allowed_puzzles="nurimisaki")


def _main():
    if len(sys.argv) == 1:
        # https://twitter.com/semiexp/status/1168898897424633856
        height = 10
        width = 10
        # fmt: off
        problem = [
            [-1, -1, -1, -1,  3, -1, -1, -1, -1, -1],  # noqa: E201, E241
            [-1,  3, -1, -1, -1, -1, -1, -1, -1, -1],  # noqa: E201, E241
            [-1, -1, -1, -1, -1, -1, -1, -1,  2, -1],  # noqa: E201, E241
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],  # noqa: E201, E241
            [-1, -1, -1,  2, -1, -1, -1, -1, -1, -1],  # noqa: E201, E241
            [-1, -1, -1, -1,  0, -1,  2, -1, -1, -1],  # noqa: E201, E241
            [-1,  2, -1, -1, -1, -1, -1, -1, -1, -1],  # noqa: E201, E241
            [-1, -1, -1, -1, -1, -1, -1, -1, -1,  2],  # noqa: E201, E241
            [-1, -1, -1, -1, -1,  2, -1, -1, -1, -1],  # noqa: E201, E241
            [-1, -1, -1, -1,  3, -1, -1, -1, -1, -1],  # noqa: E201, E241
        ]
        # fmt: on
        is_sat, ans = solve_nurimisaki(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(ans, {None: "?", True: ".", False: "#"}))
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            problem = generate_fillomino(height, width, verbose=True)
            if problem is not None:
                print(util.stringify_array(problem, {-1: ".", 0: "O"}), flush=True)
                print(flush=True)


if __name__ == "__main__":
    _main()
