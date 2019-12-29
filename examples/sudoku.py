from cspuz import Solver, latin_square


def solve_sudoku(problem, n=3):
    # solve N*N sudoku, where N=n*n
    size = n * n
    solver = Solver()
    grid = latin_square(solver, size)
    solver.add_answer_key(grid[:, :])
    for y in range(n):
        for x in range(n):
            solver.ensure(grid[y*n:(y+1)*n, x*n:(x+1)*n].alldifferent())
    for y in range(size):
        for x in range(size):
            if problem[y][x] >= 1:
                solver.ensure(grid[y, x] == problem[y][x])
    solver.solve()

    for y in range(size):
        for x in range(size):
            if grid[y, x].sol is None:
                print('.', end=' ')
            else:
                print(grid[y, x].sol, end=' ')
        print()


def main():
    # https://commons.wikimedia.org/wiki/File:Sudoku-by-L2G-20050714.svg
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
    solve_sudoku(problem)


if __name__ == '__main__':
    main()
