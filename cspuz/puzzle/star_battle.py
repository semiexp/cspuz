import random
import math
import sys
import numpy as np

from cspuz import Array, Solver
from cspuz.puzzle import util


def solve_star_battle(n, blocks, k):
    if not isinstance(blocks, Array):
        blocks = Array(blocks)
    solver = Solver()
    has_star = solver.bool_array((n, n))
    solver.add_answer_key(has_star)
    for i in range(n):
        solver.ensure(sum(has_star[i, :].cond(1, 0)) == k)
        solver.ensure(sum(has_star[:, i].cond(1, 0)) == k)
    solver.ensure(~(has_star[:-1, :] & has_star[1:, :]))
    solver.ensure(~(has_star[:, :-1] & has_star[:, 1:]))
    solver.ensure(~(has_star[:-1, :-1] & has_star[1:, 1:]))
    solver.ensure(~(has_star[:-1, 1:] & has_star[1:, :-1]))
    for i in range(n):
        solver.ensure(sum((has_star & (blocks == i)).cond(1, 0)) == k)

    is_sat = solver.solve()
    return is_sat, has_star


def _initial_blocks(n):
    seeds = set()
    while len(seeds) < n:
        seeds.add((random.randint(0, n - 1), random.randint(0, n - 1)))
    blocks = [[-1 for _ in range(n)] for _ in range(n)]
    seeds = list(seeds)
    for i, (y, x) in enumerate(seeds):
        blocks[y][x] = i

    dirs = [(-1, 0), (0, -1), (1, 0), (0, 1)]

    for i in range(n * (n - 1)):
        cand = []
        sz = [0] * n
        for y in range(n):
            for x in range(n):
                if blocks[y][x] != -1:
                    sz[blocks[y][x]] += 1
                    continue
                for dy, dx in dirs:
                    y2 = y + dy
                    x2 = x + dx
                    if 0 <= y2 < n and 0 <= x2 < n and blocks[y2][x2] != -1:
                        cand.append((y, x, blocks[y2][x2]))
        w = [sz[g] ** -4 for _, _, g in cand]
        p = np.array(w) / sum(w)
        i = np.random.choice(np.arange(len(cand)), p=p)
        y, x, g = cand[i]
        blocks[y][x] = g

    return blocks


def _is_connected(n, blocks, g, excluded):
    visited = [[False for _ in range(n)] for _ in range(n)]

    def visit(y, x):
        if not (0 <= y < n and 0 <= x < n) or (y, x) == excluded or visited[y][x] or blocks[y][x] != g:
            return
        visited[y][x] = True
        visit(y - 1, x)
        visit(y + 1, x)
        visit(y, x - 1)
        visit(y, x + 1)

    grp = 0
    for y in range(n):
        for x in range(n):
            if blocks[y][x] == g and not visited[y][x] and (y, x) != excluded:
                grp += 1
                visit(y, x)

    return grp == 1


def _compute_score(has_star):
    ret = 0
    for v in has_star:
        if v.sol is not None:
            ret += 1
    return ret


def generate_star_battle(n, k, verbose=False):
    while True:
        blocks = _initial_blocks(n)
        is_sat, has_star = solve_star_battle(n, blocks, k)
        if is_sat:
            score = _compute_score(has_star)
            break

    temperature = 5.0
    fully_solved_score = n * n
    for step in range(n * n * 10):
        cand = []
        for y in range(n):
            for x in range(n):
                if not _is_connected(n, blocks, blocks[y][x], (y, x)):
                    continue
                g2 = set()
                if y > 0:
                    g2.add(blocks[y - 1][x])
                if y < n - 1:
                    g2.add(blocks[y + 1][x])
                if x > 0:
                    g2.add(blocks[y][x - 1])
                if x < n - 1:
                    g2.add(blocks[y][x + 1])
                for g in g2:
                    if g != blocks[y][x]:
                        cand.append((y, x, g))
        random.shuffle(cand)

        for y, x, g in cand:
            g_prev = blocks[y][x]
            blocks[y][x] = g

            sat, has_star = solve_star_battle(n, blocks, k)
            if not sat:
                score_next = -1
                update = False
            else:
                score_next = _compute_score(has_star)
                if score_next == fully_solved_score:
                    return blocks
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                if verbose:
                    print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                break
            else:
                blocks[y][x] = g_prev

        temperature *= 0.995
    if verbose:
        print('failed', file=sys.stderr)
    return None


def problem_to_pzv_url(n, k, blocks):
    def convert_binary_seq(s):
        ret = ''
        for i in range((len(s) + 4) // 5):
            v = 0
            for j in range(5):
                if i * 5 + j < len(s) and s[i * 5 + j] == 1:
                    v += (2 ** (4 - j))
            ret += np.base_repr(v, 32).lower()
        return ret

    s = []
    for y in range(n):
        for x in range(n - 1):
            s.append(1 if blocks[y][x] != blocks[y][x + 1] else 0)
    ret = convert_binary_seq(s)
    s = []
    for y in range(n - 1):
        for x in range(n):
            s.append(1 if blocks[y][x] != blocks[y + 1][x] else 0)
    ret += convert_binary_seq(s)
    return 'http://pzv.jp/p.html?starbattle/{}/{}/{}/{}'.format(n, n, k, ret)


def _main():
    if len(sys.argv) == 1:
        # generated example: http://pzv.jp/p.html?starbattle/6/6/1/2u9gn9c9jpmk
        is_sat, has_star = solve_star_battle(6, [
            [0, 0, 0, 0, 1, 1],
            [0, 2, 3, 0, 1, 1],
            [2, 2, 3, 3, 3, 1],
            [2, 1, 1, 1, 1, 1],
            [2, 4, 4, 1, 4, 5],
            [2, 2, 4, 4, 4, 5],
        ], 1)
        print('has answer:', is_sat)
        if is_sat:
            print(util.stringify_array(has_star, {None: '?', True: '*', False: '.'}))
    else:
        n, k = map(int, sys.argv[1:])
        while True:
            problem = generate_star_battle(n, k, verbose=True)
            if problem is not None:
                print(problem_to_pzv_url(n, k, problem), flush=True)


if __name__ == '__main__':
    _main()
