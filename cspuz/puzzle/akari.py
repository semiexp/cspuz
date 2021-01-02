import sys

from cspuz import Solver
from cspuz.constraints import fold_or, count_true
from cspuz.puzzle import util
from cspuz.generator import (generate_problem, count_non_default_values,
                             ArrayBuilder2D)


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
                    solver.ensure(
                        count_true([has_light[p]
                                    for p in neighbors]) == problem[y][x])

    is_sat = solver.solve()
    return is_sat, has_light


def compute_score(ans):
    score = 0
    for v in ans:
        if v.sol is not None:
            score += 1
    return score


def generate_akari(height, width, no_easy=False, verbose=False):
    def pretest(problem):
        visited = [[False for _ in range(width)] for _ in range(height)]

        def visit(y, x):
            if not (0 <= y < height and 0 <= x < width and problem[y][x] == -2
                    and not visited[y][x]):
                return
            visited[y][x] = True
            visit(y - 1, x)
            visit(y + 1, x)
            visit(y, x - 1)
            visit(y, x + 1)

        n_component = 0
        for y in range(height):
            for x in range(width):
                if problem[y][x] == -2 and not visited[y][x]:
                    n_component += 1
                    visit(y, x)
        if n_component != 1:
            return False
        if not no_easy:
            return True
        for y in range(height):
            for x in range(width):
                if problem[y][x] >= 0:
                    n_adj = (1 if y > 0 and problem[y - 1][x] == -2 else 0) + (
                        1 if x > 0 and problem[y][x - 1] == -2 else
                        0) + (1 if y < height - 1 and problem[y + 1][x] == -2
                              else 0) + (1 if x < width - 1
                                         and problem[y][x + 1] == -2 else 0)
                    if problem[y][x] >= n_adj - 1:
                        return False
        return True

    pattern = [-2, -1, 1, 2] if no_easy else [-2, -1, 0, 1, 2, 3, 4]
    generated = generate_problem(
        lambda problem: solve_akari(height, width, problem),
        builder_pattern=ArrayBuilder2D(height,
                                       width,
                                       pattern,
                                       default=-2,
                                       symmetry=True),
        clue_penalty=lambda problem: count_non_default_values(
            problem, default=-2, weight=5),
        pretest=pretest,
        verbose=verbose)
    return generated


def _main():
    if len(sys.argv) == 1:
        # generated example
        # https://twitter.com/semiexp/status/1225770511080144896
        height = 10
        width = 10
        problem = [
            [-2, -2,  2, -2, -2, -2, -2, -2, -2, -2],  # noqa: E201
            [-2, -2, -2, -2, -2, -2, -2, -2,  2, -2],  # noqa: E201
            [-2, -2, -2, -2, -2, -2, -2, -1, -2, -2],  # noqa: E201
            [-1, -2, -2, -2,  3, -2, -2, -2, -2, -2],  # noqa: E201
            [-2, -2, -2, -2, -2, -1, -2, -2, -2, -1],  # noqa: E201
            [ 2, -2, -2, -2,  2, -2, -2, -2, -2, -2],  # noqa: E201
            [-2, -2, -2, -2, -2,  3, -2, -2, -2, -1],  # noqa: E201
            [-2, -2, -1, -2, -2, -2, -2, -2, -2, -2],  # noqa: E201
            [-2,  2, -2, -2, -2, -2, -2, -2, -2, -2],  # noqa: E201
            [-2, -2, -2, -2, -2, -2, -2, -1, -2, -2],  # noqa: E201
        ]  # yapf: disable
        is_sat, has_light = solve_akari(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(
                util.stringify_array(has_light, {
                    True: 'O',
                    False: '.',
                    None: '?'
                }))
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            problem = generate_akari(height, width, verbose=True)
            if problem is not None:
                print(
                    util.stringify_array(problem, {
                        -2: '.',
                        -1: '#',
                        0: '0',
                        1: '1',
                        2: '2',
                        3: '3',
                        4: '4'
                    }))
                print('', flush=True)


if __name__ == '__main__':
    _main()
