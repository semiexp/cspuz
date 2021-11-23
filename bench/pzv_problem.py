import argparse
import sys
import time

from cspuz import problem_serializer
from cspuz.puzzle import nurikabe
from cspuz.generator import default_uniqueness_checker


def solve_nurikabe(url):
    problem = nurikabe.deserialize_nurikabe(url)
    height = len(problem)
    width = len(problem[0])
    is_sat, ans = nurikabe.solve_nurikabe(height, width, problem)
    if not is_sat:
        return False
    return default_uniqueness_checker(ans)


def solve_problem(url, height_lim=None, width_lim=None):
    info = problem_serializer.get_puzzle_info_from_url(url)
    if info is None:
        return None
    kind, height, width = info

    if height_lim is not None and height > height_lim:
        return None
    if width_lim is not None and width > width_lim:
        return None

    if kind == "nurikabe":
        return solve_nurikabe(url)
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
