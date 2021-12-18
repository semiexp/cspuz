import argparse
from typing import List, Tuple
import random
import sys
import math

from cspuz import Solver, graph
from cspuz.constraints import count_true, fold_or
from cspuz.puzzle import util
from cspuz.problem_serializer import (
    OneOf,
    ValuedRooms,
    HexInt,
    Spaces,
    serialize_problem_as_url,
    deserialize_problem_as_url,
)

RectangularRepr = List[Tuple[int, int, int, int, int]]
RoomRepr = Tuple[List[List[Tuple[int, int]]], List[int]]


def convert_from_rectangular_repr(problem: RectangularRepr) -> RoomRepr:
    rooms = []
    clues = []
    for y0, x0, y1, x1, n in problem:
        room = []
        for y in range(y0, y1):
            for x in range(x0, x1):
                room.append((y, x))
        rooms.append(room)
        clues.append(n)
    return rooms, clues


def solve_heyawake(height, width, *problem):
    solver = Solver()
    is_black = solver.bool_array((height, width))
    solver.add_answer_key(is_black)
    graph.active_vertices_not_adjacent(solver, is_black)
    graph.active_vertices_connected(solver, ~is_black)

    if len(problem) == 1:
        rooms, clues = convert_from_rectangular_repr(problem[0])
    else:
        rooms, clues = problem

    room_id = [[-1 for _ in range(width)] for _ in range(height)]
    for i in range(len(rooms)):
        room_cells = []
        for y, x in rooms[i]:
            if room_id[y][x] != -1:
                raise ValueError(f"cell ({y}, {x}) belongs to multiple rooms")
            room_id[y][x] = i
            room_cells.append(is_black[y, x])
        if clues[i] >= 0:
            solver.ensure(count_true(room_cells) == clues[i])

    for y in range(height):
        for x in range(width):
            if room_id[y][x] == -1:
                raise ValueError(f"cell ({y}, {x}) belongs to no room")
            if y < height - 1 and room_id[y][x] != room_id[y + 1][x]:
                y2 = y + 1
                while y2 < height - 1:
                    if room_id[y2][x] != room_id[y2 + 1][x]:
                        solver.ensure(fold_or(is_black[y : (y2 + 2), x]))
                        break
                    y2 += 1
            if x < width - 1 and room_id[y][x] != room_id[y][x + 1]:
                x2 = x + 1
                while x2 < width - 1:
                    if room_id[y][x2] != room_id[y][x2 + 1]:
                        solver.ensure(fold_or(is_black[y, x : (x2 + 2)]))
                        break
                    x2 += 1

    is_sat = solver.solve()

    return is_sat, is_black


def enumerate_division_update(problem):
    ret = []
    for i in range(len(problem)):
        y0, x0, y1, x1, n = problem[i]
        if y1 - y0 >= 2:
            for y in range(y0 + 1, y1):
                # if x1 - x0 == 1 and (y - y0 == 1 or y1 - y == 1):
                #     continue
                # if y - y0 == 1 or y1 - y == 1:
                #     continue
                ret.append(([i], [(y0, x0, y, x1, -1), (y, x0, y1, x1, -1)]))
        if x1 - x0 >= 2:
            for x in range(x0 + 1, x1):
                # if y1 - y0 == 1 and (x - x0 == 1 and x1 - x == 1):
                #     continue
                # if x - x0 == 1 or x1 - x == 1:
                #     continue
                ret.append(([i], [(y0, x0, y1, x, -1), (y0, x, y1, x1, -1)]))
    for i in range(len(problem)):
        if i == 0:
            continue
        for j in range(i):
            if j == 0:
                continue
            y0a, x0a, y1a, x1a, na = problem[i]
            y0b, x0b, y1b, x1b, nb = problem[j]
            if y0a == y0b and y1a == y1b and (x1a == x0b or x1b == x0a):
                y0 = y0a
                y1 = y1a
                x0 = min(x0a, x0b)
                x1 = max(x1a, x1b)
            elif x0a == x0b and x1a == x1b and (y1a == y0b or y1b == y0a):
                x0 = x0a
                x1 = x1a
                y0 = min(y0a, y0b)
                y1 = max(y1a, y1b)
            else:
                continue
            ret.append(([i, j], [(y0, x0, y1, x1, -1)]))
    return ret


def num_thin_blocks(problem):
    ret = 0
    for y0, x0, y1, x1, n in problem:
        if y1 - y0 == 1:
            ret += 1
        if x1 - x0 == 1:
            ret += 1
    return ret


def num_max_black_cells(h, w):
    # Formula: https://web.archive.org/web/20181106095427/http://www.geocities.co.jp/HeartLand-Poplar/2112/heyawake_mx/  # noqa: E501
    if h == 1 or w == 1:
        return (h * w + 1) // 2
    elif h == 3 or w == 3:
        n = h + w - 3
        k = (n + 1) // 4
        return 5 * k + [0, 2, 3, 0][n % 4]
    else:
        if h == 7 and w == 7:
            # (2^k-1) * (2^k-1) cases are very limited
            return 21
        elif h % 2 == 1 and w % 2 == 1:
            return (h * w + h + w - 1) // 3
        else:
            return (h * w + h + w - 2) // 3


