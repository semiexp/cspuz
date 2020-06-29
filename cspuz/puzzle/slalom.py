import random
import math
import sys
import subprocess

import cspuz
from cspuz import Solver, graph
from cspuz.constraints import count_true, fold_or

from cspuz.grid_frame import BoolGridFrame
from cspuz.puzzle import util


def solve_slalom(height, width, origin, is_black, gates):
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
    is_sat = solver.solve()
    return is_sat, loop


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


def compute_score(height, width, loop):
    ret = 0
    for y in range(height * 2 - 1):
        for x in range(width * 2 - 1):
            if y % 2 != x % 2 and loop[y, x].sol is not None:
                ret += 1
    return ret


def enumerate_next_problem(height, width, problem_base, n_min_gates=4, n_max_gates=6, min_gate_len=1, max_gate_len=4):
    origin, extra_black, gates = problem_base
    ret = []

    is_black = instantiate_problem(height, width, problem_base)
    if is_black is None:
        return []

    # alter `origin`
    for y in range(height):
        for x in range(width):
            if (y, x) != origin and not is_black[y][x] and random.random() < 0.2:
                ret.append(((y, x), extra_black, gates))

    # alter `extra_black`
    # add
    if len(extra_black) < 2:
        for y in range(height):
            for x in range(width):
                if not is_black[y][x] and random.random() < 0.5:
                    ret.append((origin, extra_black + [(y, x)], gates))
    # remove
    for i in range(len(extra_black)):
        ret.append((origin, [p for j, p in enumerate(extra_black) if j != i], gates))

    # alter `gates`
    # add
    if len(gates) < n_max_gates:
        for y in range(height):
            for x in range(width):
                if x < width - 1 and random.random() < 0.5:
                    ret.append((origin, extra_black, gates + [(y, x, 0, random.randint(min_gate_len, min(max_gate_len, width - x)), -1)]))
                if y < height - 1 and random.random() < 0.5:
                    ret.append((origin, extra_black, gates + [(y, x, 1, random.randint(min_gate_len, min(max_gate_len, height - y)), -1)]))
    # remove
    if len(gates) > n_min_gates:
        for i in range(len(gates)):
            ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i]))
    used_indices = [x[4] for x in gates if x[4] != -1]
    for i in range(len(gates)):
        # change indices
        y, x, d, l, n = gates[i]
        for n2 in [-1] + list(range(1, len(gates) + 1)):
            if n == -1 and len(used_indices) >= 3:
                continue
            if n != n2 and n2 not in used_indices:
                ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i] + [(y, x, d, l, n2)]))
        # extend
        if l < max_gate_len:
            if d == 0:
                if x < width - 1:
                    ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i] + [(y, x, d, l + 1, n)]))
                if x > 0:
                    ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i] + [(y, x - 1, d, l + 1, n)]))
            else:
                if y < height - 1:
                    ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i] + [(y, x, d, l + 1, n)]))
                if y > 0:
                    ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i] + [(y - 1, x, d, l + 1, n)]))
        # shrink
        if l > min_gate_len:  # 1 -> 2
            if d == 0:
                ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i] + [(y, x, d, l - 1, n)]))
                ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i] + [(y, x + 1, d, l - 1, n)]))
            else:
                ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i] + [(y, x, d, l - 1, n)]))
                ret.append((origin, extra_black, [p for j, p in enumerate(gates) if j != i] + [(y + 1, x, d, l - 1, n)]))

    return ret


def check_problem(height, width, problem_base):
    origin, extra_black, gates = problem_base
    board = [['.' for _ in range(width)] for _ in range(height)]

    board[origin[0]][origin[1]] = 'O'
    for y, x in extra_black:
        board[y][x] = '#'
    for y, x, d, l, n in gates:
        v = '#' # if n == -1 else str(n)
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
        for x in range(width):
            if board[y][x] == '-':
                if (y > 0 and board[y - 1][x] != '.') or (y < height - 1 and board[y + 1][x] != '.'):
                    return False
            if board[y][x] == '|':
                if (x > 0 and board[y][x - 1] != '.') or (x < width - 1 and board[y][x + 1] != '.'):
                    return False
            if board[y][x] == '.':
                adj_non_black = 0
                if y > 0 and board[y - 1][x] != '#':
                    adj_non_black += 1
                if x > 0 and board[y][x - 1] != '#':
                    adj_non_black += 1
                if y < height - 1 and board[y + 1][x] != '#':
                    adj_non_black += 1
                if x < width - 1 and board[y][x + 1] != '#':
                    adj_non_black += 1
                if adj_non_black < 2:
                    return False
    trivial_ends = set()
    for y, x, d, l, n in gates:
        if l != 1:
            continue
        if d == 0:
            if not 0 < y < height - 1:
                return False
            e1 = (y - 1, x)
            e2 = (y + 1, x)
        else:
            if not 0 < x < width - 1:
                return False
            e1 = (y, x - 1)
            e2 = (y, x + 1)
        if e1 in trivial_ends or e2 in trivial_ends:
            return False
        trivial_ends.add(e1)
        trivial_ends.add(e2)
    return True


def generate_slalom(height, width, verbose=False):
    problem = ((random.randint(0, height - 1), random.randint(0, width - 1)), [], [])
    score = 0
    temperature = 5.0
    fully_solved_score = height * (width - 1) + (height - 1) * width

    for step in range(height * width * 5):
        cand = enumerate_next_problem(height, width, problem)
        random.shuffle(cand)

        for problem2 in cand:
            origin, extra_black, gates = problem2
            is_black = instantiate_problem(height, width, (origin, extra_black, gates))
            if is_black is None:
                continue

            if not check_problem(height, width, (origin, extra_black, gates)):
                continue
            if problem_to_pzv_url(height, width, (origin, extra_black, gates)) is None:
                continue

            is_sat, loop = solve_slalom(height, width, origin, is_black, gates)
            if not is_sat:
                continue
            else:
                raw_score = compute_score(height, width, loop)
                if raw_score == fully_solved_score:
                    print('steps: {}'.format(step), flush=True)
                    return origin, extra_black, gates
                clue_penalty = len(extra_black) * 8 + len(gates) * 5
                score_next = raw_score - clue_penalty
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))
            if update:
                if verbose:
                    print('update: {} -> {} ({} {})'.format(score, score_next, raw_score, clue_penalty), file=sys.stderr)
                score = score_next
                problem = problem2
                break
            else:
                continue
        temperature *= 0.995
    if verbose:
        print('failed', file=sys.stderr)
    return None


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
        height, width = map(int, sys.argv[1:])
        cspuz.config.solver_timeout = 600.0
        while True:
            try:
                problem = generate_slalom(height, width, verbose=True)
                if problem is not None:
                    print(problem_to_pzv_url(height, width, problem), flush=True)
                    print(problem, flush=True)
                    print(problem, file=sys.stderr)
            except subprocess.TimeoutExpired:
                print('timeout', file=sys.stderr)


if __name__ == '__main__':
    _main()
