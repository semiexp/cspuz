import sys
from collections import defaultdict
import subprocess

import numpy as np

import cspuz
from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.generator import (
    generate_problem,
    ArrayBuilder2D,
    SegmentationBuilder2D,
    count_non_default_values,
)


def solve_nanro(height, width, blocks, num):
    block_id = [[-1 for _ in range(width)] for _ in range(height)]
    for i, block in enumerate(blocks):
        for y, x in block:
            block_id[y][x] = i
    solver = Solver()
    answer = []
    has_num = solver.bool_array((height, width))
    for y in range(height):
        row = []
        for x in range(width):
            v = solver.int_var(0, len(blocks[block_id[y][x]]))
            solver.add_answer_key(v)
            solver.ensure(has_num[y, x] == (v != 0))
            row.append(v)
        answer.append(row)
    graph.active_vertices_connected(solver, has_num)

    for i, block in enumerate(blocks):
        nonempty = solver.int_var(1, len(block))
        solver.ensure(nonempty == count_true(answer[y][x] != 0 for y, x in block))
        for y, x in block:
            solver.ensure((answer[y][x] == 0) | (answer[y][x] == nonempty))
    for y in range(height):
        for x in range(width):
            if num[y][x] > 0:
                solver.ensure(answer[y][x] == num[y][x])
            if y < height - 1 and x < width - 1:
                solver.ensure(
                    (answer[y][x] == 0)
                    | (answer[y][x + 1] == 0)
                    | (answer[y + 1][x] == 0)
                    | (answer[y + 1][x + 1] == 0)
                )
            if y < height - 1 and block_id[y][x] != block_id[y + 1][x]:
                solver.ensure(
                    (answer[y][x] == 0)
                    | (answer[y + 1][x] == 0)
                    | (answer[y][x] != answer[y + 1][x])
                )
            if x < width - 1 and block_id[y][x] != block_id[y][x + 1]:
                solver.ensure(
                    (answer[y][x] == 0)
                    | (answer[y][x + 1] == 0)
                    | (answer[y][x] != answer[y][x + 1])
                )

    is_sat = solver.solve()
    return is_sat, answer


def generate_nanro(height, width, max_block_size=8, verbose=False):
    def is_unique(answer):
        for y in range(height):
            for x in range(width):
                if answer[y][x].sol is None:
                    return False
        return True

    def score(answer):
        ret = 0
        for y in range(height):
            for x in range(width):
                if answer[y][x].sol is not None:
                    ret += 1
        return ret

    def pretest(problem):
        blocks, num = problem
        cells = [[None for _ in range(width)] for _ in range(height)]
        for i, block in enumerate(blocks):
            n = None
            for y, x in block:
                if num[y][x] != 0:
                    if n is not None:
                        return False
                    n = num[y][x]
            if n is not None:
                lim = len(block)
                block_set = set(block)
                for y, x in block_set:
                    if (
                        (y + 1, x) in block_set
                        and (y, x + 1) in block_set
                        and (y + 1, x + 1) in block_set
                    ):
                        lim -= 1
                if n >= lim - 1:
                    return False
                for y, x in block:
                    cells[y][x] = (i, n)
        for y in range(height):
            for x in range(width):
                if cells[y][x] is None:
                    continue
                i, n = cells[y][x]
                if y < height - 1 and cells[y + 1][x] is not None:
                    j, m = cells[y + 1][x]
                    if i != j and n == m:
                        return False
                if x < width - 1 and cells[y][x + 1] is not None:
                    j, m = cells[y][x + 1]
                    if i != j and n == m:
                        return False
        for block in blocks:
            for y, x in block:
                if num[y][x] != 2:
                    continue
                if (
                    (y == 0 or (y - 1, x) in block)
                    and (x == 0 or (y, x - 1) in block)
                    and (y == height - 1 or (y + 1, x) in block)
                    and (x == width - 1 or (y, x + 1) in block)
                ):
                    return False
                if len(block) >= 6:
                    return False
        return True

    generated = generate_problem(
        lambda problem: solve_nanro(height, width, *problem),
        builder_pattern=(
            SegmentationBuilder2D(
                height,
                width,
                min_num_blocks=height * width // 6,
                max_num_blocks=None,
                min_block_size=2,
                max_block_size=max_block_size,
                allow_unmet_constraints_first=False,
            ),
            ArrayBuilder2D(
                height, width, choice=[0] + list(range(2, 7)), default=0, disallow_adjacent=True
            ),
        ),
        clue_penalty=lambda problem: count_non_default_values(problem[1], default=0, weight=6),
        uniqueness=is_unique,
        score=score,
        solve_initial_problem=True,
        pretest=pretest,
        verbose=verbose,
    )
    return generated


