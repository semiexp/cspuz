import random
import sys
import math

import numpy as np

from cspuz import Solver, graph
from cspuz.constraints import count_true, fold_or
from cspuz.puzzle import util


def solve_heyawake(height, width, problem):
    solver = Solver()
    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)
    graph.active_vertices_not_adjacent_and_not_segmenting(solver, is_black)
    for y0, x0, y1, x1, n in problem:
        if n >= 0:
            solver.ensure(count_true(is_black[y0:y1, x0:x1]) == n)
        if 0 < y0 and y1 < height:
            for x in range(x0, x1):
                solver.ensure(fold_or(is_black[(y0 - 1):(y1 + 1), x]))
        if 0 < x0 and x1 < width:
            for y in range(y0, y1):
                solver.ensure(fold_or(is_black[y, (x0 - 1):(x1 + 1)]))
    is_sat = solver.solve()

    return is_sat, is_black


def enumerate_division_update(problem):
    ret = []
    for i in range(len(problem)):
        y0, x0, y1, x1, n = problem[i]
        if y1 - y0 >= 2:
            for y in range(y0 + 1, y1):
                #if x1 - x0 == 1 and (y - y0 == 1 or y1 - y == 1):
                #    continue
                #if y - y0 == 1 or y1 - y == 1:
                #    continue
                ret.append(([i], [
                    (y0, x0, y, x1, -1),
                    (y, x0, y1, x1, -1)
                ]))
        if x1 - x0 >= 2:
            for x in range(x0 + 1, x1):
                #if y1 - y0 == 1 and (x - x0 == 1 and x1 - x == 1):
                #    continue
                #if x - x0 == 1 or x1 - x == 1:
                #    continue
                ret.append(([i], [
                    (y0, x0, y1, x, -1),
                    (y0, x, y1, x1, -1)
                ]))
    for i in range(len(problem)):
        for j in range(i):
            y0a, x0a, y1a, x1a, na = problem[i]
            y0b, x0b, y1b, x1b, nb = problem[j]
            if y0a == y0b and y1a == y1b and (x1a == x0b or x1b == x0a):
                y0 = y0a
                y1 = y1a
                x0 = min(x0a, x0b)
                x1 = max(x1a, x1b)
            elif x0a == x0b and x1a == x1b and (y1a == y0b or y1b == y0a):
                x0 = x0a
                x1 = x1a
                y0 = min(y0a, y0b)
                y1 = max(y1a, y1b)
            else:
                continue
            ret.append(([i, j], [(y0, x0, y1, x1, -1)]))
    return ret


def num_thin_blocks(problem):
    ret = 0
    for y0, x0, y1, x1, n in problem:
        if y1 - y0 == 1:
            ret += 1
        if x1 - x0 == 1:
            ret += 1
    return ret


def num_max_black_cells(h, w):
    # Formula: https://web.archive.org/web/20181106095427/http://www.geocities.co.jp/HeartLand-Poplar/2112/heyawake_mx/
    if h == 1 or w == 1:
        return (h * w + 1) // 2
    elif h == 3 or w == 3:
        n = h + w - 3
        k = (n + 1) // 4
        return 5 * k + [0, 2, 3, 0][n % 4]
    else:
        if h == 7 and w == 7:
            # (2^k-1) * (2^k-1) cases are very limited
            return 21
        elif h % 2 == 1 and w % 2 == 1:
            return (h * w + h + w - 1) // 3
        else:
            return (h * w + h + w - 2) // 3


def enumerate_clue_update(problem):
    ret = []
    for i in range(len(problem)):
        y0, x0, y1, x1, n = problem[i]
        nmax = num_max_black_cells(y1 - y0, x1 - x0)
        for n2 in range(-1, nmax + 1):
            if n2 != n and n2 != 0 and n2 != 1 and n2 <= 8 and n2 >= nmax // 2 and n2 != nmax:
                ret.append(([i], [(y0, x0, y1, x1, n2)]))
    return ret


def compute_score(is_black):
    score = 0
    for v in is_black:
        if v.sol is not None:
            score += 1
    return score


def compute_clue_score(problem):
    clue_score = 0
    for y0, x0, y1, x1, n in problem:
        if n != -1:
            clue_score += 5 # n * 2 + (y1 - y0) * (x1 - x0) * 0.2
        # 'thin' blocks are not preferred
        if y1 - y0 == 1:
            clue_score += 2
        if x1 - x0 == 1:
            clue_score += 2
    return clue_score


