from cspuz import Solver, BoolGrid, BoolGridFrame, BoolVars


def solve_yajilin(height, width, problem):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height - 1, width - 1)
    passed = grid_frame.single_loop()
    black_cell = BoolGrid(solver, height, width)
    black_cell.forbid_adjacent_true_cells()
    solver.add_answer_key(grid_frame.all_edges())
    solver.add_answer_key(black_cell[:, :])

    for y in range(height):
        for x in range(width):
            if problem[y][x] != '..':
                # clue
                solver.ensure(passed[y, x] == False)
                solver.ensure(black_cell[y, x] == False)

                if problem[y][x][0] == '^':
                    solver.ensure(black_cell[0:y, x].count_true() == int(problem[y][x][1:]))
                elif problem[y][x][0] == 'v':
                    solver.ensure(black_cell[(y + 1):height, x].count_true() == int(problem[y][x][1:]))
                elif problem[y][x][0] == '<':
                    solver.ensure(black_cell[y, 0:x].count_true() == int(problem[y][x][1:]))
                elif problem[y][x][0] == '>':
                    solver.ensure(black_cell[y, (x + 1):width].count_true() == int(problem[y][x][1:]))
            else:
                solver.ensure(passed[y, x] != black_cell[y, x])

    solver.solve()

    for y in range(2 * height - 1):
        for x in range(2 * width - 1):
            if y % 2 == 0 and x % 2 == 0:
                if black_cell[y // 2, x // 2].sol == True:
                    print('#', end='')
                else:
                    print('+', end='')
            elif y % 2 != x % 2:
                edge = grid_frame[y, x].sol
                if black_cell[y // 2, x // 2].sol or black_cell[(y + 1) // 2, (x + 1) // 2].sol or \
                        problem[y // 2][x // 2] != '..' or problem[(y + 1) // 2][(x + 1) // 2] != '..':
                    edge = None
                if edge is None:
                    print(' ', end='')
                elif edge:
                    print('|' if y % 2 == 1 else '-', end='')
                else:
                    print(' ', end='')
            else:
                print(' ', end='')
        print()


if __name__ == '__main__':
    # https://twitter.com/semiexp/status/1206956338556764161
    height = 10
    width = 10
    problem = [
        ['..', '..', '..', '..', '..', '..', '..', '..', '..', '..'],
        ['..', '..', '..', '..', '..', '..', '..', '..', '..', '..'],
        ['..', '..', 'v0', '..', '..', '>2', '..', '..', '..', '..'],
        ['..', '..', '..', '..', '..', '..', '..', '..', '..', '..'],
        ['..', '..', '..', '..', '..', '..', '..', '..', '..', '..'],
        ['..', '..', '..', '..', '..', '..', '..', '..', '^1', '..'],
        ['..', '..', '..', '..', '..', '..', '..', '..', '..', '..'],
        ['..', '..', '^0', '..', '^3', '..', '..', '>1', '..', '..'],
        ['..', '..', '..', '..', '..', '..', '..', '..', '..', '..'],
        ['..', '..', '..', '..', '..', '..', '..', '>0', '..', '..'],
    ]
    solve_yajilin(height, width, problem)
