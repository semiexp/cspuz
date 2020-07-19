import random
import sys
import math
from copy import deepcopy
from collections import defaultdict, deque
import subprocess

import numpy as np

import cspuz
from cspuz import Solver, graph
from cspuz.constraints import Array, count_true, fold_or, fold_and


def solve_nanro(height, width, blocks, num):
    block_id = [[-1 for _ in range(width)] for _ in range(height)]
    for i, block in enumerate(blocks):
        for y, x in block:
            block_id[y][x] = i
    solver = Solver()
    answer = []
    has_num = solver.bool_array((height, width))
    for y in range(height):
        row = []
        for x in range(width):
            v = solver.int_var(0, len(blocks[block_id[y][x]]))
            solver.add_answer_key(v)
            solver.ensure(has_num[y, x] == (v != 0))
            row.append(v)
        answer.append(row)
    graph.active_vertices_connected(solver, has_num)

    for i, block in enumerate(blocks):
        nonempty = solver.int_var(1, len(block))
        solver.ensure(nonempty == count_true(answer[y][x] != 0 for y, x in block))
        for y, x in block:
            solver.ensure((answer[y][x] == 0) | (answer[y][x] == nonempty))
    for y in range(height):
        for x in range(width):
            if num[y][x] > 0:
                solver.ensure(answer[y][x] == num[y][x])
            if y < height - 1 and x < width - 1:
                solver.ensure((answer[y][x] == 0) | (answer[y][x + 1] == 0) | (answer[y + 1][x] == 0) | (answer[y + 1][x + 1] == 0))
            if y < height - 1 and block_id[y][x] != block_id[y + 1][x]:
                solver.ensure((answer[y][x] == 0) | (answer[y + 1][x] == 0) | (answer[y][x] != answer[y + 1][x]))
            if x < width - 1 and block_id[y][x] != block_id[y][x + 1]:
                solver.ensure((answer[y][x] == 0) | (answer[y][x + 1] == 0) | (answer[y][x] != answer[y][x + 1]))

    is_sat = solver.solve()
    return is_sat, answer


def split_block(block):
    assert len(block) >= 2
    while True:
        seed_a = random.randint(0, len(block) - 1)
        seed_b = random.randint(0, len(block) - 1)
        if seed_a != seed_b:
            break
    block_set = set(block)

    def bfs(seed):
        q = deque()
        q.append(seed)
        ans = dict()
        ans[seed] = 0

        while len(q) > 0:
            y, x = q.popleft()
            d = ans[(y, x)]
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if (y + dy, x + dx) in block_set and (y + dy, x + dx) not in ans:
                    ans[(y + dy, x + dx)] = d + 1
                    q.append((y + dy, x + dx))
        return ans

    dist_a = bfs(block[seed_a])
    dist_b = bfs(block[seed_b])
    block_a = []
    block_b = []
    for b in block:
        da = dist_a[b]
        db = dist_b[b]
        if da <= db:
            block_a.append(b)
        else:
            block_b.append(b)
    return block_a, block_b


def is_connected(block, excluded):
    block_set = set(block)
    visited = set()

    def visit(y, x):
        if (y, x) not in block or (y, x) in visited or (y, x) == excluded:
            return
        visited.add((y, x))
        visit(y - 1, x)
        visit(y + 1, x)
        visit(y, x - 1)
        visit(y, x + 1)

    if len(block) == 1:
        return excluded is None

    if block[0] == excluded:
        visit(*block[1])
    else:
        visit(*block[0])

    return len(visited) == len(block_set) - (1 if excluded in block_set else 0)


