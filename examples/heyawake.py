from cspuz import Solver, BoolGrid


def solve_heyawake(height, width, problem):
    solver = Solver()
    grid = BoolGrid(solver, height, width)
    solver.add_answer_key(grid[:, :])
    grid.forbid_adjacent_true_cells()
    grid.connect_false_cells()

    for y0, x0, y1, x1, n in problem:
        if n >= 0:
            solver.ensure(grid[y0:y1, x0:x1].count_true() == n)
        if 0 < y0 and y1 < height:
            for x in range(x0, x1):
                solver.ensure(grid[(y0 - 1):(y1 + 1), x].fold_or())
        if 0 < x0 and x1 < width:
            for y in range(y0, y1):
                solver.ensure(grid[y, (x0 - 1):(x1 + 1)].fold_or())

    solver.solve()

    for y in range(height):
        for x in range(width):
            s = grid[y, x].sol
            if s is None:
                print('? ', end='')
            elif s:
                print('# ', end='')
            else:
                print('. ', end='')
        print()


if __name__ == '__main__':
    # original example: http://pzv.jp/p.html?heyawake/6/6/aa66aapv0fu0g2i3k
    height = 6
    width = 6
    problem = [
        (0, 0, 1, 2, -1),
        (0, 2, 2, 4, 2),
        (0, 4, 1, 6, -1),
        (1, 0, 2, 2, -1),
        (1, 4, 3, 6, -1),
        (2, 0, 4, 3, 3),
        (2, 3, 4, 4, -1),
        (3, 4, 4, 6, -1),
        (4, 0, 6, 2, -1),
        (4, 2, 6, 4, -1),
        (4, 4, 6, 6, -1)
    ]
    solve_heyawake(height, width, problem)
