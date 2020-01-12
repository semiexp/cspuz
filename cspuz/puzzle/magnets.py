import random
import math
import sys

from cspuz import Solver, Array
from cspuz.constraints import count_true


def solve_magnets(height, width, to_right, to_down, cond_row, cond_col):
    solver = Solver()
    plus = solver.bool_array((height, width))
    minus = solver.bool_array((height, width))
    solver.add_answer_key(plus)
    solver.add_answer_key(minus)
    solver.ensure(~(plus & minus))
    solver.ensure(Array(to_right)[:, :-1].then((plus[:, :-1] == minus[:, 1:]) & (minus[:, :-1] == plus[:, 1:])))
    solver.ensure(Array(to_down)[:-1, :].then((plus[:-1, :] == minus[1:, :]) & (minus[:-1, :] == plus[1:, :])))
    solver.ensure(~(plus[:-1, :] & plus[1:, :]))
    solver.ensure(~(minus[:-1, :] & minus[1:, :]))
    solver.ensure(~(plus[:, :-1] & plus[:, 1:]))
    solver.ensure(~(minus[:, :-1] & minus[:, 1:]))
    for y in range(height):
        if cond_row[y][0] >= 0:
            solver.ensure(count_true(plus[y, :]) == cond_row[y][0])
        if cond_row[y][1] >= 0:
            solver.ensure(count_true(minus[y, :]) == cond_row[y][1])
    for x in range(width):
        if cond_col[x][0] >= 0:
            solver.ensure(count_true(plus[:, x]) == cond_col[x][0])
        if cond_col[x][1] >= 0:
            solver.ensure(count_true(minus[:, x]) == cond_col[x][1])
    is_sat = solver.solve()
    return is_sat, plus, minus


def _compute_score(plus, minus):
    score = 0
    for v in plus[:, :]:
        if v.sol is not None:
            score += 1
    for v in minus[:, :]:
        if v.sol is not None:
            score += 1
    return score