def generate_cand(height, width, blocks, no_merge=False, min_block_size=2):
    block_id = [[-1 for _ in range(width)] for _ in range(height)]
    for i, block in enumerate(blocks):
        for y, x in block:
            block_id[y][x] = i

    ret = []

    # merge
    if not no_merge:
        adjacent_pairs = set()
        for y in range(height):
            for x in range(width):
                if y < height - 1 and block_id[y][x] != block_id[y + 1][x]:
                    i = block_id[y][x]
                    j = block_id[y + 1][x]
                    if i < j:
                        adjacent_pairs.add((i, j))
                    else:
                        adjacent_pairs.add((j, i))
                if x < width - 1 and block_id[y][x] != block_id[y][x + 1]:
                    i = block_id[y][x]
                    j = block_id[y][x + 1]
                    if i < j:
                        adjacent_pairs.add((i, j))
                    else:
                        adjacent_pairs.add((j, i))
        for i, j in adjacent_pairs:
            ret.append(([i, j], [blocks[i] + blocks[j]]))

    # split
    for i, block in enumerate(blocks):
        if len(block) >= min_block_size * 2:
            for _ in range(2 * (len(block) - 1)):
                block_a, block_b = split_block(block)
                if len(block_a) >= min_block_size and len(block_b) >= min_block_size:
                    ret.append(([i], [block_a, block_b]))

    # mutate
    for y in range(height):
        for x in range(width):
            if y < height - 1 and block_id[y][x] != block_id[y + 1][x]:
                i = block_id[y][x]
                j = block_id[y + 1][x]
                if len(blocks[i]) > min_block_size and is_connected(blocks[i], (y, x)):
                    ret.append(([i, j], [[p for p in blocks[i] if p != (y, x)], blocks[j] + [(y, x)]]))
                if len(blocks[j]) > min_block_size and is_connected(blocks[j], (y + 1, x)):
                    ret.append(([i, j], [[p for p in blocks[j] if p != (y + 1, x)], blocks[i] + [(y + 1, x)]]))
            if x < width - 1 and block_id[y][x] != block_id[y][x + 1]:
                i = block_id[y][x]
                j = block_id[y][x + 1]
                if len(blocks[i]) > min_block_size and is_connected(blocks[i], (y, x)):
                    ret.append(([i, j], [[p for p in blocks[i] if p != (y, x)], blocks[j] + [(y, x)]]))
                if len(blocks[j]) > min_block_size and is_connected(blocks[j], (y, x + 1)):
                    ret.append(([i, j], [[p for p in blocks[j] if p != (y, x + 1)], blocks[i] + [(y, x + 1)]]))

    return ret


def _compute_score(height, width, answer):
    ret = 0
    for y in range(height):
        for x in range(width):
            if answer[y][x].sol is not None:
                ret += 1
    return ret


def generate_nanro(height, width, verbose=False):
    def is_stoppable(blocks):
        return len(blocks) >= height * width // 6 and max(map(len, blocks)) <= 7

    block = []
    for y in range(height):
        for x in range(width):
            block.append((y, x))
    blocks = [block]

    num = [[0 for _ in range(width)] for _ in range(height)]

    score = -1e5
    temperature = 5.0
    fully_solved_score = height * width
    block_threshold = 10

    for step in range(height * width * 10):
        cand = generate_cand(height, width, blocks, no_merge=(len(blocks) <= block_threshold))

        if len(blocks) >= 11:
            for block in blocks:
                for y, x in block:
                    for n in range(0, min(6, len(block) + 1)):
                        if n == 1:
                            continue
                        if num[y][x] != n:
                            cand.append((y, x, n))
        random.shuffle(cand)

        for step in cand:
            if len(step) == 2:
                rm, app = step
                blocks_next = [block for i, block in enumerate(blocks) if i not in rm] + app
                num_next = deepcopy(num)
                if len(blocks) >= block_threshold and len(blocks_next) < block_threshold:
                    continue
                for block in blocks_next:
                    for y, x in block:
                        if num_next[y][x] > len(blocks_next):
                            num_next[y][x] = 0
            else:
                y, x, n = step
                blocks_next = blocks
                num_next = deepcopy(num)
                num_next[y][x] = n

            pretest = True
            max_block_size = 0
            num_size_two = 2
            for block in blocks_next:
                max_block_size = max(max_block_size, len(block))
                has_clue = 0
                for y, x in block:
                    if num_next[y][x] > 0:
                        has_clue += 1
                    #if 0 < num_next[y][x] <= len(block) - 4:
                    #    pretest = False
                if has_clue >= 2:
                    pretest = False
                if len(block) == 2:
                    num_size_two += 1
            if is_stoppable(blocks) and not is_stoppable(blocks_next):
                pretest = False

            if num_size_two >= 5:
                pretest = False
            if pretest:
                is_sat, answer = solve_nanro(height, width, blocks_next, num_next)
            else:
                continue
            if not is_sat:
                score_next = -1
                update = False
            else:
                raw_score_next = _compute_score(height, width, answer)
                if raw_score_next == fully_solved_score and len(blocks_next) >= height * width // 6 and max_block_size <= 7:
                    return blocks_next, num_next
                clue_score = 0
                for y in range(height):
                    for x in range(width):
                        if num_next[y][x] in (1, 2):
                            clue_score += 12
                        elif num_next[y][x] == 3:
                            clue_score += 9
                        elif num_next[y][x] > 0:
                            clue_score += 6
                #clue_score = -min(len(blocks_next), 20) * 5 # abs(len(blocks_next) - 12) * 4
                for block in blocks:
                    if len(block) <= 4:
                        clue_score += (4.0 - len(block)) ** 2
                score_next = raw_score_next - clue_score
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

                if not is_stoppable(blocks):
                    update = True

            if update:
                if verbose:
                    print('update: {} -> {} ({})'.format(score, score_next, raw_score_next), file=sys.stderr)
                score = score_next
                blocks = blocks_next
                num = num_next
                break

        temperature *= 0.995
    if verbose:
        print('failed', file=sys.stderr)
        print(blocks, file=sys.stderr)
        print(num, file=sys.stderr)
    return None


