import random
import sys
import math
from collections import defaultdict, deque

from cspuz import Solver
from cspuz.constraints import count_true
from cspuz.puzzle import util
from cspuz.problem_serializer import Rooms, serialize_problem_as_url, deserialize_problem_as_url


def solve_norinori(height, width, blocks):
    solver = Solver()
    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)

    for y in range(height):
        for x in range(width):
            solver.ensure(is_black[y, x].then(count_true(is_black.four_neighbors(y, x)) == 1))

    for block in blocks:
        solver.ensure(count_true(is_black[block]) == 2)

    is_sat = solver.solve()
    return is_sat, is_black


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


def generate_cand(height, width, blocks, no_merge=False, no_split=False, min_block_size=2):
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
    if not no_split:
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
                    ret.append(
                        ([i, j], [[p for p in blocks[i] if p != (y, x)], blocks[j] + [(y, x)]])
                    )
                if len(blocks[j]) > min_block_size and is_connected(blocks[j], (y + 1, x)):
                    ret.append(
                        (
                            [i, j],
                            [[p for p in blocks[j] if p != (y + 1, x)], blocks[i] + [(y + 1, x)]],
                        )
                    )
            if x < width - 1 and block_id[y][x] != block_id[y][x + 1]:
                i = block_id[y][x]
                j = block_id[y][x + 1]
                if len(blocks[i]) > min_block_size and is_connected(blocks[i], (y, x)):
                    ret.append(
                        ([i, j], [[p for p in blocks[i] if p != (y, x)], blocks[j] + [(y, x)]])
                    )
                if len(blocks[j]) > min_block_size and is_connected(blocks[j], (y, x + 1)):
                    ret.append(
                        (
                            [i, j],
                            [[p for p in blocks[j] if p != (y, x + 1)], blocks[i] + [(y, x + 1)]],
                        )
                    )

    return ret


def _compute_score(height, width, answer):
    ret = 0
    for y in range(height):
        for x in range(width):
            if answer[y][x].sol is not None:
                ret += 1
    return ret


def generate_norinori(
    height, width, min_blocks=0, max_blocks=1000, min_block_size=2, max_block_size=8, verbose=False
):
    block = []
    for y in range(height):
        for x in range(width):
            block.append((y, x))
    blocks = [block]

    score = -1e5
    temperature = 5.0
    fully_solved_score = height * width
    for step in range(height * width * 10):
        cand = generate_cand(
            height,
            width,
            blocks,
            no_split=(len(blocks) >= max_blocks),
            no_merge=(len(blocks) <= min_blocks),
            min_block_size=min_block_size,
        )
        random.shuffle(cand)

        for step in cand:
            rm, app = step
            blocks_next = [block for i, block in enumerate(blocks) if i not in rm] + app

            is_sat, answer = solve_norinori(height, width, blocks_next)
            if not is_sat:
                score_next = -1
                update = False
            else:
                raw_score_next = _compute_score(height, width, answer)
                flg = True
                for block in blocks:
                    if len(block) > max_block_size:
                        flg = False
                if raw_score_next == fully_solved_score and flg:
                    print("generated", file=sys.stderr)
                    return blocks_next
                clue_score = 0
                score_next = raw_score_next - clue_score
                update = score < score_next or random.random() < math.exp(
                    (score_next - score) / temperature
                )

            if update:
                if verbose:
                    print(
                        "update: {} -> {} ({})".format(score, score_next, raw_score_next),
                        file=sys.stderr,
                    )
                score = score_next
                blocks = blocks_next
                break

        temperature *= 0.995
    if verbose:
        print("failed", file=sys.stderr)
    return None


NORINORI_COMBINATOR = Rooms()


def serialize_norinori(height, width, blocks):
    return serialize_problem_as_url(NORINORI_COMBINATOR, "norinori", height, width, blocks)


def deserialize_norinori(url):
    return deserialize_problem_as_url(NORINORI_COMBINATOR, url, return_size=True)


def _main():
    if len(sys.argv) == 1:
        # https://puzsq.sakura.ne.jp/main/puzzle_play.php?pid=7919
        height = 6
        width = 6
        b = ["001112", "111132", "413333", "415556", "777756", "888776"]
        blocks = defaultdict(list)
        for y in range(height):
            for x in range(width):
                blocks[b[y][x]].append((y, x))
        blocks = list(blocks.values())

        is_sat, is_black = solve_norinori(height, width, blocks)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", False: ".", True: "#"}))
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            gen = generate_norinori(height, width, min_block_size=2, verbose=True)
            if gen is not None:
                url = serialize_norinori(height, width, gen)
                print(url, flush=True)


if __name__ == "__main__":
    _main()
