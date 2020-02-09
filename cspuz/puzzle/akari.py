import random
import math
import sys
import itertools

from cspuz import Solver
from cspuz.constraints import fold_or, count_true
from cspuz.puzzle import util


def solve_akari(height, width, problem):
    solver = Solver()
    has_light = solver.bool_array((height, width))
    solver.add_answer_key(has_light)

    for y in range(height):
        for x in range(width):
            if problem[y][x] >= -1:
                continue
            if y == 0 or problem[y - 1][x] >= -1:
                group = []
                for y2 in range(y, height):
                    if problem[y2][x] < -1:
                        group.append((y2, x))
                    else:
                        break
                solver.ensure(count_true([has_light[p] for p in group]) <= 1)
            if x == 0 or problem[y][x - 1] >= -1:
                group = []
                for x2 in range(x, width):
                    if problem[y][x2] < -1:
                        group.append((y, x2))
                    else:
                        break
                solver.ensure(count_true([has_light[p] for p in group]) <= 1)

    for y in range(height):
        for x in range(width):
            if problem[y][x] < -1:
                sight = [(y, x)]
                for y2 in range(y - 1, -1, -1):
                    if problem[y2][x] < -1:
                        sight.append((y2, x))
                    else:
                        break
                for y2 in range(y + 1, height, 1):
                    if problem[y2][x] < -1:
                        sight.append((y2, x))
                    else:
                        break
                for x2 in range(x - 1, -1, -1):
                    if problem[y][x2] < -1:
                        sight.append((y, x2))
                    else:
                        break
                for x2 in range(x + 1, width, 1):
                    if problem[y][x2] < -1:
                        sight.append((y, x2))
                    else:
                        break
                solver.ensure(fold_or([has_light[p] for p in sight]))
            else:
                solver.ensure(~has_light[y, x])
                if problem[y][x] >= 0:
                    neighbors = []
                    if y > 0 and problem[y - 1][x] < -1:
                        neighbors.append((y - 1, x))
                    if y < height - 1 and problem[y + 1][x] < -1:
                        neighbors.append((y + 1, x))
                    if x > 0 and problem[y][x - 1] < -1:
                        neighbors.append((y, x - 1))
                    if x < width - 1 and problem[y][x + 1] < -1:
                        neighbors.append((y, x + 1))
                    solver.ensure(count_true([has_light[p] for p in neighbors]) == problem[y][x])

    is_sat = solver.solve()
    return is_sat, has_light


def compute_score(ans):
    score = 0
    for v in ans:
        if v.sol is not None:
            score += 1
    return score


def generate_akari(height, width, no_adjacent_clue=False, initial_blocks=None, verbose=False):
    problem = [[-2 for _ in range(width)] for _ in range(height)]
    score = 0
    temperature = 5.0
    fully_solved_score = height * width

    if initial_blocks is not None:
        num_blocks = 0
        while num_blocks < initial_blocks:
            y = random.randint(0, height - 1)
            x = random.randint(0, width - 1)
            y2 = height - 1 - y
            x2 = width - 1 - x
            if no_adjacent_clue:
                if y > 0 and problem[y - 1][x] != -2:
                    continue
                if y < height - 1 and problem[y + 1][x] != -2:
                    continue
                if x > 0 and problem[y][x - 1] != -2:
                    continue
                if x < width - 1 and problem[y][x + 1] != -2:
                    continue
                if abs(y2 - y) + abs(x2 - x) == 1:
                    continue
            if problem[y][x] != -2:
                continue
            problem[y][x] = -1
            problem[y2][x2] = -1
            if (y, x) == (y2, x2):
                num_blocks += 1
            else:
                num_blocks += 2
        score = -(num_blocks * 2)

    for step in range(height * width * 10):
        cand = []
        for y in range(height):
            for x in range(width):
                if no_adjacent_clue:
                    if y > 0 and problem[y - 1][x] != -2:
                        continue
                    if y < height - 1 and problem[y + 1][x] != -2:
                        continue
                    if x > 0 and problem[y][x - 1] != -2:
                        continue
                    if x < width - 1 and problem[y][x + 1] != -2:
                        continue

                y2, x2 = height - 1 - y, width - 1 - x
                maxn = (1 if y2 > 0 and problem[y2 - 1][x2] == -2 else 0) +\
                       (1 if y2 < height - 1 and problem[y2 + 1][x2] == -2 else 0) +\
                       (1 if x2 > 0 and problem[y2][x2 - 1] == -2 else 0) +\
                       (1 if x2 < width - 1 and problem[y2][x2 + 1] == -2 else 0)
                if (y, x) < (y2, x2):
                    for n1, n2 in [(-2, -2)] + list(itertools.product(range(-1, maxn + 1), range(-1, maxn + 1))):
                        if (problem[y][x], problem[y2][x2]) != (n1, n2):
                            cand.append([(y, x, n1), (y2, x2, n2)])
                elif (y, x) == (y2, x2):
                    for n in range(-2, maxn + 1):
                        if problem[y][x] != n:
                            cand.append([(y, x, n)])
        random.shuffle(cand)

        for update in cand:
            restore = [(y, x, problem[y][x]) for y, x, _ in update]
            for y, x, n in update:
                problem[y][x] = n

            sat, has_light = solve_akari(height, width, problem)
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(has_light)
                if raw_score == fully_solved_score:
                    return problem
                clue_score = 0
                for y in range(height):
                    for x in range(width):
                        if problem[y][x] == -1:
                            clue_score += 2
                        elif problem[y][x] >= 0:
                            clue_score += 8
                score_next = raw_score - clue_score
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                if verbose:
                    print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                break
            else:
                for y, x, n in restore:
                    problem[y][x] = n

        temperature *= 0.995
    if verbose:
        print('failed', file=sys.stderr)
    return None


def _main():
    if len(sys.argv) == 1:
        # generated example: https://twitter.com/semiexp/status/1225770511080144896
        height = 10
        width = 10
        problem = [
            [-2, -2,  2, -2, -2, -2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2, -2, -2, -2,  2, -2],
            [-2, -2, -2, -2, -2, -2, -2, -1, -2, -2],
            [-1, -2, -2, -2,  3, -2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2, -1, -2, -2, -2, -1],
            [ 2, -2, -2, -2,  2, -2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2,  3, -2, -2, -2, -1],
            [-2, -2, -1, -2, -2, -2, -2, -2, -2, -2],
            [-2,  2, -2, -2, -2, -2, -2, -2, -2, -2],
            [-2, -2, -2, -2, -2, -2, -2, -1, -2, -2],
        ]
        is_sat, has_light = solve_akari(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(util.stringify_array(has_light, {
                True: 'O',
                False: '.',
                None: '?'
            }))
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            problem = generate_akari(height, width, no_adjacent_clue=True, initial_blocks=6, verbose=True)
            if problem is not None:
                print(util.stringify_array(problem, {
                    -2: '.', -1: '#', 0: '0', 1: '1', 2: '2', 3: '3', 4: '4'
                }))


if __name__ == '__main__':
    _main()