def problem_to_pzv_url(height, width, blocks, num):
    def convert_binary_seq(s):
        ret = ''
        for i in range((len(s) + 4) // 5):
            v = 0
            for j in range(5):
                if i * 5 + j < len(s) and s[i * 5 + j] == 1:
                    v += (2 ** (4 - j))
            ret += np.base_repr(v, 32).lower()
        return ret

    block_id = [[-1 for _ in range(width)] for _ in range(height)]
    for i, block in enumerate(blocks):
        for y, x in block:
            block_id[y][x] = i
    s = []
    for y in range(height):
        for x in range(width - 1):
            s.append(1 if block_id[y][x] != block_id[y][x + 1] else 0)
    ret = convert_binary_seq(s)
    s = []
    for y in range(height - 1):
        for x in range(width):
            s.append(1 if block_id[y][x] != block_id[y + 1][x] else 0)
    ret += convert_binary_seq(s)

    contiguous_empty_cells = 0
    for y in range(height):
        for x in range(width):
            if num[y][x] == 0:
                if contiguous_empty_cells == 20:
                    ret += 'z'
                    contiguous_empty_cells = 1
                else:
                    contiguous_empty_cells += 1
            else:
                if contiguous_empty_cells > 0:
                    ret += np.base_repr(contiguous_empty_cells + 15, 36).lower()
                    contiguous_empty_cells = 0
                if num[y][x] < 16:
                    ret += np.base_repr(num[y][x], 16).lower()
                else:
                    ret += '-' + np.base_repr(num[y][x], 16).lower()
    if contiguous_empty_cells > 0:
        ret += np.base_repr(contiguous_empty_cells + 15, 36).lower()

    return 'http://pzv.jp/p.html?nanro/{}/{}/{}'.format(width, height, ret)


def _main():
    if len(sys.argv) == 1:
        # http://pzv.jp/p.html?nanro/8/8/j9db9n5v9i6ge9g1de1h9rr05j4l2k5q5k2h4n3j3p
        height = 8
        width = 8
        b = [
            '01112334',
            '00022344',
            '05522344',
            '05552664',
            '75888664',
            '7579866a',
            '7779bbba',
            'ccccbdda'
        ]
        blocks = defaultdict(list)
        for y in range(height):
            for x in range(width):
                blocks[b[y][x]].append((y, x))
        blocks = list(blocks.values())

        num = [
            [5, 0, 0, 0, 0, 4, 0, 0],
            [0, 0, 0, 0, 2, 0, 0, 0],
            [0, 0, 5, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 5, 0],
            [0, 0, 0, 0, 2, 0, 0, 4],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [3, 0, 0, 0, 0, 3, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        is_sat, answer = solve_nanro(height, width, blocks, num)
        print('has answer:', is_sat)
        if is_sat:
            for y in range(height):
                for x in range(width):
                    if answer[y][x].sol is None:
                        print('?', end=' ')
                    elif answer[y][x].sol == 0:
                        print('.', end=' ')
                    else:
                        print(answer[y][x].sol, end=' ')
                print()
            print()
    else:
        cspuz.config.solver_timeout = 1200.0
        height, width = map(int, sys.argv[1:])
        while True:
            try:
                gen = generate_nanro(height, width, verbose=True)
                if gen is not None:
                    print(gen)
                    blocks, num = gen
                    print(problem_to_pzv_url(height, width, blocks, num), flush=True)
            except subprocess.TimeoutExpired:
                print('timeout', file=sys.stderr)


if __name__ == '__main__':
    _main()
