import random
import math
import sys

from cspuz import Solver, BoolGridFrame, graph
from cspuz.constraints import count_true


def solve_castle_wall(height, width, arrow, inside):
    solver = Solver()
    grid_frame = BoolGridFrame(solver, height - 1, width - 1)
    solver.add_answer_key(grid_frame)
    passed = graph.active_edges_single_cycle(solver, grid_frame)

    # arrow constraints
    for y in range(height):
        for x in range(width):
            if arrow[y][x] == '..':
                continue
            solver.ensure(~passed[y, x])
            if arrow[y][x][0] == '^':
                related_edges = grid_frame.vertical[:y, x]
            elif arrow[y][x][0] == 'v':
                related_edges = grid_frame.vertical[y:, x]
            elif arrow[y][x][0] == '<':
                related_edges = grid_frame.horizontal[y, :x]
            elif arrow[y][x][0] == '>':
                related_edges = grid_frame.horizontal[y, x:]
            else:
                continue
            solver.ensure(count_true(related_edges) == int(arrow[y][x][1:]))

    # inout constraints
    is_inside = solver.bool_array((height - 1, width - 1))
    for y in range(height - 1):
        for x in range(width - 1):
            if y == 0:
                solver.ensure(is_inside[y, x] == grid_frame[0, x * 2 + 1])
            else:
                solver.ensure(is_inside[y, x] == (is_inside[y - 1, x] != grid_frame[y * 2, x * 2 + 1]))
    for y in range(height):
        for x in range(width):
            if inside[y][x] is True:
                solver.ensure(is_inside[max(0, y - 1), max(0, x - 1)])
            elif inside[y][x] is False:
                solver.ensure(~is_inside[max(0, y - 1), max(0, x - 1)])
    is_sat = solver.solve()

    return is_sat, grid_frame


def compute_score(grid_frame):
    score = 0
    for e in grid_frame:
        if e.sol is not None:
            score += 1
    return score


def trivial_decision(arrow):
    def max_lines(seq):
        ret = 0
        for i in range(1, len(seq)):
            if seq[i - 1] == '..' and seq[i] == '..':
                ret += 1
        return ret
    for y in range(height):
        for x in range(width):
            if arrow[y][x] == '..':
                continue
            if arrow[y][x][0] == '^':
                related_cells = [arrow[y2][x] for y2 in range(0, y)]
            elif arrow[y][x][0] == 'v':
                related_cells = [arrow[y2][x] for y2 in range(y + 1, height)]
            elif arrow[y][x][0] == '<':
                related_cells = [arrow[y][x2] for x2 in range(0, x)]
            elif arrow[y][x][0] == '>':
                related_cells = [arrow[y][x2] for x2 in range(x + 1, width)]
            else:
                continue
            if max_lines(related_cells) - 1 <= int(arrow[y][x][1:]):
                return True
    return False


def generate_castle_wall(height, width, disallow_trivial=False, verbose=False):
    arrow = [['..' for _ in range(width)] for _ in range(height)]
    inside = [[None for _ in range(width)] for _ in range(height)]
    score = 0
    temperature = 5.0
    fully_solved_score = height * (width - 1) + (height - 1) * width

    for step in range(height * width * 10):
        cand = []
        for y in range(height):
            for x in range(width):
                for d in ['^', 'v', '<', '>']:
                    adj = False
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            y2 = y + dy
                            x2 = x + dx
                            if abs(y2) + abs(x2) != 4 and (dy, dx) != (0, 0) and 0 <= y2 < height and 0 <= x2 < width and arrow[y2][x2] != '..':
                                adj = True
                    if adj:
                        continue
                    if (y <= 1 and d == '^') or (y >= height - 2 and d == 'v') or (x <= 1 and d == '<') or (x >= width - 2 and d == '>'):
                        continue
                    for n in range(1, 10):
                        for i in [True, False, None]:
                            a = d + str(n)
                            if d == '^' and n >= y:
                                continue
                            if d == '<' and n >= x:
                                continue
                            if d == 'v' and n >= height - y - 1:
                                continue
                            if d == '>' and n >= width - x - 1:
                                continue
                            if (a, i) != (arrow[y][x], inside[y][x]):
                                cand.append((y, x, a, i))
        random.shuffle(cand)

        for y, x, a, i in cand:
            a_prev = arrow[y][x]
            i_prev = inside[y][x]
            arrow[y][x] = a
            inside[y][x] = i

            if disallow_trivial and trivial_decision(arrow):
                sat = False
            else:
                sat, grid_frame = solve_castle_wall(height, width, arrow, inside)
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(grid_frame)
                if raw_score == fully_solved_score:
                    return arrow, inside
                clue_score = 0
                for y2 in range(height):
                    for x2 in range(width):
                        if arrow[y2][x2] != '..':
                            if arrow[y2][x2][0] == '?':
                                clue_score += 5
                            else:
                                clue_score += 8
                        if inside[y2][x2] != None:
                            clue_score += 2
                clue_score = max(0, clue_score - 20)
                score_next = raw_score - clue_score
                update = (score < score_next or random.random() < math.exp((score_next - score) / temperature))

            if update:
                if verbose:
                    print('update: {} -> {}'.format(score, score_next), file=sys.stderr)
                score = score_next
                break
            else:
                arrow[y][x] = a_prev
                inside[y][x] = i_prev

        temperature *= 0.995
    if verbose:
        print('failed', file=sys.stderr)
    return None


if __name__ == '__main__':
    while True:
        height, width = map(int, sys.argv[1:])
        problem = generate_castle_wall(height, width, verbose=True)
        if problem is not None:
            arrow, inside = problem
            for y in range(height):
                for x in range(width):
                    if arrow[y][x] == '..':
                        print('...', end=' ')
                    else:
                        if inside[y][x] is None:
                            sgn = '?'
                        elif inside[y][x]:
                            sgn = 'i'
                        else:
                            sgn = 'o'
                        print(arrow[y][x] + sgn, end=' ')
                print()
            print(flush=True)
