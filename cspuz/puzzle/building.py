import sys

from cspuz import Solver
from cspuz.constraints import alldifferent, fold_and
from cspuz.puzzle import util
from cspuz.generator import Choice, generate_problem, build_neighbor_generator, count_non_default_values


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


def generate_building(size, verbose=False):
    initial, neighbor = build_neighbor_generator([[Choice(range(0, size + 1), default=0) for _ in range(size)] for _ in range(4)])
    generated = generate_problem(lambda problem: solve_building(size, *problem),
                                 initial,
                                 neighbor,
                                 clue_penalty=lambda problem: count_non_default_values(problem, default=0, weight=3.0),
                                 verbose=verbose)
    if generated is not None:
        return generated


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