def generate_magnets(height, width, no_easy_constraints=False, verbose=False):
    to_right = [[False for _ in range(width)] for _ in range(height)]
    to_down = [[False for _ in range(width)] for _ in range(height)]
    cond_row = [[-1, -1] for _ in range(height)]
    cond_col = [[-1, -1] for _ in range(width)]

    score = 0
    temperature = 5.0
    fully_solved_score = height * width * 2

    if height % 2 == 0:
        for y in range(height):
            for x in range(width):
                if y % 2 == 0:
                    to_down[y][x] = True
    elif width % 2 == 0:
        for y in range(height):
            for x in range(width):
                if x % 2 == 0:
                    to_right[y][x] = True
    else:
        raise ValueError('height * width must be a multiple of 2')

    def apply_step(s, rev=False):
        if len(s) == 2:
            y, x = s
            if to_right[y][x]:
                to_right[y][x] = False
                to_right[y + 1][x] = False
                to_down[y][x] = True
                to_down[y][x + 1] = True
            else:
                to_right[y][x] = True
                to_right[y + 1][x] = True
                to_down[y][x] = False
                to_down[y][x + 1] = False
        elif len(s) == 3:
            y, x, i = s
            if i == 0:
                if to_right[y][x]:
                    to_right[y][x] = to_down[y + 1][x] = to_down[y + 1][x + 1] = False
                    to_right[y + 2][x] = to_down[y][x] = to_down[y][x + 1] = True
                else:
                    to_right[y][x] = to_down[y + 1][x] = to_down[y + 1][x + 1] = True
                    to_right[y + 2][x] = to_down[y][x] = to_down[y][x + 1] = False
            elif i == 1:
                if to_down[y][x]:
                    to_down[y][x] = to_right[y][x + 1] = to_right[y + 1][x + 1] = False
                    to_down[y][x + 2] = to_right[y][x] = to_right[y + 1][x] = True
                else:
                    to_down[y][x] = to_right[y][x + 1] = to_right[y + 1][x + 1] = True
                    to_down[y][x + 2] = to_right[y][x] = to_right[y + 1][x] = False
        else:
            p, i, n, n2 = s
            if rev:
                n = n2
            if i < 2:
                cond_row[p][i] = n
            else:
                cond_col[p][i - 2] = n

    for step in range(-(height * width * 20), height * width * 10):
        cand = []
        for y in range(height):
            for x in range(width):
                if y < height - 1 and to_right[y][x] and to_right[y + 1][x]:
                    cand.append((y, x))
                if x < width - 1 and to_down[y][x] and to_down[y][x + 1]:
                    cand.append((y, x))
                if y < height - 2 and x < width - 1:
                    if (to_right[y][x] and to_down[y + 1][x] and to_down[y + 1][x + 1]) or (
                            to_right[y + 2][x] and to_down[y][x] and to_down[y][x + 1]):
                        cand.append((y, x, 0))
                if y < height - 1 and x < width - 2:
                    if (to_down[y][x] and to_right[y][x + 1] and to_right[y + 1][x + 1]) or (
                            to_down[y][x + 2] and to_right[y][x] and to_right[y + 1][x]):
                        cand.append((y, x, 1))
        if step < 0:
            apply_step(cand[random.randint(0, len(cand) - 1)])
            continue

        for y in range(height):
            for i in range(2):
                for n in range(-1, (width + 1) // 2 + 1):
                    if no_easy_constraints and (n == 0 or n == (width + 1) // 2):
                        continue
                    if cond_row[y][i] != n:
                        cand.append((y, i, n, cond_row[y][i]))
        for x in range(width):
            for i in range(2):
                for n in range(-1, (height + 1) // 2 + 1):
                    if no_easy_constraints and (n == 0 or n == (height + 1) // 2):
                        continue
                    if cond_col[x][i] != n:
                        cand.append((x, i + 2, n, cond_col[x][i]))
        random.shuffle(cand)

        for mv in cand:
            apply_step(mv)

            sat, plus, minus = solve_magnets(height, width, to_right, to_down, cond_row, cond_col)
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = _compute_score(plus, minus)
                if raw_score == fully_solved_score:
                    return to_right, to_down, cond_row, cond_col
                clue_score = 0
                for y in range(height):
                    if cond_row[y][0] >= 0:
                        clue_score += 7
                    if cond_row[y][1] >= 0:
                        clue_score += 7
                for x in range(height):
                    if cond_col[x][0] >= 0:
                        clue_score += 7
                    if cond_col[x][1] >= 0:
                        clue_score += 7
                score_next = raw_score - clue_score
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                if verbose:
                    print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                break
            else:
                apply_step(mv, rev=True)
    if verbose:
        print('failed', file=sys.stderr)
    return None


def stringify_magnets_problem(height, width, to_right, to_down, cond_row, cond_col):
    ret = []
    ret.append('+  |')
    for x in range(width):
        ret.append(str(cond_col[x][0]) if cond_col[x][0] != -1 else '.')
        if x != width - 1:
            ret.append(' ')
    ret.append('\n')
    ret.append('  -|')
    for x in range(width):
        ret.append(str(cond_col[x][1]) if cond_col[x][1] != -1 else '.')
        if x != width - 1:
            ret.append(' ')
    ret.append('\n')
    for y in range(height * 2 + 1):
        if y % 2 == 0:
            if y == 0:
                ret.append('---')
            else:
                ret.append('   ')
        else:
            ret.append(str(cond_row[y // 2][0]) if cond_row[y // 2][0] != -1 else '.')
            ret.append(' ')
            ret.append(str(cond_row[y // 2][1]) if cond_row[y // 2][1] != -1 else '.')
        for x in range(width * 2 + 1):
            if y % 2 == 0 and x % 2 == 0:
                ret.append('+')
            elif y % 2 == 1 and x % 2 == 0:
                if x > 0 and to_right[y // 2][x // 2 - 1]:
                    ret.append(' ')
                else:
                    ret.append('|')
            elif y % 2 == 0 and x % 2 == 1:
                if y > 0 and to_down[y // 2 - 1][x // 2]:
                    ret.append(' ')
                else:
                    ret.append('-')
            else:
                ret.append(' ')
        ret.append('\n')
    return ''.join(ret)


def _main():
    to_right, to_down, cond_row, cond_col = generate_magnets(6, 6, verbose=True)
    print(stringify_magnets_problem(6, 6, to_right, to_down, cond_row, cond_col))


if __name__ == '__main__':
    _main()
