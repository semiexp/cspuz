import sys

from cspuz import Solver
from cspuz.puzzle import util
from cspuz.constraints import count_true
from cspuz.generator import generate_problem, Choice, SegmentationBuilder2D, count_non_default_values


def solve_aquarium(height, width, blocks, clue_row, clue_col):
    solver = Solver()
    is_water = solver.bool_array((height, width))
    solver.add_answer_key(is_water)

    for y in range(height):
        if clue_row[y] >= 0:
            solver.ensure(count_true(is_water[y, :]) == clue_row[y])
    for x in range(width):
        if clue_col[x] >= 0:
            solver.ensure(count_true(is_water[:, x]) == clue_col[x])
    block_id = [[-1 for _ in range(width)] for _ in range(width)]
    for i, block in enumerate(blocks):
        for y, x in block:
            block_id[y][x] = i
    for y in range(height):
        for x in range(width):
            if x < width - 1 and block_id[y][x] == block_id[y][x + 1]:
                solver.ensure(is_water[y, x] == is_water[y, x + 1])
            if y < height - 1 and block_id[y][x] == block_id[y + 1][x]:
                solver.ensure(is_water[y, x].then(is_water[y + 1, x]))
    is_sat = solver.solve()
    return is_sat, is_water


def generate_aquarium(height, width, verbose=False):
    builder_pattern = (
        SegmentationBuilder2D(height, width, min_block_size=1, max_block_size=3,
                              allow_unmet_constraints_first=False),
        [Choice([-1] + list(range(3, width - 2)), default=-1) for _ in range(height)],
        [Choice([-1] + list(range(3, height - 2)), default=-1) for _ in range(width)]
    )
    generated = generate_problem(lambda problem: solve_aquarium(height, width, *problem),
                                 builder_pattern=builder_pattern,
                                 clue_penalty=lambda problem: count_non_default_values(problem[1], default=-1, weight=4) + count_non_default_values(problem[2], default=-1, weight=4),
                                 verbose=verbose)
    return generated


def problem_to_url(height, width, blocks, clue_row, clue_col):
    blocks_str = util.encode_grid_segmentation(height, width, util.blocks_to_block_id(height, width, blocks))
    clues_str = util.encode_array(clue_col + clue_row, empty=-1)
    return 'https://puzz.link/p?aquarium/{}/{}/{}/{}'.format(width, height, blocks_str, clues_str)


def _main():
    if len(sys.argv) == 1:
        pass
    else:
        height, width = map(int, sys.argv[1:])
        while True:
            gen = generate_aquarium(height, width, verbose=False)
            if gen is not None:
                print(gen)
                print(problem_to_url(height, width, *gen))


if __name__ == '__main__':
    _main()
