import argparse
import random
import math
import sys

import svgwrite

from cspuz import Solver, graph
from cspuz.constraints import count_true, fold_or
from cspuz.puzzle import util
from cspuz.generator import generate_problem, Choice


def solve_compass(height, width, problem):
    solver = Solver()
    roots = map(lambda x: (x[0], x[1]), problem)
    division = solver.int_array((height, width), 0, len(problem) - 1)
    graph.division_connected(solver, division, len(problem), roots=roots)
    solver.add_answer_key(division)
    for i, (y, x, up, lf, dw, rg) in enumerate(problem):
        solver.ensure(division[y, x] == i)
        if up >= 0:
            solver.ensure(count_true(division[:y, :] == i) == up)
        if dw >= 0:
            solver.ensure(count_true(division[(y + 1) :, :] == i) == dw)
        if lf >= 0:
            solver.ensure(count_true(division[:, :x] == i) == lf)
        if rg >= 0:
            solver.ensure(count_true(division[:, (x + 1) :] == i) == rg)
    is_sat = solver.solve()

    return is_sat, division


def check_problem_constraints(height, width, problem, flg, circ=-1):
    if flg is None and circ == -1:
        return True
    for clue in problem:
        a = 0
        for i in range(2, 6):
            if clue[i] >= 0:
                a += 1
    solver = Solver()
    roots = map(lambda x: (x[0], x[1]), problem)
    division = solver.int_array((height, width), 0, len(problem) - 1)
    graph.division_connected(solver, division, len(problem), roots=roots)
    solver.add_answer_key(division)
    for i, (y, x, up, lf, dw, rg) in enumerate(problem):
        solver.ensure(division[y, x] == i)
        if flg is not None and flg[i] is not None and flg[i] >= 0:
            solver.ensure(count_true(division == i) >= flg[i])
        if up >= 0:
            solver.ensure(count_true(division[:y, :] == i) == up)
        if dw >= 0:
            solver.ensure(count_true(division[(y + 1) :, :] == i) == dw)
        if lf >= 0:
            solver.ensure(count_true(division[:, :x] == i) == lf)
        if rg >= 0:
            solver.ensure(count_true(division[:, (x + 1) :] == i) == rg)

    # encircling constraint
    if circ != -1:
        col = solver.bool_array((height, width))
        solver.ensure(col[0, :])
        solver.ensure(col[-1, :])
        solver.ensure(col[:, 0])
        solver.ensure(col[:, -1])
        solver.ensure(
            ((division[1:, :] != circ) & (division[:-1, :] != circ)).then(
                col[1:, :] == col[:-1, :]
            )
        )
        solver.ensure(
            ((division[:, 1:] != circ) & (division[:, :-1] != circ)).then(
                col[:, 1:] == col[:, :-1]
            )
        )
        solver.ensure(
            ((division[1:, 1:] != circ) & (division[:-1, :-1] != circ)).then(
                col[1:, 1:] == col[:-1, :-1]
            )
        )
        solver.ensure(
            ((division[:-1, 1:] != circ) & (division[1:, :-1] != circ)).then(
                col[:-1, 1:] == col[1:, :-1]
            )
        )
        solver.ensure(fold_or(col & (division != circ)))
        solver.ensure(fold_or((~col) & (division != circ)))

    sat = solver.find_answer()
    return sat


def compute_score(division):
    score = 0
    for v in division[:, :]:
        if v.sol is not None:
            score += 1
    return score


def generate_compass(
    height,
    width,
    pos,
    min_clue,
    max_clue,
    prefer_large_blocks=None,
    encircling=False,
    verbose=False,
):
    choice_base = Choice([-1] + list(range(min_clue, max_clue + 1)), -1)
    pattern = []
    for y, x in pos:
        pattern.append(
            [
                y,
                x,
                -1 if y < 2 else choice_base,
                -1 if x < 2 else choice_base,
                -1 if y >= height - 2 else choice_base,
                -1 if x >= width - 2 else choice_base,
            ]
        )
    if prefer_large_blocks is not None:
        flg = [prefer_large_blocks if random.random() < 0.9 else -1 for _ in range(len(pos))]
    else:
        flg = None
    if encircling:
        circ = random.randint(0, len(pos) - 1)
    else:
        circ = -1
    if prefer_large_blocks or encircling:

        def pretest(problem):
            return check_problem_constraints(height, width, problem, flg, circ)

    else:
        pretest = None

    def penalty(problem):
        ret = 0
        for i in range(len(problem)):
            for j in range(2, 6):
                if problem[i][j] != -1:
                    ret += 3
        return ret

    generated = generate_problem(
        lambda problem: solve_compass(height, width, problem),
        builder_pattern=pattern,
        clue_penalty=penalty,
        pretest=pretest,
        verbose=verbose,
    )
    return generated


