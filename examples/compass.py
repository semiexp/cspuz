import random
import math
import sys

from cspuz import Solver, GridDivision, backend


def solve_compass(height, width, problem):
    solver = Solver()
    roots = map(lambda x: (x[0], x[1]), problem)
    division = GridDivision(solver, height, width, len(problem), roots)
    solver.add_answer_key(division[:, :])
    for i, (y, x, u, l, d, r) in enumerate(problem):
        solver.ensure(division[y, x] == i)
        if u >= 0:
            solver.ensure(sum(map(lambda g: (g == i).cond(1, 0), division[:y, :])) == u)
        if d >= 0:
            solver.ensure(sum(map(lambda g: (g == i).cond(1, 0), division[(y + 1):, :])) == d)
        if l >= 0:
            solver.ensure(sum(map(lambda g: (g == i).cond(1, 0), division[:, :x])) == l)
        if r >= 0:
            solver.ensure(sum(map(lambda g: (g == i).cond(1, 0), division[:, (x + 1):])) == r)
    sat = solver.solve(backend=backend.sugar_extended)

    return sat, division


def compute_score(division):
    score = 0
    for v in division[:, :]:
        if v.sol is not None:
            score += 1
    return score


def generate_compass(height, width, pos):
    problem = [[y, x, -1, -1, -1, -1] for y, x in pos]
    score = 0
    temperature = 5.0
    fully_solved_score = height * width

    for step in range(height * width * 10):
        cand = []
        for i in range(len(pos)):
            for j in range(4):
                for n in range(-1, 6):
                    if problem[i][j + 2] != n:
                        cand.append((i, j, n))
        random.shuffle(cand)

        for i, j, n in cand:
            n_prev = problem[i][j + 2]
            problem[i][j + 2] = n

            sat, division = solve_compass(height, width, problem)
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(division)
                if raw_score == fully_solved_score:
                    return problem
                clue_score = 0
                for i2 in range(len(pos)):
                    for j2 in range(2, 6):
                        if problem[i2][j2] >= 0:
                            clue_score += 3
                score_next = raw_score - clue_score
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                break
            else:
                problem[i][j + 2] = n_prev

        temperature *= 0.995
    print('failed')


def generate_example():
    height, width = map(int, sys.stdin.readline().strip().split(' '))
    pos = []
    for y in range(height):
        row = sys.stdin.readline().strip().split(' ')
        for x in range(width):
            if row[x] == '#':
                pos.append((y, x))
    problem = generate_compass(height, width, pos)
    print(problem)
    print(emit_puzz_link_url(height, width, problem))


def emit_puzz_link_url(height, width, pos):
    problem = [[None for _ in range(width)] for _ in range(height)]
    for (y, x, u, l, d, r) in pos:
        problem[y][x] = (u, l, d, r)
    def convert_clue_value(v):
        if v == -1:
            return '.'
        elif 0 <= v <= 15:
            return format(v, 'x')
        else:
            return '-' + format(v, 'x')
    ret = ''
    contiguous_empty_cells = 0
    for y in range(height):
        for x in range(width):
            if problem[y][x] is None:
                if contiguous_empty_cells == 20:
                    ret += 'z'
                    contiguous_empty_cells = 1
                else:
                    contiguous_empty_cells += 1
            else:
                if contiguous_empty_cells > 0:
                    ret += chr(ord('f') + contiguous_empty_cells)
                    contiguous_empty_cells = 0
                ret += convert_clue_value(problem[y][x][0]) + convert_clue_value(problem[y][x][2]) + \
                       convert_clue_value(problem[y][x][1]) + convert_clue_value(problem[y][x][3])
    if contiguous_empty_cells > 0:
        ret += chr(ord('f') + contiguous_empty_cells)
    return 'https://puzz.link/p?compass/{}/{}/{}'.format(width, height, ret)


def solve_example():
    # http://puzzle-toketa.blogspot.com/2016/10/compass.html
    height = 5
    width = 5
    problem = [
        (0, 1, -1, -1, 5, 3),
        (1, 1, 0, 0, 0, 2),
        (2, 2, 0, 0, 1, 2),
        (3, 0, 3, -1, -1, -1)
    ]
    sat, division = solve_compass(height, width, problem)
    if sat:
        for y in range(height):
            for x in range(width):
                n = division[y, x].sol
                print('{:2}'.format(n) if n is not None else '..', end=' ')
            print()
    else:
        print('no answer')


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1].startswith('gen'):
        while True:
            generate_example()
    else:
        solve_example()
