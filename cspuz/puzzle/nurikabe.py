from cspuz import Solver, graph, count_true
from cspuz.puzzle import util


def solve_nurikabe(height, width, problem):
    solver = Solver()
    clues = []
    for y in range(height):
        for x in range(width):
            if problem[y][x] >= 1:
                clues.append((y, x, problem[y][x]))
    division = solver.int_array((height, width), 0, len(clues))
    roots = [None] + list(map(lambda x: (x[0], x[1]), clues))
    graph.division_connected(solver, division, len(clues) + 1, roots=roots)
    is_white = solver.bool_array((height, width))
    solver.ensure(is_white == (division != 0))
    solver.add_answer_key(is_white)

    solver.ensure((is_white[:-1, :] & is_white[1:, :]).then(division[:-1, :] == division[1:, :]))
    solver.ensure((is_white[:, :-1] & is_white[:, 1:]).then(division[:, :-1] == division[:, 1:]))
    solver.ensure(is_white[:-1, :-1] | is_white[:-1, 1:] | is_white[1:, :-1] | is_white[1:, 1:])
    for i, (y, x, n) in enumerate(clues):
        solver.ensure(count_true(division == (i + 1)) == n)

    is_sat = solver.solve()

    return is_sat, is_white


def main():
    # https://twitter.com/semiexp/status/1222541993638678530
    problem = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 7, 0, 0, 0, 0, 0],
        [0, 0, 0, 7, 0, 0, 0, 0, 9, 0],
        [0, 0, 0, 0, 0, 0, 0, 7, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 7, 0, 0, 0, 7, 0, 0, 0],
        [0, 0, 0, 0, 0, 7, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    is_sat, is_white = solve_nurikabe(10, 10, problem)
    print('has answer:', is_sat)
    if is_sat:
        print(util.stringify_array(is_white, {
            None: '?',
            True: '.',
            False: '#'
        }))


if __name__ == '__main__':
    main()
