from cspuz import Solver, graph
from cspuz.constraints import count_true
from cspuz.grid_frame import BoolGridFrame
from cspuz.puzzle import util


def solve_yajilin(height, width, problem):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height - 1, width - 1)
    is_passed = graph.active_edges_single_cycle(solver, grid_frame)
    black_cell = solver.bool_array((height, width))
    graph.active_vertices_not_adjacent(solver, black_cell)
    solver.add_answer_key(grid_frame)
    solver.add_answer_key(black_cell)

    for y in range(height):
        for x in range(width):
            if problem[y][x] != '..':
                # clue
                solver.ensure(~is_passed[y, x])
                solver.ensure(~black_cell[y, x])

                if problem[y][x][0] == '^':
                    solver.ensure(count_true(black_cell[0:y, x]) == int(problem[y][x][1:]))
                elif problem[y][x][0] == 'v':
                    solver.ensure(count_true(black_cell[(y + 1):height, x]) == int(problem[y][x][1:]))
                elif problem[y][x][0] == '<':
                    solver.ensure(count_true(black_cell[y, 0:x]) == int(problem[y][x][1:]))
                elif problem[y][x][0] == '>':
                    solver.ensure(count_true(black_cell[y, (x + 1):width]) == int(problem[y][x][1:]))
            else:
                solver.ensure(is_passed[y, x] != black_cell[y, x])

    is_sat = solver.solve()
    return is_sat, grid_frame, is_passed


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
    is_sat, is_line, is_passed = solve_yajilin(height, width, problem)
    print('has answer:', is_sat)
    if is_sat:
        print(util.stringify_grid_frame(is_line))
