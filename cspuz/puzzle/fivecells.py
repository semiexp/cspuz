import random
import math
import sys

from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.puzzle import util


def solve_fivecells(height, width, problem):
    vertex_id = [[-1 for _ in range(width)] for _ in range(height)]
    id_last = 0
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= -1:
                vertex_id[y][x] = id_last
                id_last += 1
    g = graph.Graph(id_last)
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= -1:
                if y < height - 1 and problem[y + 1][x] >= -1:
                    g.add_edge(vertex_id[y][x], vertex_id[y + 1][x])
                if x < width - 1 and problem[y][x + 1] >= -1:
                    g.add_edge(vertex_id[y][x], vertex_id[y][x + 1])
    solver = Solver()
    group_id = graph.division_connected_variable_groups(solver, graph=g, group_size=5)
    is_invalid = False
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 0:
                borders = []
                if y > 0 and problem[y - 1][x] >= -1:
                    borders.append(group_id[vertex_id[y][x]] != group_id[vertex_id[y - 1][x]])
                if y < height - 1 and problem[y + 1][x] >= -1:
                    borders.append(group_id[vertex_id[y][x]] != group_id[vertex_id[y + 1][x]])
                if x > 0 and problem[y][x - 1] >= -1:
                    borders.append(group_id[vertex_id[y][x]] != group_id[vertex_id[y][x - 1]])
                if x < width - 1 and problem[y][x + 1] >= -1:
                    borders.append(group_id[vertex_id[y][x]] != group_id[vertex_id[y][x + 1]])
                always_border = 4 - len(borders)
                solver.ensure(count_true(borders) == problem[y][x] - always_border)
                if problem[y][x] - always_border < 0:
                    is_invalid = True

    is_border = solver.bool_array(len(g))
    for i, (u, v) in enumerate(g):
        solver.ensure(is_border[i] == (group_id[u] != group_id[v]))
    solver.add_answer_key(is_border)

    if is_invalid:
        is_sat = False
    else:
        is_sat = solver.solve()
    return is_sat, is_border


def compute_score(ans):
    score = 0
    for v in ans:
        if v.sol is not None:
            score += 1
    return score


def generate_fivecells(height, width, verbose=False):
    problem = [[-1 for _ in range(width)] for _ in range(height)]
    score = 0
    temperature = 5.0
    fully_solved_score = height * (width - 1) + (height - 1) * width

    for step in range(height * width * 10):
        cand = []
        for y in range(height):
            for x in range(width):
                low = 0
                if y == 0 or y == height - 1:
                    low += 1
                if x == 0 or x == width - 1:
                    low += 1
                for n in range(-1, 4):
                    if n != -1 and n < low:
                        continue
                    if n == low:  # avoid easy problems
                        continue
                    if problem[y][x] != n:
                        cand.append((y, x, n))
        random.shuffle(cand)

        for y, x, n in cand:
            n_prev = problem[y][x]
            problem[y][x] = n

            sat, answer = solve_fivecells(height, width, problem)
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
                        if problem[y2][x2] >= 0:
                            clue_score += 8
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
        # generated example: http://pzv.jp/p.html?fivecells/5/5/a23i21b3g3
        height = 5
        width = 5
        problem = [
            [-1,  2,  3, -1, -1],
            [-1, -1, -1, -1, -1],
            [-1, -1,  2,  1, -1],
            [-1,  3, -1, -1, -1],
            [-1, -1, -1, -1,  3],
        ]
        is_sat, is_border = solve_fivecells(height, width, problem)
        print('has answer:', is_sat)
        for i, x in enumerate(is_border):
            print(i, x.sol)
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            problem = generate_fivecells(height, width, verbose=True)
            if problem is not None:
                print(util.stringify_array(problem, {
                    -2: '#', -1: '.', 0: '0', 1: '1', 2: '2', 3: '3'
                }) + '\n', flush=True)


if __name__ == '__main__':
    _main()
