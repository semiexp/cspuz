import random
from collections import deque
from copy import deepcopy

from cspuz.generator.builder import Builder


class SegmentationBuilder2D(Builder):
    def __init__(self, height, width, min_num_blocks=None, max_num_blocks=None,
                 min_block_size=None, max_block_size=None, allow_unmet_constraints_first=False):
        self.height = height
        self.width = width
        self.min_num_blocks = min_num_blocks or 1
        self.max_num_blocks = max_num_blocks or (height * width)
        self.min_block_size = min_block_size or 1
        self.max_block_size = max_block_size or (height * width)
        self.allow_unmet_constraints_first = allow_unmet_constraints_first

    def initial(self):
        block = []
        for y in range(self.height):
            for x in range(self.width):
                block.append((y, x))
        blocks = [block]
        if self.allow_unmet_constraints_first:
            return blocks
        while True:
            is_met = True
            if not (self.min_num_blocks <= len(blocks) <= self.max_num_blocks):
                is_met = False
            for block in blocks:
                if not (self.min_block_size <= len(block) <= self.max_block_size):
                    is_met = False
            if is_met:
                return blocks
            cands = self.candidates(blocks)
            cand = random.choice(cands)
            blocks = self._copy_with_update(blocks, cand, use_deepcopy=False)

    def candidates(self, current):
        ret = []

        num_blocks = len(current)
        height = self.height
        width = self.width

        block_id = [[-1 for _ in range(width)] for _ in range(height)]
        for i, block in enumerate(current):
            for y, x in block:
                block_id[y][x] = i

        # merge
        if num_blocks > self.min_num_blocks:
            adjacent_pairs = set()
            for y in range(height):
                for x in range(width):
                    if y < height - 1 and block_id[y][x] != block_id[y + 1][x]:
                        i = block_id[y][x]
                        j = block_id[y + 1][x]
                        if len(current[i]) + len(current[j]) > self.max_block_size:
                            continue
                        if i < j:
                            adjacent_pairs.add((i, j))
                        else:
                            adjacent_pairs.add((j, i))
                    if x < width - 1 and block_id[y][x] != block_id[y][x + 1]:
                        i = block_id[y][x]
                        j = block_id[y][x + 1]
                        if len(current[i]) + len(current[j]) > self.max_block_size:
                            continue
                        if i < j:
                            adjacent_pairs.add((i, j))
                        else:
                            adjacent_pairs.add((j, i))
            for i, j in adjacent_pairs:
                ret.append(([i, j], [current[i] + current[j]]))

        # split
        if num_blocks < self.max_num_blocks:
            for i, block in enumerate(current):
                if len(block) >= self.min_block_size * 2:
                    for _ in range(2 * (len(block) - 1)):
                        block_a, block_b = split_block(block)
                        if len(block_a) >= self.min_block_size and len(block_b) >= self.min_block_size:
                            ret.append(([i], [block_a, block_b]))

        # mutate
        for y in range(height):
            for x in range(width):
                if y < height - 1 and block_id[y][x] != block_id[y + 1][x]:
                    i = block_id[y][x]
                    j = block_id[y + 1][x]
                    if len(current[i]) > self.min_block_size and len(current[j]) < self.max_block_size and _is_connected(current[i], (y, x)):
                        ret.append(([i, j], [[p for p in current[i] if p != (y, x)], current[j] + [(y, x)]]))
                    if len(current[j]) > self.min_block_size and len(current[i]) < self.max_block_size and _is_connected(current[j], (y + 1, x)):
                        ret.append(([i, j], [[p for p in current[j] if p != (y + 1, x)], current[i] + [(y + 1, x)]]))
                if x < width - 1 and block_id[y][x] != block_id[y][x + 1]:
                    i = block_id[y][x]
                    j = block_id[y][x + 1]
                    if len(current[i]) > self.min_block_size and len(current[j]) < self.max_block_size and _is_connected(current[i], (y, x)):
                        ret.append(([i, j], [[p for p in current[i] if p != (y, x)], current[j] + [(y, x)]]))
                    if len(current[j]) > self.min_block_size and len(current[i]) < self.max_block_size and _is_connected(current[j], (y, x + 1)):
                        ret.append(([i, j], [[p for p in current[j] if p != (y, x + 1)], current[i] + [(y, x + 1)]]))

        return ret

    def copy_with_update(self, previous, update):
        return self._copy_with_update(previous, update, use_deepcopy=True)

    def _copy_with_update(self, previous, update, use_deepcopy):
        exclude, append = update
        if use_deepcopy:
            return [deepcopy(previous[i]) for i in range(len(previous)) if i not in exclude] + append
        else:
            return [previous[i] for i in range(len(previous)) if i not in exclude] + append


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


def _is_connected(block, excluded):
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
