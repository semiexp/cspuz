import argparse
import random
import math
import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.constraints import count_true, fold_or, fold_and

from cspuz.grid_frame import BoolGridFrame
from cspuz.puzzle import util


def solve_slalom(height, width, origin, is_black, gates, reference_sol_loop=None):
    solver = Solver()
    loop = BoolGridFrame(solver, height - 1, width - 1)
    loop_dir = BoolGridFrame(solver, height - 1, width - 1)
    solver.add_answer_key(loop.all_edges())

    graph.active_edges_single_cycle(solver, loop)

    gate_ord = solver.int_array((height, width), 0, len(gates))
    passed = solver.bool_array((height, width))

    gate_id = [[None for _ in range(width)] for _ in range(height)]
    for y, x, d, l, n in gates:
        if d == 0:  # horizontal
            gate_cells = [(y, x + i) for i in range(l)]
        elif d == 1:  # vertical
            gate_cells = [(y + i, x) for i in range(l)]
        for y2, x2 in gate_cells:
            gate_id[y2][x2] = n
        solver.ensure(count_true([passed[y2, x2] for y2, x2 in gate_cells]) == 1)
    solver.ensure(passed[origin])
    for y in range(height):
        for x in range(width):
            neighbors = []
            if y > 0:
                neighbors.append((y - 1, x))
            if y < height - 1:
                neighbors.append((y + 1, x))
            if x > 0:
                neighbors.append((y, x - 1))
            if x < width - 1:
                neighbors.append((y, x + 1))

            # in-degree, out-degree
            solver.ensure(count_true(
                [loop[y + y2, x + x2] & (loop_dir[y + y2, x + x2] != ((y2, x2) < (y, x))) for y2, x2 in neighbors]
            ) == passed[y, x].cond(1, 0))
            solver.ensure(count_true(
                [loop[y + y2, x + x2] & (loop_dir[y + y2, x + x2] == ((y2, x2) < (y, x))) for y2, x2 in neighbors]
            ) == passed[y, x].cond(1, 0))

            if is_black[y][x]:
                solver.ensure(~passed[y, x])
                continue
            if (y, x) == origin:
                continue
            if gate_id[y][x] is None:
                for y2, x2 in neighbors:
                    solver.ensure((loop[y + y2, x + x2] & (loop_dir[y + y2, x + x2] != ((y2, x2) < (y, x)))).then(
                        (gate_ord[y2, x2] == gate_ord[y, x])
                    ))
            else:
                for y2, x2 in neighbors:
                    solver.ensure((loop[y + y2, x + x2] & (loop_dir[y + y2, x + x2] != ((y2, x2) < (y, x)))).then(
                        (gate_ord[y2, x2] == gate_ord[y, x] - 1)
                    ))
                if gate_id[y][x] >= 1:
                    solver.ensure(passed[y, x].then(gate_ord[y, x] == gate_id[y][x]))

    # auxiliary constraint
    for y0 in range(height):
        for x0 in range(width):
            for y1 in range(height):
                for x1 in range(width):
                    if (y0, x0) < (y1, x1) and gate_id[y0][x0] is not None and gate_id[y1][x1] is not None:
                        solver.ensure((passed[y0, x0] & passed[y1, x1]).then(gate_ord[y0, x0] != gate_ord[y1, x1]))

    if reference_sol_loop is not None:
        avoid_reference_sol = []
        for y in range(height):
            for x in range(width):
                if y < height - 1:
                    avoid_reference_sol.append(loop.vertical[y, x] != reference_sol_loop.vertical[y, x].sol)
                if x < width - 1:
                    avoid_reference_sol.append(loop.horizontal[y, x] != reference_sol_loop.horizontal[y, x].sol)
        solver.ensure(fold_or(avoid_reference_sol))

        is_sat = solver.find_answer()
        return is_sat, loop
    else:
        is_sat = solver.solve()
        return is_sat, loop


