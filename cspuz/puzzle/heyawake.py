from cspuz import Solver, graph
from cspuz.constraints import count_true, fold_or
from cspuz.puzzle import util


def solve_heyawake(height, width, problem):
    solver = Solver()
    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)
    graph.active_vertices_not_adjacent_and_not_segmenting(solver, is_black)
    for y0, x0, y1, x1, n in problem:
        if n >= 0:
            solver.ensure(count_true(is_black[y0:y1, x0:x1]) == n)
        if 0 < y0 and y1 < height:
            for x in range(x0, x1):
                solver.ensure(fold_or(is_black[(y0 - 1):(y1 + 1), x]))
        if 0 < x0 and x1 < width:
            for y in range(y0, y1):
                solver.ensure(fold_or(is_black[y, (x0 - 1):(x1 + 1)]))
    is_sat = solver.solve()

    return is_sat, is_black


def _main():
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
    is_sat, is_black = solve_heyawake(height, width, problem)
    print('has answer:', is_sat)
    if is_sat:
        print(util.stringify_array(is_black, {
            None: '?',
            True: '#',
            False: '.'
        }))


if __name__ == '__main__':
    _main()
