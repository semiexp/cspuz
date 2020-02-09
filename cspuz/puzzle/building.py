import random
import math
import sys

from cspuz import Solver
from cspuz.constraints import alldifferent, fold_and
from cspuz.puzzle import util


def solve_building(n, u, d, l, r):
    solver = Solver()
    answer = solver.int_array((n, n), 1, n)
    solver.add_answer_key(answer)

    for i in range(n):
        solver.ensure(alldifferent(answer[i, :]))
        solver.ensure(alldifferent(answer[:, i]))

    def num_visible_buildings(cells):
        cells = list(cells)
        res = 1
        for i in range(1, len(cells)):
            res += fold_and([cells[j] < cells[i] for j in range(i)]).cond(1, 0)
        return res

    for i in range(n):
        if u[i] >= 1:
            solver.ensure(num_visible_buildings(answer[:, i]) == u[i])
        if d[i] >= 1:
            solver.ensure(num_visible_buildings(reversed(list(answer[:, i]))) == d[i])
        if l[i] >= 1:
            solver.ensure(num_visible_buildings(answer[i, :]) == l[i])
        if r[i] >= 1:
            solver.ensure(num_visible_buildings(reversed(list(answer[i, :]))) == r[i])

    is_sat = solver.solve()
    return is_sat, answer


def compute_score(nums):
    score = 0
    for v in nums:
        if v.sol is not None:
            score += 1
    return score


def generate_building(size, verbose=False):
    problem = [[0 for _ in range(size)] for _ in range(4)]
    score = 0
    temperature = 3.0
    fully_solved_score = size * size

    for step in range(size * size * 10):
        cand = []
        for d in range(4):
            for i in range(size):
                for n in range(0, size):
                    if n == 1:
                        continue
                    if problem[d][i] != n:
                        cand.append((d, i, n))
        random.shuffle(cand)

        for d, i, n in cand:
            n_prev = problem[d][i]
            problem[d][i] = n

            is_sat, answer = solve_building(size, *problem)
            if not is_sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(answer)
                if raw_score == fully_solved_score:
                    return problem
                clue_score = 0
                for d2 in range(4):
                    for i2 in range(size):
                        if problem[d2][i2] >= 1:
                            clue_score += 4
                score_next = raw_score - clue_score
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                if verbose:
                    print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                break
            else:
                problem[d][i] = n_prev

        temperature *= 0.995
    if verbose:
        print('failed', file=sys.stderr)
    return None


def _main():
    if len(sys.argv) == 1:
        # generated example: https://twitter.com/semiexp/status/1223911674941296641
        n = 6
        u = [0, 0, 0, 2, 0, 3]
        d = [0, 6, 3, 3, 2, 0]
        l = [2, 0, 0, 3, 3, 3]
        r = [0, 6, 3, 0, 2, 0]
        is_sat, answer = solve_building(n, u, d, l, r)
        if is_sat:
            print(util.stringify_array(answer, str))
    else:
        n = int(sys.argv[1])
        while True:
            problem = generate_building(n, verbose=True)
            if problem is not None:
                print(problem)


if __name__ == '__main__':
    _main()
