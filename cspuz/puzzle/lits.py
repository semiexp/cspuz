from collections import defaultdict, deque
import random
import sys
import math

from cspuz import Solver, graph
from cspuz.constraints import count_true, fold_or, fold_and
from cspuz.puzzle import util
from cspuz.problem_serializer import Rooms, serialize_problem_as_url, deserialize_problem_as_url


def solve_lits(height, width, blocks):
    solver = Solver()
    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)

    # black cells are connected
    graph.active_vertices_connected(solver, is_black)

    # no 2x2 black cells
    solver.ensure(~(is_black[1:, 1:] & is_black[1:, :-1] & is_black[:-1, 1:] & is_black[:-1, :-1]))

    block_id = [[-1 for _ in range(width)] for _ in range(height)]
    for i, block in enumerate(blocks):
        for y, x in block:
            block_id[y][x] = i

    num_straight = solver.int_array(len(blocks), 0, 2)
    has_t = solver.bool_array(len(blocks))

    for i in range(len(blocks)):
        solver.ensure(count_true([is_black[p] for p in blocks[i]]) == 4)
        adjacent_pairs = []
        is_straight = []
        is_t = []
        for y, x in blocks[i]:
            neighbor_same_block = []
            for y2, x2 in is_black.four_neighbor_indices(y, x):
                if block_id[y2][x2] == i:
                    neighbor_same_block.append((y2, x2))
                    if (y, x) < (y2, x2):
                        adjacent_pairs.append(is_black[y, x] & is_black[y2, x2])
            solver.ensure(is_black[y, x].then(fold_or([is_black[p] for p in neighbor_same_block])))

            tmp = []
            if 0 < y < height - 1 and block_id[y - 1][x] == i and block_id[y + 1][x] == i:
                tmp.append(fold_and(is_black[y - 1 : y + 2, x]))
            if 0 < x < width - 1 and block_id[y][x - 1] == i and block_id[y][x + 1] == i:
                tmp.append(fold_and(is_black[y, x - 1 : x + 2]))
            if len(tmp) >= 1:
                is_straight.append(fold_or(tmp))

            if len(neighbor_same_block) >= 3:
                is_t.append(count_true([is_black[p] for p in neighbor_same_block]) >= 3)
        solver.ensure(count_true(adjacent_pairs) == 3)

        solver.ensure(num_straight[i] == count_true(is_straight))
        solver.ensure(has_t[i] == fold_or(is_t))

    for y in range(height):
        for x in range(width):
            if y < height - 1 and block_id[y][x] != block_id[y + 1][x]:
                i = block_id[y][x]
                j = block_id[y + 1][x]
                solver.ensure(
                    (is_black[y, x] & is_black[y + 1, x]).then(
                        (num_straight[i] != num_straight[j]) | (has_t[i] != has_t[j])
                    )
                )
            if x < width - 1 and block_id[y][x] != block_id[y][x + 1]:
                i = block_id[y][x]
                j = block_id[y][x + 1]
                solver.ensure(
                    (is_black[y, x] & is_black[y, x + 1]).then(
                        (num_straight[i] != num_straight[j]) | (has_t[i] != has_t[j])
                    )
                )
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
        return True

    if block[0] == excluded:
        visit(*block[1])
    else:
        visit(*block[0])

    return len(visited) == len(block_set) - (1 if excluded in block_set else 0)


