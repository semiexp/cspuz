import random
import math
import sys

import numpy as np

from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.puzzle import util


def solve_nurimaze(height, width, wall_vertical, wall_horizontal, mark, start, goal):
    solver = Solver()
    is_white = solver.bool_array((height, width))
    graph.active_vertices_connected(solver, is_white, acyclic=True)
    solver.add_answer_key(is_white)

    solver.ensure(is_white[:-1, :-1] | is_white[:-1, 1:] | is_white[1:, :-1] | is_white[1:, 1:])
    solver.ensure(~(is_white[:-1, :-1] & is_white[:-1, 1:] & is_white[1:, :-1] & is_white[1:, 1:]))
    path = solver.bool_array((height, width))
    solver.ensure(path.then(is_white))
    for y in range(height):
        for x in range(width):
            if x < width - 1 and not wall_vertical[y][x]:
                solver.ensure(is_white[y, x] == is_white[y, x + 1])
            if y < height - 1 and not wall_horizontal[y][x]:
                solver.ensure(is_white[y, x] == is_white[y + 1, x])
            if (y, x) == start or (y, x) == goal:
                solver.ensure(path[y, x])
                solver.ensure(count_true(path.four_neighbors(y, x)) == 1)
            else:
                solver.ensure(path[y, x].then(count_true(path.four_neighbors(y, x)) == 2))
            if mark[y][x] != 0:
                solver.ensure(is_white[y, x])
            if mark[y][x] == 1:  # pass
                solver.ensure(path[y, x])
            elif mark[y][x] == 2:
                solver.ensure(~path[y, x])

    is_sat = solver.solve()
    return is_sat, is_white


def compute_score(ans):
    score = 0
    for v in ans:
        if v.sol is not None:
            score += 1
    return score


def check_isolatedness(height, width, wall_vertical, wall_horizontal, mark, start, goal):
    for y in range(height):
        for x in range(width):
            if mark[y][x] != 0 or (y, x) == start or (y, x) == goal:
                if y > 0 and (mark[y - 1][x] != 0 or wall_horizontal[y - 1][x] == 0):
                    return False
                if y < height - 1 and (mark[y + 1][x] != 0 or wall_horizontal[y][x] == 0):
                    return False
                if x > 0 and (mark[y][x - 1] != 0 or wall_vertical[y][x - 1] == 0):
                    return False
                if x < width - 1 and (mark[y][x + 1] != 0 or wall_vertical[y][x] == 0):
                    return False
    return True


def generate_nurimaze(height, width, verbose=False, isolated_clues=False):
    wall_vertical = [[1 for _ in range(width - 1)] for _ in range(height)]
    wall_horizontal = [[1 for _ in range(width)] for _ in range(height - 1)]
    mark = [[0 for _ in range(width)] for _ in range(height)]
    while True:
        sy = random.randint(0, height - 1)
        sx = random.randint(0, width - 1)
        gy = random.randint(0, height - 1)
        gx = random.randint(0, width - 1)
        if abs(sy - gy) + abs(sx - gx) >= 2:
            start = (sy, sx)
            goal = (gy, gx)
            break
    score = 0
    temperature = 3.0
    fully_solved_score = height * width

    for step in range(height * width * 10):
        cand = []
        for y in range(height):
            for x in range(width):
                if x < width - 1:
                    cand.append((0, y, x, 1 - wall_vertical[y][x]))
                if y < height - 1:
                    cand.append((1, y, x, 1 - wall_horizontal[y][x]))
                for n in range(3):
                    if n != 0 and (y, x) in [start, goal]:
                        continue
                    if mark[y][x] != n:
                        cand.append((2, y, x, n))
                if mark[y][x] == 0:
                    if (y, x) != start:
                        cand.append((3, (y, x)))
                    if (y, x) != goal:
                        cand.append((4, (y, x)))
        random.shuffle(cand)

        for ty, *val in cand:
            if ty <= 2:
                y, x, n = val
                if ty == 0:
                    n_prev = wall_vertical[y][x]
                    wall_vertical[y][x] = n
                elif ty == 1:
                    n_prev = wall_horizontal[y][x]
                    wall_horizontal[y][x] = n
                elif ty == 2:
                    n_prev = mark[y][x]
                    mark[y][x] = n
            elif ty == 3:
                n_prev = start
                start = val[0]
            elif ty == 4:
                n_prev = goal
                goal = val[0]

            if isolated_clues and not check_isolatedness(
                height, width, wall_vertical, wall_horizontal, mark, start, goal
            ):
                sat, is_white = False, None
            else:
                sat, is_white = solve_nurimaze(
                    height, width, wall_vertical, wall_horizontal, mark, start, goal
                )
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(is_white)
                if raw_score == fully_solved_score:
                    print(wall_vertical, wall_horizontal, mark, start, goal)
                    # print(util.stringify_array(is_white, {
                    #     None: '?',
                    #     True: '.',
                    #     False: '#'
                    # }))
                    return wall_vertical, wall_horizontal, mark, start, goal
                clue_score = 0
                for y2 in range(height):
                    for x2 in range(width):
                        if y2 < height - 1 and wall_horizontal[y2][x2] != 1:
                            clue_score += 2
                        if x2 < width - 1 and wall_vertical[y2][x2] != 1:
                            clue_score += 2
                        if mark[y2][x2] != 0:
                            clue_score += 5

                score_next = raw_score - clue_score
                update = score < score_next or random.random() < math.exp(
                    (score_next - score) / temperature
                )

            if update:
                if verbose:
                    print("update: {} -> {}".format(score, score_next), file=sys.stderr)
                score = score_next
                break
            else:
                if ty <= 2:
                    y, x, n = val
                    if ty == 0:
                        wall_vertical[y][x] = n_prev
                    elif ty == 1:
                        wall_horizontal[y][x] = n_prev
                    elif ty == 2:
                        mark[y][x] = n_prev
                elif ty == 3:
                    start = n_prev
                elif ty == 4:
                    goal = n_prev

        temperature *= 0.995
    if verbose:
        print("failed", file=sys.stderr)
    return None