def generate_slalom_initial_placement(height, width,
                                      n_min_gates=None,
                                      n_max_gates=None,
                                      n_max_isolated_black_cells=None,
                                      no_adjacent_black_cell=False,
                                      no_facing_length_two=False,
                                      no_space_2x2=False,
                                      black_cell_in_every_3x3=False,
                                      min_go_through=0):
    solver = Solver()
    loop = BoolGridFrame(solver, height - 1, width - 1)
    is_black = solver.bool_array((height, width))
    is_horizontal = solver.bool_array((height, width))
    is_vertical = solver.bool_array((height, width))

    solver.ensure(~(is_black & is_horizontal))
    solver.ensure(~(is_black & is_vertical))
    solver.ensure(~(is_horizontal & is_vertical))
    solver.ensure(~(is_horizontal[0, :]))
    solver.ensure(~(is_horizontal[-1, :]))
    solver.ensure(~(is_vertical[:, 0]))
    solver.ensure(~(is_vertical[:, -1]))

    is_passed = graph.active_edges_single_cycle(solver, loop)

    # --------- board must be valid as a problem ---------

    # loop constraints
    for y in range(height):
        for x in range(width):
            if y > 0:
                solver.ensure(is_black[y, x].then(~loop.vertical[y - 1, x]))
                solver.ensure(is_vertical[y, x].then(~loop.vertical[y - 1, x]))
            if y < height - 1:
                solver.ensure(is_black[y, x].then(~loop.vertical[y, x]))
                solver.ensure(is_vertical[y, x].then(~loop.vertical[y, x]))
            if x > 0:
                solver.ensure(is_black[y, x].then(~loop.horizontal[y, x - 1]))
                solver.ensure(is_horizontal[y, x].then(~loop.horizontal[y, x - 1]))
            if x < width - 1:
                solver.ensure(is_black[y, x].then(~loop.horizontal[y, x]))
                solver.ensure(is_horizontal[y, x].then(~loop.horizontal[y, x]))

    # gates must be closed
    solver.ensure(is_vertical[1:, :].then(is_vertical[:-1, :] | is_black[:-1, :]))
    solver.ensure(is_vertical[:-1, :].then(is_vertical[1:, :] | is_black[1:, :]))
    solver.ensure(is_horizontal[:, 1:].then(is_horizontal[:, :-1] | is_black[:, :-1]))
    solver.ensure(is_horizontal[:, :-1].then(is_horizontal[:, 1:] | is_black[:, 1:]))
    # each horizontal gate must be passed exactly once
    for y in range(1, height - 1):
        for x in range(width):
            on_loop = []
            for x2 in range(width):
                cond = [is_passed[y, x2]]
                if x2 < x:
                    cond += [is_horizontal[y, i] for i in range(x2, x)]
                elif x < x2:
                    cond += [is_horizontal[y, i] for i in range(x + 1, x2 + 1)]
                on_loop.append(fold_and(cond))
            solver.ensure(is_horizontal[y, x].then(count_true(on_loop) == 1))
    # each vertical gate must be passed exactly once
    for y in range(height):
        for x in range(1, width - 1):
            on_loop = []
            for y2 in range(width):
                cond = [is_passed[y2, x]]
                if y2 < y:
                    cond += [is_vertical[i, x] for i in range(y2, y)]
                elif y < y2:
                    cond += [is_vertical[i, x] for i in range(y + 1, y2 + 1)]
                on_loop.append(fold_and(cond))
            solver.ensure(is_vertical[y, x].then(count_true(on_loop) == 1))

    # --------- loop must be canonical ---------

    # for simplicity, no stacked gates (although this is not necessary for the canonicity)
    solver.ensure(~(is_horizontal[:-1, :] & is_horizontal[1:, :]))
    solver.ensure(~(is_vertical[:, :-1] & is_vertical[:, 1:]))
    for y in range(height):
        for x in range(width):
            if 0 < y < height - 1:
                if x == 0 or x == width - 1:
                    solver.ensure(is_horizontal[y, x].then(~is_black[y - 1, x] & ~is_black[y + 1, x]))
                else:
                    solver.ensure((is_horizontal[y, x] & (is_black[y - 1, x] | is_black[y + 1, x])).then(
                        is_horizontal[y, x - 1] & is_horizontal[y, x + 1] & ~is_black[y - 1, x - 1] & ~is_black[y + 1, x - 1] & ~is_black[y + 1, x - 1] & ~is_black[y + 1, x + 1]
                    ))
            if 0 < x < width - 1:
                if y == 0 or y == height - 1:
                    solver.ensure(is_vertical[y, x].then(~is_black[y, x - 1] & ~is_black[y, x + 1]))
                else:
                    solver.ensure((is_vertical[y, x] & (is_black[y, x - 1] | is_black[y, x + 1])).then(
                        is_vertical[y - 1, x] & is_vertical[y + 1, x] & ~is_black[y - 1, x - 1] & ~is_black[y + 1, x - 1] & ~is_black[y + 1, x - 1] & ~is_black[y + 1, x + 1]
                    ))

    # no detour
    for y in range(height - 1):
        for x in range(width - 1):
            solver.ensure(count_true(loop.cell_neighbors(y, x)) <= 2)
            solver.ensure(fold_and(~is_black[y:y+2, x:x+2], ~is_horizontal[y:y+2, x:x+2], ~is_vertical[y:y+2, x:x+2])
                          .then(count_true(loop.cell_neighbors(y, x)) + 1 < count_true(is_passed[y:y+2, x:x+2])))

    # no ambiguous L-shaped turning
    for y in range(height - 1):
        for x in range(width - 1):
            for dy in [0, 1]:
                for dx in [0, 1]:
                    solver.ensure(~fold_and([loop.horizontal[y + dy, x],
                                             loop.vertical[y, x + dx],
                                             ~is_vertical[y + dy, x + 1 - dx],
                                             ~is_horizontal[y + 1 - dx, x + dx],
                                             ~is_black[y + 1 - dy, x + 1 - dx],
                                             count_true(is_passed[y:y+2, x:x+2]) == 3]))

    # no ambiguous L-shaped turning involving gates
    for y in range(height - 1):
        for x in range(width - 2):
            solver.ensure(fold_and(is_vertical[y:y+2, x+1], ~is_black[y:y+2, x:x+3])
                          .then(count_true(loop.horizontal[y, x], loop.horizontal[y + 1, x],
                                           loop.vertical[y, x], loop.vertical[y, x + 2]) + 1
                                < count_true(is_passed[y:y+2, x], is_passed[y:y+2, x+2])))
    for y in range(height - 2):
        for x in range(width - 1):
            solver.ensure(fold_and(is_horizontal[y+1, x:x+2], ~is_black[y:y+3, x:x+2])
                          .then(count_true(loop.vertical[y, x], loop.vertical[y, x + 1],
                                           loop.horizontal[y, x], loop.horizontal[y + 2, x]) + 1
                                < count_true(is_passed[y, x:x+2], is_passed[y+2, x:x+2])))

    # no dead ends
    for y in range(height):
        for x in range(width):
            solver.ensure((~is_black[y, x]).then(count_true(~is_black.four_neighbors(y, x)) >= 2))

    # --------- avoid "trivial" problems ---------
    solver.ensure(count_true(is_vertical) > 5)
    solver.ensure(count_true(is_horizontal) > 4)

    if n_max_isolated_black_cells is not None:
        lonely_black_cell = []
        for y in range(height):
            for x in range(width):
                cond = [is_black[y, x]]
                if y > 0:
                    cond.append(~is_vertical[y - 1, x])
                if y < height - 1:
                    cond.append(~is_vertical[y + 1, x])
                if x > 0:
                    cond.append(~is_horizontal[y, x - 1])
                if x < width - 1:
                    cond.append(~is_horizontal[y, x + 1])
                lonely_black_cell.append(fold_and(cond))
        solver.ensure(count_true(lonely_black_cell) <= n_max_isolated_black_cells)

    short_gates = []
    for y in range(height):
        for x in range(width):
            g1 = fold_and([
                is_vertical[y, x],
                ~is_vertical[y - 1, x] if y > 0 else True,
                ~is_vertical[y + 1, x] if y < height - 1 else True
            ])
            g2 = fold_and([
                is_horizontal[y, x],
                ~is_horizontal[y, x - 1] if x > 0 else True,
                ~is_horizontal[y, x + 1] if x < width - 1 else True
            ])
            if 0 < y < height - 1 and 0 < x < width - 1:
                short_gates.append(g1)
                short_gates.append(g2)
                solver.ensure((g1 | g2).then(~is_black[y - 1, x - 1] & ~is_black[y - 1, x + 1] & ~is_black[y + 1, x - 1] & ~is_black[y + 1, x + 1]))
            else:
                solver.ensure(~g1)
                solver.ensure(~g2)

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            solver.ensure(count_true(
                is_horizontal[y - 1, x] & is_black[y - 1, x - 1] & is_black[y - 1, x + 1],
                is_horizontal[y + 1, x] & is_black[y + 1, x - 1] & is_black[y + 1, x + 1],
                is_vertical[y, x - 1] & is_black[y - 1, x - 1] & is_black[y + 1, x - 1],
                is_vertical[y, x + 1] & is_black[y - 1, x + 1] & is_black[y + 1, x + 1],
            ) <= 1)
    # --------- ensure randomness ---------

    passed_constraints = [[0 for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if (y > 0 and passed_constraints[y - 1][x] != 0) or (x > 0 and passed_constraints[y][x - 1] != 0):
                continue
            passed_constraints[y][x] = max(0, random.randint(-20, 2))
    for y in range(height):
        for x in range(width):
            if passed_constraints[y][x] == 1:
                solver.ensure(is_passed[y, x])
            elif passed_constraints[y][x] == 2:
                solver.ensure(~is_passed[y, x])

    # --------- extra constraints ---------
    if n_min_gates is not None or n_max_gates is not None:
        gate_representative = []
        for y in range(height):
            for x in range(width):
                gate_representative.append(is_horizontal[y, x] & (~is_horizontal[y, x - 1] if x > 0 else True))
                gate_representative.append(is_vertical[y, x] & (~is_vertical[y - 1, x] if y > 0 else True))
        if n_min_gates is not None:
            solver.ensure(n_min_gates <= count_true(gate_representative))
        if n_max_gates is not None:
            solver.ensure(count_true(gate_representative) <= n_max_gates)

    if min_go_through > 0:
        go_through = []
        for y in range(height):
            for x in range(width):
                if y < height - 4 and 0 < x < width - 1:
                    go_through.append(fold_and(is_horizontal[y + 1, x],
                                               is_horizontal[y + 1, x - 1] | is_horizontal[y + 1, x + 1],
                                               ~is_black[y + 2, x - 1], ~is_black[y + 2, x + 1],
                                               is_horizontal[y + 3, x],
                                               is_horizontal[y + 3, x - 1] | is_horizontal[y + 3, x + 1],
                                               loop.vertical[y:y+4, x]))
                if x < width - 4 and 0 < y < height - 1:
                    go_through.append(fold_and(is_vertical[y, x + 1],
                                               is_vertical[y - 1, x + 1] | is_vertical[y + 1, x + 1],
                                               ~is_black[y - 1, x + 2], ~is_black[y + 1, x + 2],
                                               is_vertical[y, x + 3],
                                               is_vertical[y - 1, x + 3] | is_vertical[y + 1, x + 3],
                                               loop.horizontal[y, x:x+4]))
        solver.ensure(count_true(go_through) >= 2)

    if no_adjacent_black_cell:
        solver.ensure(~(is_black[:-1, :] & is_black[1:, :]))
        solver.ensure(~(is_black[:, :-1] & is_black[:, 1:]))
        solver.ensure(~(is_black[:-1, :-1] & is_black[1:, 1:]))
        solver.ensure(~(is_black[:-1, 1:] & is_black[1:, :-1]))

    if no_facing_length_two:
        for y in range(height):
            for x in range(width):
                if y <= height - 3 and x <= width - 4:
                    solver.ensure(~fold_and(is_black[y, x], is_black[y + 2, x], is_black[y, x + 3], is_black[y + 2, x + 3],
                                            is_horizontal[y, x + 1], is_horizontal[y, x + 2], is_horizontal[y + 2, x + 1], is_horizontal[y + 2, x + 2]))
                if y <= height - 4 and x <= width - 3:
                    solver.ensure(~fold_and(is_black[y, x], is_black[y, x + 2], is_black[y + 3, x], is_black[y + 3, x + 2],
                                            is_vertical[y + 1, x], is_vertical[y + 2, x], is_vertical[y + 1, x + 2], is_vertical[y + 2, x + 2]))

    if no_space_2x2:
        has_some = is_black | is_vertical | is_horizontal
        solver.ensure(has_some[:-1, :-1] | has_some[1:, :-1] | has_some[:-1, 1:] | has_some[1:, 1:])

    if black_cell_in_every_3x3:
        for y in range(-1, height - 2):
            for x in range(-1, width - 2):
                solver.ensure(fold_or(is_black[max(0, y):min(height, y+3), max(0, x):min(width, x+3)]))

    is_sat = solver.find_answer()
    if not is_sat:
        return None
    return loop, is_passed, is_black, is_horizontal, is_vertical


def generate_slalom(height, width, minify=True, **kwargs):
    initial = generate_slalom_initial_placement(height, width, **kwargs)
    if initial is None:
        return None
    loop, is_passed, is_black, is_horizontal, is_vertical = initial

    is_black_problem = [[is_black[y, x].sol for x in range(width)] for y in range(height)]
    gate_id = [[-1 for _ in range(width)] for _ in range(height)]
    id_last = 0
    extra_black = []
    gates = []

    for y in range(height):
        for x in range(width):
            if is_horizontal[y, x].sol and (x == 0 or not is_horizontal[y, x - 1].sol):
                gate_len = 0
                for x2 in range(x, width):
                    if is_horizontal[y, x2].sol:
                        gate_id[y][x2] = id_last
                        gate_len += 1
                    else:
                        break
                id_last += 1
                gates.append((y, x, 0, gate_len, -1))
            if is_vertical[y, x].sol and (y == 0 or not is_vertical[y - 1, x].sol):
                gate_len = 0
                for y2 in range(y, height):
                    if is_vertical[y2, x].sol:
                        gate_id[y2][x] = id_last
                        gate_len += 1
                    else:
                        break
                id_last += 1
                gates.append((y, x, 1, gate_len, -1))
            if is_black[y, x].sol:
                if not ((y > 0 and is_vertical[y - 1, x].sol) or (y < height - 1 and is_vertical[y + 1, x].sol)
                or (x > 0 and is_horizontal[y, x - 1].sol) or (x < width - 1 and is_horizontal[y, x + 1].sol)):
                    extra_black.append((y, x))

    traverse_base = None
    for y in range(height):
        for x in range(width):
            if is_passed[y, x].sol:
                traverse_base = (y, x)
                break
        if traverse_base is not None:
            break
    assert traverse_base is not None

    py, px = -1, -1
    cy, cx = traverse_base
    loop_ord = []
    while (py, px) == (-1, -1) or (cy, cx) != traverse_base:
        loop_ord.append((cy, cx))

        neighbors = []
        if cy > 0 and loop.vertical[cy - 1, cx].sol:
            neighbors.append((cy - 1, cx))
        if cy < height - 1 and loop.vertical[cy, cx].sol:
            neighbors.append((cy + 1, cx))
        if cx > 0 and loop.horizontal[cy, cx - 1].sol:
            neighbors.append((cy, cx - 1))
        if cx < width - 1 and loop.horizontal[cy, cx].sol:
            neighbors.append((cy, cx + 1))
        neighbors = list(filter(lambda p: (py, px) != p, neighbors))
        assert 1 <= len(neighbors) <= 2
        py, px = cy, cx
        cy, cx = random.choice(neighbors)

    for _ in range(10):
        while True:
            origin_idx = random.randint(0, len(loop_ord) - 1)
            oy, ox = loop_ord[origin_idx]
            if gate_id[oy][ox] == -1:
                break
        gate_ord_constraints = [-1 for _ in range(len(gates))]
        #enable_clue = [False for _ in range(len(gates))]
        #for i in range(len(gates)):
        #    if i != 0 and i != len(gates) - 1 and not enable_clue[i - 1] and random.random() < 0.2:
        #        enable_clue[i] = True

        gate_ord = 0
        for i in range(len(loop_ord)):
            y, x = loop_ord[(i + origin_idx) % len(loop_ord)]
            if gate_id[y][x] != -1:
                gate_ord += 1
                if random.random() < 0.2:
                    gate_ord_constraints[gate_id[y][x]] = gate_ord
        actual_gates = [(*(gates[i][0:4]), gate_ord_constraints[i]) for i in range(len(gates))]

        if problem_to_pzv_url(height, width, ((oy, ox), extra_black, actual_gates)) is None:
            continue

        has_multiple_ans, _ = solve_slalom(height, width, (oy, ox), is_black_problem, actual_gates, reference_sol_loop=loop)
        if not has_multiple_ans:
            if minify:
                minify_problem(height, width, (oy, ox), is_black_problem, actual_gates, reference_sol_loop=loop)
            return (oy, ox), extra_black, actual_gates
    return None


def minify_problem(height, width, origin, is_black, gates, reference_sol_loop):
    for i in range(len(gates)):
        y, x, d, l, n = gates[i]
        if n != -1:
            gates[i] = (y, x, d, l, -1)
            is_sat, _ = solve_slalom(height, width, origin, is_black, gates, reference_sol_loop)
            if is_sat:
                gates[i] = (y, x, d, l, n)


def instantiate_problem(height, width, problem_base):
    origin, extra_black, gates = problem_base
    board = [[0 for _ in range(width)] for _ in range(height)]
    for y, x in extra_black:
        board[y][x] = -1

    def update_gate_end(y, x, n):
        if not (0 <= y < height and 0 <= x < width):
            return False
        if n == -1:
            if board[y][x] >= 1:
                return True
            elif board[y][x] == 0:
                board[y][x] = -1
                return False
            else:
                return False
        else:
            if board[y][x] >= 1:
                return True
            elif board[y][x] == 0:
                board[y][x] = -(n + 1)
                return False
            else:
                return True

    def update_gate(y, x):
        if board[y][x] != 0:
            return True
        else:
            board[y][x] = 1
            return False

    for y, x, d, l, n in gates:
        if n != -1 and not (1 <= n <= len(gates)):
            return None
        if d == 0:  # horizontal
            if x + l > width:
                return None
            if update_gate_end(y, x - 1, n) | update_gate_end(y, x + l, n):
                return None
            for i in range(l):
                if update_gate(y, x + i):
                    return None
        else:
            if y + l > height:
                return None
            if update_gate_end(y - 1, x, n) | update_gate_end(y + l, x, n):
                return None
            for i in range(l):
                if update_gate(y + i, x):
                    return None
    oy, ox = origin
    if board[oy][ox] != 0:
        return None

    is_black = [[board[y][x] <= -1 for x in range(width)] for y in range(height)]
    return is_black


def problem_to_pzv_url(height, width, problem):
    def stringify_clue(y, x, dir, n):
        return str(dir + (5 if n >= 16 else 0)) + hex(n)[2:]

    origin, extra_black, gates = problem
    origin_y, origin_x = origin
    board = [[None for _ in range(width)] for _ in range(height)]
    required_clues_one = []
    required_clues_two = []
    for y, x in extra_black:
        board[y][x] = '1'
    for y, x, d, l, n in gates:
        ends = []
        if d == 0:
            for i in range(l):
                board[y][x + i] = '3'
            if x > 0:
                ends.append((y, x - 1, 4))
            if x + l < width:
                ends.append((y, x + l, 3))
        else:
            for i in range(l):
                board[y + i][x] = '2'
            if y > 0:
                ends.append((y - 1, x, 2))
            if y + l < width:
                ends.append((y + l, x, 1))
        for y2, x2, dir in ends:
            board[y2][x2] = '1'
        if n != -1:
            if len(ends) == 0:
                return None
            elif len(ends) == 1:
                required_clues_one.append((n, ends))
            else:
                required_clues_two.append((n, ends))
    for n, c in required_clues_one:
        y, x, dir = c[0]
        if board[y][x] != '1':
            return None
        board[y][x] = stringify_clue(y, x, dir, n)
    for n, cs in required_clues_two:
        y1, x1, dir1 = cs[0]
        y2, x2, dir2 = cs[1]
        board[y1][x1] = stringify_clue(y1, x1, dir1, n)
        board[y2][x2] = stringify_clue(y2, x2, dir2, n)
    for n, cs in required_clues_two:
        y1, x1, dir1 = cs[0]
        y2, x2, dir2 = cs[1]
        if board[y1][x1] != stringify_clue(y1, x1, dir1, n) and board[y2][x2] != stringify_clue(y2, x2, dir2, n):
            return None
    blocks = []
    for y in range(height):
        for x in range(width):
            if board[y][x] == '1':
                blocks.append(None)
            elif board[y][x] is not None and len(board[y][x]) >= 2:
                blocks.append(board[y][x])
                board[y][x] = '1'
    return 'http://pzv.jp/p.html?slalom/d/{}/{}/{}{}/{}'.format(
        width,
        height,
        util.encode_array(board, single_empty_marker='4'),
        util.encode_array(blocks, single_empty_marker='g'),
        origin_y * width + origin_x
    )


def visualize_problem(height, width, problem_base):
    origin, extra_black, gates = problem_base
    board = [['.' for _ in range(width)] for _ in range(height)]

    board[origin[0]][origin[1]] = 'O'
    for y, x in extra_black:
        board[y][x] = '#'
    for y, x, d, l, n in gates:
        v = '#' if n == -1 else str(n)
        if d == 0:
            if x > 0:
                board[y][x - 1] = v
            for i in range(l):
                board[y][x + i] = '-'
            if x + l < width:
                board[y][x + l] = v
        else:
            if y > 0:
                board[y - 1][x] = v
            for i in range(l):
                board[y + i][x] = '|'
            if y + l < height:
                board[y + l][x] = v
    for y in range(height):
        print(''.join(board[y]), file=sys.stderr)
    print(file=sys.stderr)


def _main():
    if len(sys.argv) == 1:
        # https://puzsq.jp/main/puzzle_play.php?pid=9522
        height = 10
        width = 10
        origin = (5, 1)
        extra_black = [(9, 2)]
        gates = [(1, 5, 0, 3, -1), (2, 3, 0, 1, -1), (3, 8, 0, 1, 1), (6, 3, 0, 4, 3), (7, 1, 0, 1, -1), (8, 6, 0, 4, 2)]
        visualize_problem(height, width, (origin, extra_black, gates))

        is_black = instantiate_problem(height, width, (origin, extra_black, gates))
        is_sat, sol = solve_slalom(height, width, origin, is_black, gates)
        print(is_sat)
        print(util.stringify_grid_frame(sol))
    else:
        sys.setrecursionlimit(2000)

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-h', '--height', type=int, required=True)
        parser.add_argument('-w', '--width', type=int, required=True)
        parser.add_argument('--min-gates', type=int)
        parser.add_argument('--max-gates', type=int)
        parser.add_argument('--max-isolated-black-cells', type=int)
        parser.add_argument('--no-adjacent-black-cell', action='store_true')
        parser.add_argument('--no-facing-length-two', action='store_true')
        parser.add_argument('--no-space-2x2', action='store_true')
        parser.add_argument('--black-cell-in-every-3x3', action='store_true')
        parser.add_argument('--min-go-through', type=int, default=0)
        parser.add_argument('--no-minify', action='store_true')

        args = parser.parse_args()
        height = args.height
        width = args.width

        cspuz.config.solver_timeout = 600.0
        while True:
            try:
                problem = generate_slalom(height, width,
                                          minify=not args.no_minify,
                                          n_min_gates=args.min_gates,
                                          n_max_gates=args.max_gates,
                                          n_max_isolated_black_cells=args.max_isolated_black_cells,
                                          no_adjacent_black_cell=args.no_adjacent_black_cell,
                                          no_facing_length_two=args.no_facing_length_two,
                                          no_space_2x2=args.no_space_2x2,
                                          black_cell_in_every_3x3=args.black_cell_in_every_3x3,
                                          min_go_through=args.min_go_through)
                if problem is not None:
                    print(problem_to_pzv_url(height, width, problem), flush=True)

            except subprocess.TimeoutExpired:
                print('timeout', file=sys.stderr)


if __name__ == '__main__':
    _main()