def to_puzz_link_url(height, width, pos):
    problem = [[None for _ in range(width)] for _ in range(height)]
    for (y, x, u, l, d, r) in pos:
        problem[y][x] = tuple(map(lambda x: "." if x == -1 else x, (u, d, l, r)))
    return "https://puzz.link/p?compass/{}/{}/{}".format(width, height, util.encode_array(problem))


def parse_puzz_link_url(url):
    height, width, body = url.split("/")[-3:]
    height = int(height)
    width = int(width)

    pos = 0
    i = 0
    res = []
    while i < len(body):
        if ord(body[i]) >= ord("g"):
            pos += ord(body[i]) - ord("f")
            i += 1
        else:
            num = [-1, -1, -1, -1]
            for j in range(4):
                if body[i] == "-":
                    num[j] = int(body[i + 1 : i + 3], 16)
                    i += 3
                else:
                    if body[i] != ".":
                        num[j] = int(body[i], 16)
                    i += 1
            res.append((pos // width, pos % width, num[0], num[2], num[1], num[3]))
            pos += 1
    return height, width, res


def generate_placement(height, width, nlo, nhi, symmetry=False):
    while True:
        has_clue = [[False for _ in range(width)] for _ in range(height)]
        n = random.randint(nlo, nhi) // 2 * 2
        pos = []
        while n > 0:
            y = random.randint(0, height - 1)
            x = random.randint(0, width - 1)
            if has_clue[y][x]:
                continue
            if y == 0 or x == 0 or y == height - 1 or x == width - 1:
                continue
            score = 0
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    y2 = y + dy
                    x2 = x + dx
                    if 0 <= y2 < height and 0 <= x2 < width and has_clue[y2][x2]:
                        if abs(dy) + abs(dx) <= 2:
                            score += 1
                        else:
                            score += 0.5
            if random.random() > math.exp(-score / 1.5):
                continue
            has_clue[y][x] = True
            pos.append((y, x))
            n -= 1
            if symmetry:
                has_clue[height - 1 - y][width - 1 - x] = True
                pos.append((height - 1 - y, width - 1 - x))
                n -= 1
        flg = False
        window = 4
        for y in range(height - window + 1):
            for x in range(width - window + 1):
                cnt = 0
                for dy in range(window):
                    for dx in range(window):
                        if has_clue[y + dy][x + dx]:
                            cnt += 1
                if cnt == 0:
                    flg = True
        if flg:
            continue
        return pos


def emit_svg(height, width, problem):
    boundary = 5
    cell_size = 50

    dwg = svgwrite.Drawing(
        size=(boundary * 2 + cell_size * width, boundary * 2 + cell_size * height)
    )

    grid_style = {"stroke": "gray", "stroke_width": 1, "stroke_dasharray": cell_size / 12}
    border_style = {"stroke": "black", "stroke_width": 4}
    compass_style = {"stroke": "black", "stroke_width": 1}
    text_style_one = {
        "fill": "black",
        "font_size": cell_size * 0.4,
        "text_anchor": "middle",
        "dominant_baseline": "mathematical",
        "font_family": "Helvetica",
    }
    text_style_two = {
        "fill": "black",
        "font_size": cell_size * 0.4,
        "text_anchor": "middle",
        "dominant_baseline": "mathematical",
        "textLength": cell_size * 0.3,
        "lengthAdjust": "spacingAndGlyphs",
        "font_family": "Helvetica",
    }
    # grid
    for y in range(1, height):
        dwg.add(
            dwg.line(
                (boundary, boundary + y * cell_size),
                (boundary + width * cell_size, boundary + y * cell_size),
                **grid_style
            )
        )
    for x in range(1, width):
        dwg.add(
            dwg.line(
                (boundary + x * cell_size, boundary),
                (boundary + x * cell_size, boundary + height * cell_size),
                **grid_style
            )
        )

    # border
    dwg.add(
        dwg.line(
            (boundary - 2, boundary), (boundary + width * cell_size + 2, boundary), **border_style
        )
    )
    dwg.add(
        dwg.line(
            (boundary - 2, boundary + height * cell_size),
            (boundary + width * cell_size + 2, boundary + height * cell_size),
            **border_style
        )
    )
    dwg.add(
        dwg.line(
            (boundary, boundary - 2), (boundary, boundary + height * cell_size + 2), **border_style
        )
    )
    dwg.add(
        dwg.line(
            (boundary + width * cell_size, boundary - 2),
            (boundary + width * cell_size, boundary + height * cell_size + 2),
            **border_style
        )
    )

    # clues
    for (y, x, up, lf, dw, rg) in problem:
        dwg.add(
            dwg.line(
                (boundary + x * cell_size, boundary + y * cell_size),
                (boundary + (x + 1) * cell_size, boundary + (y + 1) * cell_size),
                **compass_style
            )
        )
        dwg.add(
            dwg.line(
                (boundary + (x + 1) * cell_size, boundary + y * cell_size),
                (boundary + x * cell_size, boundary + (y + 1) * cell_size),
                **compass_style
            )
        )
        center_y = boundary + (y + 0.5) * cell_size
        center_x = boundary + (x + 0.5) * cell_size
        if up >= 0:
            dwg.add(
                dwg.text(
                    str(up),
                    x=[center_x],
                    y=[center_y - cell_size * 0.27],
                    **(text_style_two if up >= 10 else text_style_one)
                )
            )
        if lf >= 0:
            dwg.add(
                dwg.text(
                    str(lf),
                    x=[center_x - cell_size * 0.3],
                    y=[center_y],
                    **(text_style_two if lf >= 10 else text_style_one)
                )
            )
        if dw >= 0:
            dwg.add(
                dwg.text(
                    str(dw),
                    x=[center_x],
                    y=[center_y + cell_size * 0.3],
                    **(text_style_two if dw >= 10 else text_style_one)
                )
            )
        if rg >= 0:
            dwg.add(
                dwg.text(
                    str(rg),
                    x=[center_x + cell_size * 0.3],
                    y=[center_y],
                    **(text_style_two if rg >= 10 else text_style_one)
                )
            )
    return dwg


def _main():
    if len(sys.argv) == 1:
        # generated example
        # https://puzz.link/p?compass/5/5/m..1.i25.1g53..i1..1m
        height = 5
        width = 5
        problem = [
            (1, 2, -1, 1, -1, -1),
            (2, 1, 2, -1, 5, 1),
            (2, 3, 5, -1, 3, -1),
            (3, 2, 1, -1, -1, 1),
        ]
        is_sat, ans = solve_compass(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(ans, str))
    else:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-h", "--height", type=int, required=True)
        parser.add_argument("-w", "--width", type=int, required=True)
        parser.add_argument("--min-num-blocks", type=int, required=True)
        parser.add_argument("--max-num-blocks", type=int, required=True)
        parser.add_argument("--min-clue", type=int, required=True)
        parser.add_argument("--max-clue", type=int, required=True)
        parser.add_argument("--prefer-large-blocks", type=int)
        parser.add_argument("--encircling-block", action="store_true")
        parser.add_argument("--symmetry", action="store_true")
        parser.add_argument("-v", "--verbose", action="store_true")
        args = parser.parse_args()

        height = args.height
        width = args.width
        min_num_blocks = args.min_num_blocks
        max_num_blocks = args.max_num_blocks
        min_clue = args.min_clue or 1
        max_clue = args.max_clue or height * width
        prefer_large_blocks = args.prefer_large_blocks
        enclircling_block = args.encircling_block
        symmetry = args.symmetry
        verbose = args.verbose
        while True:
            pos = generate_placement(
                height, width, min_num_blocks, max_num_blocks, symmetry=symmetry
            )
            problem = generate_compass(
                height,
                width,
                pos,
                min_clue,
                max_clue,
                prefer_large_blocks=prefer_large_blocks,
                encircling=enclircling_block,
                verbose=verbose,
            )
            if problem is not None:
                print(to_puzz_link_url(height, width, problem), flush=True)


if __name__ == "__main__":
    _main()
