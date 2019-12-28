from cspuz import Solver, BoolGridFrame, BoolVars, backend
import random
import math
import sys


def solve_slitherlink(height, width, problem, check_sat_only=False):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height, width)
    grid_frame.single_loop()
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 0:
                solver.ensure(BoolVars(
                    [grid_frame[y * 2 + 1, x * 2 + 0],
                     grid_frame[y * 2 + 1, x * 2 + 2],
                     grid_frame[y * 2 + 0, x * 2 + 1],
                     grid_frame[y * 2 + 2, x * 2 + 1]]
                ).count_true() == problem[y][x])

    if check_sat_only:
        return solver.find_answer()

    solver.add_answer_key(grid_frame.all_edges())
    sat = solver.solve(backend=backend.sugar_extended)
    return sat, grid_frame


def compute_score(grid_frame):
    score = 0
    for e in grid_frame.all_edges():
        if e.sol is not None:
            score += 1
    return score


def generate_slitherlink(height, width):
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
                    for y in range(height):
                        for x in range(width):
                            n = problem[y][x]
                            print(n if n >= 0 else '.', end=' ')
                        print()
                    return
                score_next = raw_score - 5.0 * n_clues_next
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                n_clues = n_clues_next
                break
            else:
                problem[y][x] = n_prev

        temperature *= 0.995
    print('failed')


if __name__ == '__main__':
    height, width = map(int, sys.argv[1:])
    generate_slitherlink(height, width)