def problem_to_pzv_url(height, width, wall_vertical, wall_horizontal, mark, start, goal):
    def convert_binary_seq(s):
        ret = ""
        for i in range((len(s) + 4) // 5):
            v = 0
            for j in range(5):
                if i * 5 + j < len(s) and s[i * 5 + j] == 1:
                    v += 2 ** (4 - j)
            ret += np.base_repr(v, 32).lower()
        return ret

    s = []
    for y in range(height):
        for x in range(width - 1):
            s.append(wall_vertical[y][x])
    ret = convert_binary_seq(s)
    s = []
    for y in range(height - 1):
        for x in range(width):
            s.append(wall_horizontal[y][x])
    ret += convert_binary_seq(s)

    contiguous_empty_cells = 0
    for y in range(height):
        for x in range(width):
            v = 0
            if mark[y][x] != 0:
                v = mark[y][x] + 2
            elif (y, x) == start:
                v = 1
            elif (y, x) == goal:
                v = 2
            if v == 0:
                if contiguous_empty_cells == 31:
                    ret += "z"
                    contiguous_empty_cells = 1
                else:
                    contiguous_empty_cells += 1
            else:
                if contiguous_empty_cells > 0:
                    ret += np.base_repr(contiguous_empty_cells + 4, 36).lower()
                    contiguous_empty_cells = 0
                ret += str(v)
    if contiguous_empty_cells > 0:
        ret += np.base_repr(contiguous_empty_cells + 4, 36).lower()

    return "http://pzv.jp/p.html?nurimaze/{}/{}/{}".format(width, height, ret)


def _main():
    if len(sys.argv) == 1:
        # https://twitter.com/semiexp/status/1229769178623574026
        height = 10
        width = 10
        wall_vertical = [
            [0, 1, 1, 1, 0, 1, 0, 1, 1],
            [1, 0, 0, 1, 0, 1, 1, 0, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 0, 1, 1, 1],
            [1, 1, 0, 0, 1, 0, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 0, 1],
            [1, 0, 1, 1, 1, 0, 1, 0, 1],
        ]
        wall_horizontal = [
            [1, 1, 1, 1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 0, 0, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 0, 1, 0, 1, 1, 1],
            [1, 1, 0, 1, 1, 1, 1, 1, 1, 0],
        ]
        mark = [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 2, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 2, 0, 0, 0, 0, 2, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
        ]  # yapf: disable
        start = (6, 5)
        goal = (7, 8)
        is_sat, is_white = solve_nurimaze(
            height, width, wall_vertical, wall_horizontal, mark, start, goal
        )
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_white, {None: "?", True: ".", False: "#"}))
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            generated = generate_nurimaze(height, width, verbose=True)
            if generated is not None:
                wall_vertical, wall_horizontal, mark, start, goal = generated
                for y in range(height * 2 + 1):
                    for x in range(width * 2 + 1):
                        if y % 2 == 0 and x % 2 == 0:
                            print("+", end="")
                        elif y % 2 == 1 and x % 2 == 1:
                            cy = y // 2
                            cx = x // 2
                            if mark[cy][cx] == 0:
                                if (cy, cx) == start:
                                    c = "S"
                                elif (cy, cx) == goal:
                                    c = "G"
                                else:
                                    c = " "
                            elif mark[cy][cx] == 1:
                                c = "O"
                            elif mark[cy][cx] == 2:
                                c = "X"
                            print(c, end="")
                        elif y % 2 == 0 and x % 2 == 1:
                            if (
                                y == 0
                                or y == height * 2
                                or wall_horizontal[y // 2 - 1][x // 2] == 1
                            ):
                                print("-", end="")
                            else:
                                print(" ", end="")
                        elif y % 2 == 1 and x % 2 == 0:
                            if x == 0 or x == width * 2 or wall_vertical[y // 2][x // 2 - 1] == 1:
                                print("|", end="")
                            else:
                                print(" ", end="")
                    print()
                print()
                print(
                    problem_to_pzv_url(
                        height, width, wall_vertical, wall_horizontal, mark, start, goal
                    ),
                    flush=True,
                )


if __name__ == "__main__":
    _main()
