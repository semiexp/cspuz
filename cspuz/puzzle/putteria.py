import sys

from cspuz import Solver
from cspuz.constraints import count_true
from cspuz.puzzle import util
from cspuz.generator import generate_problem, SegmentationBuilder2D


def solve_putteria(height, width, blocks):
    solver = Solver()
    has_number = solver.bool_array((height, width))
    solver.add_answer_key(has_number)

    solver.ensure((~has_number[:, :-1]) | (~has_number[:, 1:]))
    solver.ensure((~has_number[:-1, :]) | (~has_number[1:, :]))
    for block in blocks:
        solver.ensure(count_true([has_number[y, x] for y, x in block]) == 1)

    block_size = [[0 for _ in range(width)] for _ in range(height)]
    for block in blocks:
        for y, x in block:
            block_size[y][x] = len(block)
    for y in range(height):
        for x1 in range(width):
            for x2 in range(x1 + 1, width):
                if block_size[y][x1] == block_size[y][x2]:
                    solver.ensure(~(has_number[y, x1] & has_number[y, x2]))
    for x in range(width):
        for y1 in range(height):
            for y2 in range(y1 + 1, height):
                if block_size[y1][x] == block_size[y2][x]:
                    solver.ensure(~(has_number[y1, x] & has_number[y2, x]))

    is_sat = solver.solve()
    return is_sat, has_number


def generate_putteria(
    height, width, min_blocks=13, max_blocks=22, max_block_size=8, verbose=False
):
    generated = generate_problem(
        lambda problem: solve_putteria(height, width, problem),
        builder_pattern=SegmentationBuilder2D(
            height,
            width,
            min_num_blocks=min_blocks,
            max_num_blocks=max_blocks,
            min_block_size=3,
            max_block_size=max_block_size,
            allow_unmet_constraints_first=True,
        ),
        verbose=verbose,
    )
    return generated


def _main():
    if len(sys.argv) == 1:
        pass
    else:
        height, width, min_blocks, max_blocks, max_block_size = map(int, sys.argv[1:])
        while True:
            gen = generate_putteria(
                height,
                width,
                min_blocks=min_blocks,
                max_blocks=max_blocks,
                max_block_size=max_block_size,
                verbose=True,
            )
            print(gen, file=sys.stderr)
            if gen is not None:
                block_id = [[-1 for _ in range(width)] for _ in range(height)]
                for i, block in enumerate(gen):
                    for y, x in block:
                        block_id[y][x] = i
                url = util.encode_grid_segmentation(height, width, block_id)
                print(url, flush=True)


if __name__ == "__main__":
    _main()