def enumerate_clue_update(problem, min_clue=None, max_clue=None, no_limit_clue=False):
    ret = []
    for i in range(len(problem)):
        if i == 0:
            continue
        y0, x0, y1, x1, n = problem[i]
        nmax = num_max_black_cells(y1 - y0, x1 - x0)
        for n2 in range(-1, nmax + 1):
            if n2 == n:
                continue
            if n2 != -1:
                if min_clue is not None and n2 < min_clue:
                    continue
                if max_clue is not None and max_clue < n2:
                    continue
                if no_limit_clue and n2 == nmax:
                    continue
            ret.append(([i], [(y0, x0, y1, x1, n2)]))
    return ret


def compute_score(is_black):
    score = 0
    for v in is_black:
        if v.sol is not None:
            score += 1
    return score


def compute_clue_score(problem):
    clue_score = 0
    for y0, x0, y1, x1, n in problem:
        if n != -1:
            clue_score += 5  # n * 2 + (y1 - y0) * (x1 - x0) * 0.2
        # 'thin' blocks are not preferred
        if y1 - y0 == 1:
            clue_score += 2
        if x1 - x0 == 1:
            clue_score += 2
    return clue_score


def generate_heyawake(
    height,
    width,
    n_max_rooms=None,
    min_clue=None,
    max_clue=None,
    no_limit_clue=False,
    verbose=False,
):
    if n_max_rooms is None:
        n_max_rooms = height * width
    problem = [(0, 0, height, width, -1)]
    score = -compute_clue_score(problem)
    temperature = 5.0
    fully_solved_score = height * width

    for step in range(height * width):
        cand = enumerate_division_update(problem)
        random.shuffle(cand)

        for elim, app in cand:
            num_rooms = len(problem) + len(app) - len(elim)
            if num_rooms <= n_max_rooms:
                problem2 = [x for i, x in enumerate(problem) if i not in elim] + app
                if num_thin_blocks(problem2) <= 3:
                    problem = problem2
                    break

    for step in range(height * width * 10):
        cand = enumerate_division_update(problem) + enumerate_clue_update(
            problem, min_clue=min_clue, max_clue=max_clue, no_limit_clue=no_limit_clue
        )
        random.shuffle(cand)

        for elim, app in cand:
            num_rooms = len(problem) + len(app) - len(elim)
            if num_rooms > n_max_rooms:
                continue
            problem2 = [x for i, x in enumerate(problem) if i not in elim]
            problem2 += app

            if num_thin_blocks(problem2) > 5:
                continue
            sat, is_black = solve_heyawake(height, width, problem2)
            if not sat:
                score_next = -1
                update = False
            else:
                raw_score = compute_score(is_black)
                if raw_score == fully_solved_score:
                    return problem2
                clue_score = compute_clue_score(problem2)
                score_next = raw_score - clue_score
                update = score < score_next or random.random() < math.exp(
                    (score_next - score) / temperature
                )

            if update:
                if verbose:
                    print(
                        "update: {} -> {} ({} {})".format(
                            score, score_next, raw_score, clue_score
                        ),
                        file=sys.stderr,
                    )
                problem = problem2
                score = score_next
                break
            else:
                continue
        temperature *= 0.995
    if verbose or True:
        print("failed", file=sys.stderr)
    return None


HEYAWAKE_COMBINATOR = ValuedRooms(
    OneOf(HexInt(), Spaces(-1, "g")), skip_on_error=True, allow_redundant_border=False
)


def serialize_heyawake(height, width, *problem):
    if len(problem) == 1:
        rooms, clues = convert_from_rectangular_repr(problem[0])
    else:
        rooms, clues = problem
    return serialize_problem_as_url(HEYAWAKE_COMBINATOR, "heyawake", height, width, (rooms, clues))


def deserialize_heyawake(url) -> RoomRepr:
    return deserialize_problem_as_url(
        HEYAWAKE_COMBINATOR, url, allowed_puzzles="heyawake", allow_failure=True, return_size=True
    )


def _main():
    if len(sys.argv) == 1:
        # original example: http://pzv.jp/p.html?heyawake/6/6/aa66aapv0fu0g2i3k
        height = 6
        width = 6
        problem = [
            (0, 0, 1, 2, -1),
            (0, 2, 2, 4, 2),
            (0, 4, 1, 6, -1),
            (1, 0, 2, 2, -1),
            (1, 4, 3, 6, -1),
            (2, 0, 4, 3, 3),
            (2, 3, 4, 4, -1),
            (3, 4, 4, 6, -1),
            (4, 0, 6, 2, -1),
            (4, 2, 6, 4, -1),
            (4, 4, 6, 6, -1),
        ]
        is_sat, is_black = solve_heyawake(height, width, problem)
        print("has answer:", is_sat)
        if is_sat:
            print(util.stringify_array(is_black, {None: "?", True: "#", False: "."}))
    else:
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-h", "--height", type=int, required=True)
        parser.add_argument("-w", "--width", type=int, required=True)
        parser.add_argument("--max-rooms", type=int)
        parser.add_argument("--min-clue", type=int)
        parser.add_argument("--max-clue", type=int)
        parser.add_argument("--no-limit-clue", action="store_true")
        parser.add_argument("-v", "--verbose", action="store_true")

        args = parser.parse_args()
        height = args.height
        width = args.width
        while True:
            problem = generate_heyawake(
                height,
                width,
                n_max_rooms=args.max_rooms,
                min_clue=args.min_clue,
                max_clue=args.max_clue,
                no_limit_clue=args.no_limit_clue,
                verbose=args.verbose,
            )
            if problem is not None:
                url = serialize_heyawake(height, width, problem)
                print(url, flush=True)
                print(problem, file=sys.stderr)


if __name__ == "__main__":
    _main()
