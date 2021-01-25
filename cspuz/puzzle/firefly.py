import sys
import subprocess

import cspuz
from cspuz import Solver
from cspuz.array import BoolArray1D
from cspuz.grid_frame import BoolGridFrame
from cspuz.constraints import count_true
from cspuz.puzzle import util
from cspuz.generator import (generate_problem, count_non_default_values,
                             ArrayBuilder2D)


def solve_firefly(height, width, problem):
    solver = Solver()

    has_line = BoolGridFrame(solver, height - 1, width - 1)
    solver.add_answer_key(has_line)

    line_ul = BoolGridFrame(solver, height - 1, width - 1)
    line_dr = BoolGridFrame(solver, height - 1, width - 1)
    solver.ensure(
        BoolArray1D(list(has_line)) == (BoolArray1D(list(line_ul)) | BoolArray1D(list(line_dr))))
    solver.ensure(~(BoolArray1D(list(line_ul)) & BoolArray1D(list(line_dr))))

    # unicyclic (= connected)
    ignored_edge = BoolGridFrame(solver, height - 1, width - 1)
    solver.ensure(count_true(ignored_edge) == 1)
    rank = solver.int_array((height, width), 0, height * width - 1)
    solver.ensure(
        (line_ul.horizontal
         & ~ignored_edge.horizontal).then(rank[:, :-1] < rank[:, 1:]))
    solver.ensure((line_ul.vertical
                   & ~ignored_edge.vertical).then(rank[:-1, :] < rank[1:, :]))
    solver.ensure(
        (line_dr.horizontal
         & ~ignored_edge.horizontal).then(rank[:, :-1] > rank[:, 1:]))
    solver.ensure((line_dr.vertical
                   & ~ignored_edge.vertical).then(rank[:-1, :] > rank[1:, :]))

    max_n_turn = 0
    for y in range(height):
        for x in range(width):
            if problem[y][x][0] != '.' and problem[y][x][1] != '?':
                max_n_turn = max(max_n_turn, int(problem[y][x][1:]))
    n_turn_unknown = max_n_turn + 1
    n_turn_horizontal = solver.int_array((height, width - 1), 0,
                                         max_n_turn + 1)
    n_turn_vertical = solver.int_array((height - 1, width), 0, max_n_turn + 1)

    for y in range(height):
        for x in range(width):
            # u, d, l, r
            adj = []  # (line_in, line_out, # turn)

            if y > 0:
                adj.append((line_dr.vertical[y - 1, x],
                            line_ul.vertical[y - 1, x], n_turn_vertical[y - 1,
                                                                        x]))
            else:
                adj.append(None)
            if y < height - 1:
                adj.append((line_ul.vertical[y, x], line_dr.vertical[y, x],
                            n_turn_vertical[y, x]))
            else:
                adj.append(None)
            if x > 0:
                adj.append(
                    (line_dr.horizontal[y, x - 1],
                     line_ul.horizontal[y, x - 1], n_turn_horizontal[y,
                                                                     x - 1]))
            else:
                adj.append(None)
            if x < width - 1:
                adj.append((line_ul.horizontal[y, x], line_dr.horizontal[y, x],
                            n_turn_horizontal[y, x]))
            else:
                adj.append(None)

            if problem[y][x][0] != '.':
                if problem[y][x][0] == '^':
                    out_idx = 0
                elif problem[y][x][0] == 'v':
                    out_idx = 1
                elif problem[y][x][0] == '<':
                    out_idx = 2
                elif problem[y][x][0] == '>':
                    out_idx = 3
                else:
                    raise ValueError('invalid direction: {}'.format(
                        problem[y][x][0]))
                if adj[out_idx] is None:
                    solver.ensure(False)
                    break
                solver.ensure(adj[out_idx][1])
                if problem[y][x][1] != '?':
                    solver.ensure(adj[out_idx][2] == int(problem[y][x][1:]))
                else:
                    solver.ensure(adj[out_idx][2] == n_turn_unknown)
                for i in range(4):
                    if adj[i] is not None and i != out_idx:
                        solver.ensure(~adj[i][1])
                        solver.ensure(
                            adj[i][0].then((adj[i][2] == 0)
                                           | (adj[i][2] == n_turn_unknown)))
            else:
                adj_present = list(filter(lambda x: x is not None, adj))
                solver.ensure(
                    count_true(map(lambda x: x[0], adj_present)) <= 1)
                solver.ensure(
                    count_true(map(lambda x: x[0], adj_present)) == count_true(
                        map(lambda x: x[1], adj_present)))

                for i in range(4):
                    for j in range(4):
                        if adj[i] is not None and adj[j] is not None \
                                and i != j:
                            if (i // 2) == (j // 2):  # straight
                                solver.ensure(
                                    (adj[i][0]
                                     & adj[j][1]).then(adj[i][2] == adj[j][2]))
                            else:
                                solver.ensure(
                                    (adj[i][0] & adj[j][1]
                                     ).then(((adj[i][2] == n_turn_unknown)
                                             & (adj[j][2] == n_turn_unknown))
                                            | (adj[i][2] == adj[j][2] + 1)))
    is_sat = solver.solve()
    return is_sat, has_line


def generate_firefly(height, width, min_clue=0, max_clue=5, verbose=False):
    cand = ['..']
    for d in ['^', 'v', '<', '>']:
        cand.append(d + '?')
        for i in range(min_clue, max_clue + 1):
            cand.append(d + str(i))
    generated = generate_problem(
        lambda problem: solve_firefly(height, width, problem),
        builder_pattern=ArrayBuilder2D(height, width, cand, default='..'),
        clue_penalty=lambda problem: count_non_default_values(
            problem, default='..', weight=10),
        verbose=verbose)
    return generated


def _main():
    if len(sys.argv) == 1:
        # http://pzv.jp/p.html?firefly/6/6/a2.k4.b27a45g22i
        height = 6
        width = 6
        problem = [
            ['..', 'v?', '..', '..', '..', '..'],
            ['..', '..', '..', '..', '..', '..'],
            ['..', '>?', '..', '..', 'v7', '..'],
            ['>5', '..', '..', '..', '..', '..'],
            ['..', '..', 'v2', '..', '..', '..'],
            ['..', '..', '..', '..', '..', '..'],
        ]
        is_sat, is_line = solve_firefly(height, width, problem)
        print('has answer:', is_sat)
        if is_sat:
            print(util.stringify_grid_frame(is_line))
    else:
        cspuz.config.solver_timeout = 600.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                problem = generate_firefly(height,
                                           width,
                                           min_clue=2,
                                           max_clue=7,
                                           verbose=True)
                if problem is not None:
                    print(util.stringify_array(problem))
                    print(flush=True)
            except subprocess.TimeoutExpired:
                print('timeout', file=sys.stderr)


if __name__ == '__main__':
    _main()