def problem_to_pzv_url(height, width, blocks, num):
    def convert_binary_seq(s):
        ret = ""
        for i in range((len(s) + 4) // 5):
            v = 0
            for j in range(5):
                if i * 5 + j < len(s) and s[i * 5 + j] == 1:
                    v += 2 ** (4 - j)
            ret += np.base_repr(v, 32).lower()
        return ret

    block_id = [[-1 for _ in range(width)] for _ in range(height)]
    for i, block in enumerate(blocks):
        for y, x in block:
            block_id[y][x] = i
    s = []
    for y in range(height):
        for x in range(width - 1):
            s.append(1 if block_id[y][x] != block_id[y][x + 1] else 0)
    ret = convert_binary_seq(s)
    s = []
    for y in range(height - 1):
        for x in range(width):
            s.append(1 if block_id[y][x] != block_id[y + 1][x] else 0)
    ret += convert_binary_seq(s)

    contiguous_empty_cells = 0
    for y in range(height):
        for x in range(width):
            if num[y][x] == 0:
                if contiguous_empty_cells == 20:
                    ret += "z"
                    contiguous_empty_cells = 1
                else:
                    contiguous_empty_cells += 1
            else:
                if contiguous_empty_cells > 0:
                    ret += np.base_repr(contiguous_empty_cells + 15, 36).lower()
                    contiguous_empty_cells = 0
                if num[y][x] < 16:
                    ret += np.base_repr(num[y][x], 16).lower()
                else:
                    ret += "-" + np.base_repr(num[y][x], 16).lower()
    if contiguous_empty_cells > 0:
        ret += np.base_repr(contiguous_empty_cells + 15, 36).lower()

    return "http://pzv.jp/p.html?nanro/{}/{}/{}".format(width, height, ret)


def _main():
    if len(sys.argv) == 1:
        # http://pzv.jp/p.html?nanro/8/8/j9db9n5v9i6ge9g1de1h9rr05j4l2k5q5k2h4n3j3p
        height = 8
        width = 8
        b = [
            "01112334",
            "00022344",
            "05522344",
            "05552664",
            "75888664",
            "7579866a",
            "7779bbba",
            "ccccbdda",
        ]
        blocks = defaultdict(list)
        for y in range(height):
            for x in range(width):
                blocks[b[y][x]].append((y, x))
        blocks = list(blocks.values())

        num = [
            [5, 0, 0, 0, 0, 4, 0, 0],
            [0, 0, 0, 0, 2, 0, 0, 0],
            [0, 0, 5, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 5, 0],
            [0, 0, 0, 0, 2, 0, 0, 4],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [3, 0, 0, 0, 0, 3, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        is_sat, answer = solve_nanro(height, width, blocks, num)
        print("has answer:", is_sat)
        if is_sat:
            for y in range(height):
                for x in range(width):
                    if answer[y][x].sol is None:
                        print("?", end=" ")
                    elif answer[y][x].sol == 0:
                        print(".", end=" ")
                    else:
                        print(answer[y][x].sol, end=" ")
                print()
            print()
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                gen = generate_nanro(height, width, verbose=True)
                if gen is not None:
                    print(gen)
                    blocks, num = gen
                    print(problem_to_pzv_url(height, width, blocks, num), flush=True)
            except subprocess.TimeoutExpired:
                print("timeout", file=sys.stderr)


if __name__ == "__main__":
    _main()
