import argparse
import sys
import time

from cspuz import problem_serializer
from cspuz.puzzle import heyawake, lits, masyu, nurikabe, nurimisaki
from cspuz.generator import default_uniqueness_checker


def solve_nurikabe(url):
    problem = nurikabe.deserialize_nurikabe(url)
    height = len(problem)
    width = len(problem[0])
    is_sat, ans = nurikabe.solve_nurikabe(height, width, problem)
    return is_sat and default_uniqueness_checker(ans)


def solve_masyu(url):
    problem = masyu.deserialize_masyu(url)
    height = len(problem)
    width = len(problem[0])
    is_sat, ans = masyu.solve_masyu(height, width, problem)
    return is_sat and default_uniqueness_checker(ans)


def solve_heyawake(url):
    problem = heyawake.deserialize_heyawake(url)
    if problem is None:
        return None
    height, width, (rooms, clues) = problem
    for clue in clues:
        if clue > 15:
            # TODO: problem with large clue numbers are too difficult to solve
            return None
    is_sat, ans = heyawake.solve_heyawake(height, width, rooms, clues)
    return is_sat and default_uniqueness_checker(ans)


def solve_lits(url):
    problem = lits.deserialize_lits(url)
    if problem is None:
        return None
    height, width, rooms = problem
    is_sat, ans = lits.solve_lits(height, width, rooms)
    return is_sat and default_uniqueness_checker(ans)


def solve_nurimisaki(url):
    problem = nurimisaki.deserialize_nurimisaki(url)
    height = len(problem)
    width = len(problem[0])
    is_sat, ans = nurimisaki.solve_nurimisaki(height, width, problem)
    return is_sat and default_uniqueness_checker(ans)


PUZZLE_KIND_ALIAS = {
    "mashu": "masyu",
}


def solve_problem(url, height_lim=None, width_lim=None):
    info = problem_serializer.get_puzzle_info_from_url(url)
    if info is None:
        return None
    kind, height, width = info

    if height_lim is not None and height > height_lim:
        return None
    if width_lim is not None and width > width_lim:
        return None

    if kind in PUZZLE_KIND_ALIAS:
        kind = PUZZLE_KIND_ALIAS[kind]

    if kind == "nurikabe":
        return solve_nurikabe(url)
    elif kind == "masyu":
        return solve_masyu(url)
    elif kind == "heyawake":
        return solve_heyawake(url)
    elif kind == "lits":
        return solve_lits(url)
    elif kind == "nurimisaki":
        return solve_nurimisaki(url)
    else:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hmax", type=int)
    parser.add_argument("--wmax", type=int)
    args = parser.parse_args()

    hmax = args.hmax
    wmax = args.wmax

    idx = 0
    while True:
        idx += 1
        url = sys.stdin.readline().strip()
        if url == "":
            break

        start = time.time()
        res = solve_problem(url, height_lim=hmax, width_lim=wmax)
        elapsed = time.time() - start

        if res is None:
            continue
        elif res is False:
            print(f"{idx}\tnot solved", flush=True)
        else:
            print(f"{idx}\t{elapsed}", flush=True)


if __name__ == "__main__":
    main()
