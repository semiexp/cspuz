from cspuz import Solver
from cspuz.constraints import BoolVars
from cspuz.grid_frame import BoolGridFrame
from cspuz import backend


def solve_slitherlink(height, width, problem):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height, width)
    grid_frame.single_loop()
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 0:
                solver.ensure(BoolVars(
                    [grid_frame[y * 2 + 1, x * 2 + 0],
                     grid_frame[y * 2 + 1, x * 2 + 2],
                     grid_frame[y * 2 + 0, x * 2 + 1],
                     grid_frame[y * 2 + 2, x * 2 + 1]]
                ).count_true() == problem[y][x])

    solver.add_answer_key(grid_frame.all_edges())
    solver.solve()

    for y in range(2 * height + 1):
        for x in range(2 * width + 1):
            if y % 2 == 0 and x % 2 == 0:
                print('+', end='')
            elif y % 2 == 1 and x % 2 == 0:
                if grid_frame[y, x].sol == True:
                    print('|', end='')
                elif grid_frame[y, x].sol == False:
                    print('x', end='')
                else:
                    print(' ', end='')
            elif y % 2 == 0 and x % 2 == 1:
                if grid_frame[y, x].sol == True:
                    print('-', end='')
                elif grid_frame[y, x].sol == False:
                    print('x', end='')
                else:
                    print(' ', end='')
            else:
                n = problem[y // 2][x // 2]
                print(n if n >= 0 else ' ', end='')
        print()


if __name__ == '__main__':
    # original example: http://pzv.jp/p.html?slither/4/4/dgdh2c7b
    height = 4
    width = 4
    problem = [
        [ 3, -1, -1, -1],
        [ 3, -1, -1, -1],
        [-1,  2,  2, -1],
        [-1,  2, -1,  1]
    ]
    solve_slitherlink(height, width, problem)
