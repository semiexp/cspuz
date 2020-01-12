from cspuz import Solver
from cspuz.constraints import alldifferent
from cspuz.puzzle import util


def solve_sudoku(problem, n=3):
    size = n * n
    solver = Solver()
    answer = solver.int_array((size, size), 1, size)
    solver.add_answer_key(answer)
    for i in range(size):
        solver.ensure(alldifferent(answer[i, :]))
        solver.ensure(alldifferent(answer[:, i]))
    for y in range(n):
        for x in range(n):
            solver.ensure(alldifferent(answer[y*n:(y+1)*n, x*n:(x+1)*n]))
    for y in range(size):
        for x in range(size):
            if problem[y][x] >= 1:
                solver.ensure(answer[y, x] == problem[y][x])
    is_sat = solver.solve()

    return is_sat, answer


def _main():
    problem = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
    is_sat, answer = solve_sudoku(problem)
    if is_sat:
        print(util.stringify_array(answer, dict([(None, '?')] + [(i, str(i)) for i in range(1, 10)])))


if __name__ == '__main__':
    _main()
