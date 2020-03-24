import random
import math
import sys

from cspuz import Solver
from cspuz.constraints import count_true
from cspuz.puzzle import util


def solve_shakashaka(height, width, problem):
    # 1   2   3   4
    # +-+ +     + +-+
    # |/  |\   /|  \|
    # +   +-+ +-+   +
    solver = Solver()
    answer = solver.int_array((height, width), 0, 4)
    solver.add_answer_key(answer)

    for y in range(height):
        for x in range(width):
            if problem[y][x] is not None:
                solver.ensure(answer[y, x] == 0)
                if problem[y][x] >= 0:
                    solver.ensure(count_true(answer.four_neighbors(y, x) != 0) == problem[y][x])
    for y in range(height + 1):
        for x in range(width + 1):
            diagonals = []
            is_empty = []
            is_white_angle = []
            if y > 0 and x > 0:
                diagonals.append(answer[y - 1, x - 1] == 4)
                diagonals.append(answer[y - 1, x - 1] == 2)
                is_empty.append(answer[y - 1, x - 1] == 0 if problem[y - 1][x - 1] is None else False)
                if problem[y - 1][x - 1] is None:
                    is_white_angle.append((answer[y - 1, x - 1] == 0) | (answer[y - 1, x - 1] == 1))
            else:
                diagonals += [False, False]
                is_empty.append(False)
            if y < height and x > 0:
                diagonals.append(answer[y, x - 1] == 1)
                diagonals.append(answer[y, x - 1] == 3)
                is_empty.append(answer[y, x - 1] == 0 if problem[y][x - 1] is None else False)
                if problem[y][x - 1] is None:
                    is_white_angle.append((answer[y, x - 1] == 0) | (answer[y, x - 1] == 2))
            else:
                diagonals += [False, False]
                is_empty.append(False)
            if y < height and x < width:
                diagonals.append(answer[y, x] == 2)
                diagonals.append(answer[y, x] == 4)
                is_empty.append(answer[y, x] == 0 if problem[y][x] is None else False)
                if problem[y][x] is None:
                    is_white_angle.append((answer[y, x] == 0) | (answer[y, x] == 3))
            else:
                diagonals += [False, False]
                is_empty.append(False)
            if y > 0 and x < width:
                diagonals.append(answer[y - 1, x] == 3)
                diagonals.append(answer[y - 1, x] == 1)
                is_empty.append(answer[y - 1, x] == 0 if problem[y - 1][x] is None else False)
                if problem[y - 1][x] is None:
                    is_white_angle.append((answer[y - 1, x] == 0) | (answer[y - 1, x] == 4))
            else:
                diagonals += [False, False]
                is_empty.append(False)
            for i in range(8):
                if diagonals[i] is False:
                    continue
                if i % 2 == 0:
                    solver.ensure(diagonals[i].then(
                        diagonals[(i + 3) % 8] | (is_empty[(i + 3) % 8 // 2] & diagonals[(i + 5) % 8])
                    ))
                else:
                    solver.ensure(diagonals[i].then(
                        diagonals[(i + 5) % 8] | (is_empty[(i + 5) % 8 // 2] & diagonals[(i + 3) % 8])
                    ))
            solver.ensure(count_true(is_white_angle) != 3)
    is_sat = solver.solve()
    return is_sat, answer


def compute_score(ans):
    score = 0
    for v in ans:
        if v.sol is not None:
            score += 1
    return score


def generate_shakashaka(height, width, verbose=False):
    problem = [[None for _ in range(width)] for _ in range(height)]
    score = 0
    temperature = 5.0
    fully_solved_score = height * width

    for step in range(height * width * 10):
        cand = []
        for y in range(height):
            for x in range(width):
                flg = False
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        y2 = y + dy
                        x2 = x + dx
                        if 0 <= y2 < height and 0 <= x2 < width and (y2, x2) != (y, x) and problem[y2][x2] is not None:
                            flg = True
                maxn = (1 if y > 0 else 0) + (1 if x > 0 else 0) + (1 if y < height - 1 else 0) + (1 if x < width - 1 else 0)
                for n in [None, -1, 0, 1, 2, 3, 4]:
                    if n is not None and n > maxn:
                        continue
                    if flg and n is not None:
                        continue
                    if problem[y][x] != n:
                        cand.append((y, x, n))
        random.shuffle(cand)

        for y, x, n in cand:
            n_prev = problem[y][x]
            problem[y][x] = n

            sat, answer = solve_shakashaka(height, width, problem)
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(answer)
                if raw_score == fully_solved_score:
                    return problem
                clue_score = 0
                for y2 in range(height):
                    for x2 in range(width):
                        if problem[y2][x2] is not None:
                            clue_score += 6
                score_next = raw_score - clue_score
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                if verbose:
                    print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                break
            else:
                problem[y][x] = n_prev

        temperature *= 0.995
    if verbose:
        print('failed', file=sys.stderr)
    return None


def _main():
    if len(sys.argv) == 1:
        # generated example: https://twitter.com/semiexp/status/1223794016593956864
        height, width = 10, 10
        problem = [[None for _ in range(width)] for _ in range(height)]
        problem[1][2] = 3
        problem[2][7] = 2
        problem[2][9] = 0
        problem[3][0] = 1
        problem[3][3] = 3
        problem[4][6] = 3
        problem[5][0] = 2
        problem[5][3] = 2
        problem[6][8] = 2
        problem[9][3] = 2
        problem[9][7] = 0

        is_sat, ans = solve_shakashaka(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(util.stringify_array(ans, str))
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            problem = generate_shakashaka(height, width, verbose=True)
            if problem is not None:
                print(util.stringify_array(problem, {
                    None: '.',
                    -1: '#',
                    0: '0',
                    1: '1',
                    2: '2',
                    3: '3',
                    4: '4'
                }))


if __name__ == '__main__':
    _main()
