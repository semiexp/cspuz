import random
import math
import sys

from cspuz import Solver, BoolGrid, BoolGridFrame, BoolVars
from cspuz import backend


def solve_view(height, width, problem):
    solver = Solver()
    is_empty = BoolGrid(solver, height, width)
    is_empty.connect_false_cells()
    nums = [[solver.int_var(0, height + width) for _ in range(width)] for _ in range(height)]
    solver.add_answer_key(sum(nums, []))
    solver.add_answer_key(is_empty[:, :])

    to_up = [[solver.int_var(0, height - 1) for _ in range(width)] for _ in range(height)]
    to_left = [[solver.int_var(0, width - 1) for _ in range(width)] for _ in range(height)]
    to_down = [[solver.int_var(0, height - 1) for _ in range(width)] for _ in range(height)]
    to_right = [[solver.int_var(0, width - 1) for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if y == 0:
                solver.ensure(to_up[y][x] == 0)
            else:
                solver.ensure(to_up[y][x] == is_empty[y - 1, x].cond(to_up[y - 1][x] + 1, 0))
            if x == 0:
                solver.ensure(to_left[y][x] == 0)
            else:
                solver.ensure(to_left[y][x] == is_empty[y, x - 1].cond(to_left[y][x - 1] + 1, 0))
            if y == height - 1:
                solver.ensure(to_down[y][x] == 0)
            else:
                solver.ensure(to_down[y][x] == is_empty[y + 1, x].cond(to_down[y + 1][x] + 1, 0))
            if x == width - 1:
                solver.ensure(to_right[y][x] == 0)
            else:
                solver.ensure(to_right[y][x] == is_empty[y, x + 1].cond(to_right[y][x + 1] + 1, 0))

    for y in range(height):
        for x in range(width):
            solver.ensure((~is_empty[y, x]).then(nums[y][x] == to_up[y][x] + to_left[y][x] + to_down[y][x] + to_right[y][x]))
            if y > 0:
                solver.ensure(((~is_empty[y, x]) & (~is_empty[y - 1, x])).then(nums[y][x] != nums[y - 1][x]))
            if x > 0:
                solver.ensure(((~is_empty[y, x]) & (~is_empty[y, x - 1])).then(nums[y][x] != nums[y][x - 1]))
            if problem[y][x] >= 0:
                solver.ensure(nums[y][x] == problem[y][x])
                solver.ensure(~is_empty[y, x])
            solver.ensure(is_empty[y, x].then(nums[y][x] == 0))

    sat = solver.solve(backend=backend.sugar_extended)

    return sat, nums, is_empty


def compute_score(nums):
    score = 0
    for r in nums:
        for v in r:
            if v.sol is not None:
                score += 1
    return score


def generate_view(height, width):
    problem = [[-1 for _ in range(width)] for _ in range(height)]
    score = 0
    temperature = 5.0
    fully_solved_score = height * width

    for step in range(height * width * 10):
        cand = []
        for y in range(height):
            for x in range(width):
                for n in range(-1, max(height, width) + 2):
                    if problem[y][x] != n:
                        cand.append((y, x, n))
        random.shuffle(cand)

        for y, x, n in cand:
            n_prev = problem[y][x]
            problem[y][x] = n

            sat, nums, is_empty = solve_view(height, width, problem)
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(nums)
                if raw_score == fully_solved_score:
                    for y in range(height):
                        for x in range(width):
                            print(problem[y][x] if problem[y][x] >= 0 else '.', end=' ')
                        print()
                    return
                clue_score = 0
                for y2 in range(height):
                    for x2 in range(width):
                        if problem[y2][x2] >= 0:
                            clue_score += 3
                score_next = raw_score - clue_score
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                break
            else:
                problem[y][x] = n_prev

        temperature *= 0.995
    print('failed')


if __name__ == '__main__':
    height, width = map(int, sys.argv[1:])
    generate_view(height, width)