def generate_cand(height, width, blocks, no_merge=False):
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
        if len(block) >= 8:
            for _ in range(2 * (len(block) - 5)):
                block_a, block_b = split_block(block)
                if len(block_a) >= 4 and len(block_b) >= 4:
                    ret.append(([i], [block_a, block_b]))

    # mutate
    for y in range(height):
        for x in range(width):
            if y < height - 1 and block_id[y][x] != block_id[y + 1][x]:
                i = block_id[y][x]
                j = block_id[y + 1][x]
                if is_connected(blocks[i], (y, x)):
                    ret.append(
                        ([i, j], [[p for p in blocks[i] if p != (y, x)], blocks[j] + [(y, x)]])
                    )
                if is_connected(blocks[j], (y + 1, x)):
                    ret.append(
                        (
                            [i, j],
                            [[p for p in blocks[j] if p != (y + 1, x)], blocks[i] + [(y + 1, x)]],
                        )
                    )
            if x < width - 1 and block_id[y][x] != block_id[y][x + 1]:
                i = block_id[y][x]
                j = block_id[y][x + 1]
                if is_connected(blocks[i], (y, x)):
                    ret.append(
                        ([i, j], [[p for p in blocks[i] if p != (y, x)], blocks[j] + [(y, x)]])
                    )
                if is_connected(blocks[j], (y, x + 1)):
                    ret.append(
                        (
                            [i, j],
                            [[p for p in blocks[j] if p != (y, x + 1)], blocks[i] + [(y, x + 1)]],
                        )
                    )

    return ret


def _compute_score(has_star):
    ret = 0
    for v in has_star:
        if v.sol is not None:
            ret += 1
    return ret


def generate_lits(height, width, num_min_blocks=None, verbose=False):
    block = []
    for y in range(height):
        for x in range(width):
            block.append((y, x))
    blocks = [block]

    score = -1e5
    temperature = 5.0
    fully_solved_score = height * width
    for step in range(height * width * 10):
        cand = generate_cand(height, width, blocks, no_merge=(len(blocks) < 11))
        random.shuffle(cand)

        for rm, app in cand:
            blocks_next = [block for i, block in enumerate(blocks) if i not in rm] + app
            if len(blocks) >= 10 and len(blocks_next) < 10:
                continue

            is_sat, is_black = solve_lits(height, width, blocks_next)
            if not is_sat:
                score_next = -1
                update = False
            else:
                raw_score_next = _compute_score(is_black)
                if raw_score_next == fully_solved_score and (
                    num_min_blocks is None or len(blocks_next) >= num_min_blocks
                ):
                    return blocks_next
                clue_score = -min(len(blocks_next), 20) * 5  # abs(len(blocks_next) - 12) * 4
                for block in blocks:
                    clue_score += max(0.0, len(block) - float(height * width) / len(blocks)) * 2.0
                score_next = raw_score_next - clue_score
                update = score < score_next or random.random() < math.exp(
                    (score_next - score) / temperature
                )

            if update:
                if verbose:
                    print("update: {} -> {}".format(score, score_next), file=sys.stderr)
                score = score_next
                blocks = blocks_next
                break

        temperature *= 0.995
    if verbose:
        print("failed", file=sys.stderr)
    return None


LITS_COMBINATOR = Rooms()


def serialize_lits(height, width, blocks):
    return serialize_problem_as_url(LITS_COMBINATOR, "lits", height, width, blocks)


def deserialize_lits(url):
    return deserialize_problem_as_url(LITS_COMBINATOR, url, return_size=True)


def _main():
    if len(sys.argv) == 1:
        height = 10
        width = 10
        b = [
            "0000000222",
            "0010002222",
            "1113332222",
            "5563444288",
            "5663422228",
            "5663223338",
            "5633333338",
            "6673339aaa",
            "6773999aab",
            "77bbbbbbbb",
        ]
        blocks = defaultdict(list)
        for y in range(height):
            for x in range(width):
                blocks[b[y][x]].append((y, x))
        blocks = list(blocks.values())

        is_sat, is_black = solve_lits(height, width, blocks)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", True: "#", False: "."}))
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            gen = generate_lits(height, width, verbose=True)
            if gen is not None:
                a = [[-1 for _ in range(width)] for _ in range(height)]
                for i, block in enumerate(gen):
                    for y, x in block:
                        a[y][x] = i
                for y in range(height):
                    for x in range(width):
                        print("{:2}".format(a[y][x]), end="", file=sys.stderr)
                    print(file=sys.stderr)
                print(serialize_lits(height, width, gen), flush=True)


if __name__ == "__main__":
    _main()
