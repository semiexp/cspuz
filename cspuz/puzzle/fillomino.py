import random
import math
import sys

from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.puzzle import util


def solve_fillomino(height, width, problem):
    solver = Solver()
    size = solver.int_array((height, width), 1, height * width)
    solver.add_answer_key(size)
    group_id = graph.division_connected_variable_groups(solver, group_size=size)
    solver.ensure((group_id[:, :-1] == group_id[:, 1:]) == (size[:, :-1] == size[:, 1:]))
    solver.ensure((group_id[:-1, :] == group_id[1:, :]) == (size[:-1, :] == size[1:, :]))
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 1:
                solver.ensure(size[y, x] == problem[y][x])
    is_sat = solver.solve()
    return is_sat, size


def compute_score(ans):
    score = 0
    for v in ans:
        if v.sol is not None:
            score += 1
    return score


def generate_fillomino(height, width, verbose=False):
    problem = [[0 for _ in range(width)] for _ in range(height)]
    score = 0
    temperature = 3.0
    fully_solved_score = height * width

    for step in range(height * width * 10):
        cand = []
        for y in range(height):
            for x in range(width):
                flg = False
                for n in range(0, 9):
                    if problem[y][x] != n:
                        cand.append((y, x, n))
        random.shuffle(cand)

        for y, x, n in cand:
            n_prev = problem[y][x]
            problem[y][x] = n

            sat, answer = solve_fillomino(height, width, problem)
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
                        if problem[y2][x2] != 0:
                            clue_score += 3
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
        # https://twitter.com/semiexp/status/1227192389120356353
        height = 8
        width = 8
        problem = [
            [0, 0, 0, 5, 4, 0, 0, 0],
            [0, 0, 0, 4, 1, 3, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 4],
            [6, 0, 4, 0, 0, 0, 0, 7],
            [0, 5, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 2],
            [1, 0, 0, 0, 4, 0, 0, 7],
            [7, 0, 0, 6, 2, 0, 7, 0],
        ]
#        """
        is_sat, ans = solve_fillomino(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(util.stringify_array(ans, str))
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            problem = generate_fillomino(height, width, verbose=True)
            if problem is not None:
                print(util.stringify_array(problem, lambda x: '.' if x == 0 else str(x)), flush=True)
                print(flush=True)


if __name__ == '__main__':
    _main()
