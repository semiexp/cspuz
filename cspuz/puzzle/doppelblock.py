import sys

from cspuz import Solver
from cspuz.constraints import fold_or, count_true
from cspuz.generator import generate_problem, count_non_default_values, ArrayBuilder2D
from cspuz.puzzle import util


def solve_doppelblock(n, clue_row, clue_column):
    solver = Solver()
    answer = solver.int_array((n, n), 0, n - 2)
    solver.add_answer_key(answer)

    def sequence_constraint(cells, v):
        s = 0
        for i in range(n):
            s += (fold_or(cells[:i] == 0) & fold_or(cells[i+1:] == 0)).cond(cells[i], 0)
        return s == v

    def occurrence_constraint(cells):
        solver.ensure(count_true(cells == 0) == 2)
        for i in range(1, n - 1):
            solver.ensure(count_true(cells == i) == 1)

    for i in range(n):
        occurrence_constraint(answer[i, :])
        occurrence_constraint(answer[:, i])
        if clue_row[i] >= 0:
            solver.ensure(sequence_constraint(answer[i, :], clue_row[i]))
        if clue_column[i] >= 0:
            solver.ensure(sequence_constraint(answer[:, i], clue_column[i]))

    is_sat = solver.solve()
    return is_sat, answer


def generate_doppelblock(n, verbose=False):
    max_sum = (n - 2) * (n - 1) // 2
    generated = generate_problem(lambda problem: solve_doppelblock(n, problem[0], problem[1]),
                                 builder_pattern=ArrayBuilder2D(2, n, [-1] + list(range(0, max_sum + 1)), default=-1),
                                 clue_penalty=lambda problem: count_non_default_values(problem, default=-1, weight=10),
                                 verbose=verbose)
    return generated


def _main():
    if len(sys.argv) == 1:
        # https://puzsq.jp/main/puzzle_play.php?pid=10025
        n = 5
        row = [5, -1, 5, -1, -1]
        column = [3, -1, -1, 1, -1]
        is_sat, answer = solve_doppelblock(n, row, column)
        if is_sat:
            print(util.stringify_array(answer, str))
    else:
        n = int(sys.argv[1])
        while True:
            problem = generate_doppelblock(n)
            if problem is not None:
                print(problem, flush=True)


if __name__ == '__main__':
    _main()
