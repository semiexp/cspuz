import argparse
import sys

from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.grid_frame import BoolGridFrame
from cspuz.puzzle import util
from cspuz.generator import generate_problem, count_non_default_values, Choice
from cspuz.problem_serializer import (
    Combinator,
    Grid,
    OneOf,
    Spaces,
    deserialize_problem_as_url,
    serialize_problem_as_url,
)


def solve_yajilin(height, width, problem):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height - 1, width - 1)
    is_passed = graph.active_edges_single_cycle(solver, grid_frame)
    black_cell = solver.bool_array((height, width))
    graph.active_vertices_not_adjacent(solver, black_cell)
    solver.add_answer_key(grid_frame)
    solver.add_answer_key(black_cell)

    for y in range(height):
        for x in range(width):
            if problem[y][x] != "..":
                # clue
                solver.ensure(~is_passed[y, x])
                solver.ensure(~black_cell[y, x])

                if problem[y][x] == "??":
                    continue
                if problem[y][x][0] == "^":
                    solver.ensure(count_true(black_cell[0:y, x]) == int(problem[y][x][1:]))
                elif problem[y][x][0] == "v":
                    solver.ensure(
                        count_true(black_cell[(y + 1) : height, x]) == int(problem[y][x][1:])
                    )
                elif problem[y][x][0] == "<":
                    solver.ensure(count_true(black_cell[y, 0:x]) == int(problem[y][x][1:]))
                elif problem[y][x][0] == ">":
                    solver.ensure(
                        count_true(black_cell[y, (x + 1) : width]) == int(problem[y][x][1:])
                    )
            else:
                solver.ensure(is_passed[y, x] != black_cell[y, x])

    is_sat = solver.solve()
    return is_sat, grid_frame, black_cell


def generate_yajilin(height, width, no_zero=False, no_max_clue=False, verbose=False):
    choices = []
    for y in range(height):
        row = []
        for x in range(width):
            c = [".."]
            for i in range(1 if no_zero else 0, (y + 3) // 2 - (1 if no_max_clue else 0)):
                c.append("^{}".format(i))
            for i in range(1 if no_zero else 0, (x + 3) // 2 - (1 if no_max_clue else 0)):
                c.append("<{}".format(i))
            for i in range(1 if no_zero else 0, (height - y + 2) // 2 - (1 if no_max_clue else 0)):
                c.append("v{}".format(i))
            for i in range(1 if no_zero else 0, (width - x + 2) // 2 - (1 if no_max_clue else 0)):
                c.append(">{}".format(i))
            row.append(Choice(c, ".."))
        choices.append(row)
    generated = generate_problem(
        lambda problem: solve_yajilin(height, width, problem),
        builder_pattern=choices,
        clue_penalty=lambda problem: count_non_default_values(problem, default="..", weight=20),
        verbose=verbose,
    )
    return generated


class YajilinClue(Combinator):
    def __init__(self):
        super().__init__()

    def serialize(self, env, data, idx):
        if idx >= len(data):
            return None
        if data[idx] == "..":
            return None
        value = data[idx]
        DIR_MAP = {"^": 1, "v": 2, "<": 3, ">": 4}
        dir = DIR_MAP[value[0]]
        n = int(value[1:])
        return 1, f"{dir}{hex(n)[2:]}"

    def deserialize(self, env, data, idx):
        if idx + 1 >= len(data):
            return None
        dir = data[idx]
        if dir == "0":
            return 2, ["??"]
        if dir not in "1234":
            return None
        DIR_MAP = {1: "^", 2: "v", 3: "<", 4: ">"}
        n = data[idx + 1]
        if n == ".":
            return 2, ["??"]
        return 2, [f"{DIR_MAP[int(dir)]}{int(n, 16)}"]


YAJILIN_COMBINATOR = Grid(OneOf(YajilinClue(), Spaces("..", "a")))


def serialize_yajilin(problem):
    height = len(problem)
    width = len(problem[0])
    return serialize_problem_as_url(YAJILIN_COMBINATOR, "yajilin", height, width, problem)


def deserialize_yajilin(url):
    return deserialize_problem_as_url(YAJILIN_COMBINATOR, url, allowed_puzzles="yajilin")


def _main():
    if len(sys.argv) == 1:
        # https://twitter.com/semiexp/status/1206956338556764161
        height = 10
        width = 10
        problem = [
            ["..", "..", "..", "..", "..", "..", "..", "..", "..", ".."],
            ["..", "..", "..", "..", "..", "..", "..", "..", "..", ".."],
            ["..", "..", "v0", "..", "..", ">2", "..", "..", "..", ".."],
            ["..", "..", "..", "..", "..", "..", "..", "..", "..", ".."],
            ["..", "..", "..", "..", "..", "..", "..", "..", "..", ".."],
            ["..", "..", "..", "..", "..", "..", "..", "..", "^1", ".."],
            ["..", "..", "..", "..", "..", "..", "..", "..", "..", ".."],
            ["..", "..", "^0", "..", "^3", "..", "..", ">1", "..", ".."],
            ["..", "..", "..", "..", "..", "..", "..", "..", "..", ".."],
            ["..", "..", "..", "..", "..", "..", "..", ">0", "..", ".."],
        ]
        is_sat, is_line, black_cell = solve_yajilin(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_grid_frame(is_line))
    else:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-h", "--height", type=int, required=True)
        parser.add_argument("-w", "--width", type=int, required=True)
        parser.add_argument("--no-zero", action="store_true")
        parser.add_argument("--no-max-clue", action="store_true")
        parser.add_argument("-v", "--verbose", action="store_true")
        args = parser.parse_args()

        height = args.height
        width = args.width
        no_zero = args.no_zero
        no_max_clue = args.no_max_clue
        verbose = args.verbose
        while True:
            problem = generate_yajilin(
                height, width, no_zero=no_zero, no_max_clue=no_max_clue, verbose=verbose
            )
            if problem is not None:
                print(util.stringify_array(problem, str), flush=True)
                print(flush=True)


if __name__ == "__main__":
    _main()