def generate_heyawake(height, width, n_max_rooms=None):
    if n_max_rooms is None:
        n_max_rooms = height * width
    problem = [
        (0, 0, height, width, -1)
    ]
    score = -compute_clue_score(problem)
    temperature = 5.0
    fully_solved_score = height * width

    for step in range(height * width):
        cand = enumerate_division_update(problem)
        random.shuffle(cand)

        for elim, app in cand:
            num_rooms = len(problem) + len(app) - len(elim)
            if num_rooms <= n_max_rooms:
                problem2 = [x for i, x in enumerate(problem) if i not in elim] + app
                if num_thin_blocks(problem2) <= 3:
                    problem = problem2
                    break

    for step in range(height * width * 10):
        cand = enumerate_division_update(problem) + enumerate_clue_update(problem)
        random.shuffle(cand)

        for elim, app in cand:
            num_rooms = len(problem) + len(app) - len(elim)
            if num_rooms > n_max_rooms:
                continue
            problem2 = [x for i, x in enumerate(problem) if i not in elim]
            problem2 += app

            if num_thin_blocks(problem2) > 3:
                continue
            sat, is_black = solve_heyawake(height, width, problem2)
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(is_black)
                if raw_score == fully_solved_score:
                    return problem2
                clue_score = compute_clue_score(problem2)
                score_next = raw_score - clue_score
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                print('update: {} -> {} ({} {})'.format(score, score_next, raw_score, clue_score), file=sys.stderr)
                problem = problem2
                score = score_next
                break
            else:
                continue
        temperature *= 0.995
    print('failed', file=sys.stderr)
    return None


def problem_to_pzv_url(height, width, problem):
    def convert_binary_seq(s):
        ret = ''
        for i in range((len(s) + 4) // 5):
            v = 0
            for j in range(5):
                if i * 5 + j < len(s) and s[i * 5 + j] == 1:
                    v += (2 ** (4 - j))
            ret += np.base_repr(v, 32).lower()
        return ret

    blocks = [[-1 for _ in range(width)] for _ in range(height)]
    clues = [[-2 for _ in range(width)] for _ in range(height)]
    for i, (y0, x0, y1, x1, n) in enumerate(problem):
        for y in range(y0, y1):
            for x in range(x0, x1):
                blocks[y][x] = i
        clues[y0][x0] = n
    s = []
    for y in range(height):
        for x in range(width - 1):
            s.append(1 if blocks[y][x] != blocks[y][x + 1] else 0)
    ret = convert_binary_seq(s)
    s = []
    for y in range(height - 1):
        for x in range(width):
            s.append(1 if blocks[y][x] != blocks[y + 1][x] else 0)
    ret += convert_binary_seq(s)

    contiguous_empty_cells = 0
    for y in range(height):
        for x in range(width):
            if clues[y][x] == -2:
                continue
            if clues[y][x] == -1:
                if contiguous_empty_cells == 20:
                    ret += 'z'
                    contiguous_empty_cells = 1
                else:
                    contiguous_empty_cells += 1
            else:
                if contiguous_empty_cells > 0:
                    ret += chr(ord('f') + contiguous_empty_cells)
                    contiguous_empty_cells = 0
                if clues[y][x] >= 16:
                    ret += '-' + format(clues[y][x], 'x')
                else:
                    ret += format(clues[y][x], 'x')
    if contiguous_empty_cells > 0:
        ret += chr(ord('f') + contiguous_empty_cells)

    return 'http://pzv.jp/p.html?heyawake/{}/{}/{}'.format(width, height, ret)


def _main():
    if len(sys.argv) == 1:
        # original example: http://pzv.jp/p.html?heyawake/6/6/aa66aapv0fu0g2i3k
        height = 6
        width = 6
        problem = [
            (0, 0, 1, 2, -1),
            (0, 2, 2, 4, 2),
            (0, 4, 1, 6, -1),
            (1, 0, 2, 2, -1),
            (1, 4, 3, 6, -1),
            (2, 0, 4, 3, 3),
            (2, 3, 4, 4, -1),
            (3, 4, 4, 6, -1),
            (4, 0, 6, 2, -1),
            (4, 2, 6, 4, -1),
            (4, 4, 6, 6, -1)
        ]
        is_sat, is_black = solve_heyawake(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {
                None: '?',
                True: '#',
                False: '.'
            }))
    else:
        height, width, n_rooms_low, n_rooms_high = map(int, sys.argv[1:])
        while True:
            problem = generate_heyawake(height, width, n_max_rooms=random.randint(n_rooms_low, n_rooms_high))
            if problem is not None:
                url = problem_to_pzv_url(height, width, problem)
                print(url, flush=True)
                print(problem, file=sys.stderr)


if __name__ == '__main__':
    _main()
