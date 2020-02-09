import random
import math
import sys

from cspuz import Solver, graph
from cspuz.grid_frame import BoolGridFrame
from cspuz.constraints import count_true
from cspuz.puzzle import util


def solve_slitherlink(height, width, problem):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height, width)
    solver.add_answer_key(grid_frame)
    graph.active_edges_single_cycle(solver, grid_frame)
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 0:
                solver.ensure(count_true(grid_frame.cell_neighbors(y, x)) == problem[y][x])
    is_sat = solver.solve()
    return is_sat, grid_frame


def compute_score(grid_frame):
    score = 0
    for e in grid_frame.all_edges():
        if e.sol is not None:
            score += 1
    return score


def generate_slitherlink(height, width, verbose=False):
    problem = [[-1 for _ in range(width)] for _ in range(height)]
    score = 0
    n_clues = 0
    temperature = 5.0
    fully_solved_score = height * (width + 1) + (height + 1) * width

    for step in range(height * width * 10):
        cand = []
        for y in range(height):
            for x in range(width):
                for n in [-1, 1, 2, 3]:
                    if problem[y][x] != n:
                        cand.append((y, x, n))
        random.shuffle(cand)

        for y, x, n in cand:
            n_prev = problem[y][x]
            n_clues_next = n_clues + (1 if n >= 0 else 0) - (1 if n_prev >= 0 else 0)
            problem[y][x] = n

            sat, grid_frame = solve_slitherlink(height, width, problem)
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(grid_frame)
                if raw_score == fully_solved_score:
                    return problem
                score_next = raw_score - 5.0 * n_clues_next
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                if verbose:
                    print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                n_clues = n_clues_next
                break
            else:
                problem[y][x] = n_prev

        temperature *= 0.995
    if verbose:
        print('failed')
    return None


def _main():
    if len(sys.argv) == 1:
        # original example: http://pzv.jp/p.html?slither/4/4/dgdh2c7b
        height = 4
        width = 4
        problem = [
            [3, -1, -1, -1],
            [3, -1, -1, -1],
            [-1, 2, 2, -1],
            [-1, 2, -1, 1]
        ]
        is_sat, is_line = solve_slitherlink(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(util.stringify_grid_frame(is_line))
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            problem = generate_slitherlink(height, width, verbose=True)
            if problem is not None:
                print(util.stringify_array(problem, { -1: '.', 0: '0', 1: '1', 2: '2', 3: '3' }))


if __name__ == '__main__':
    _main()
