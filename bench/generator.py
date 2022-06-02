import sys
import time
from cspuz.generator.srandom import use_deterministic_prng
import cspuz.puzzle.masyu as masyu
import cspuz.puzzle.nurimisaki as nurimisaki
import cspuz.puzzle.slitherlink as slitherlink
import cspuz.puzzle.sudoku as sudoku


def run_generator_bench(bench_name, generator, serializer, num_problems, expected):
    use_deterministic_prng(True, seed=0)
    start = time.time()
    for i in range(num_problems):
        while True:
            generated = generator()
            if generated is not None:
                break
        serialized = serializer(generated)
        if expected is not None:
            assert expected[i] == serialized
        else:
            print(serialized)
    elapsed = time.time() - start

    print(f"{bench_name}: {elapsed}")


def bench_masyu():
    expected = [
        "https://puzz.link/p?masyu/10/10/2051020b00010300i0i50020002696020i",
        "https://puzz.link/p?masyu/10/10/00266000600220603230i09000c00169i0",
        "https://puzz.link/p?masyu/10/10/0023i30090366000080i1326000021160i",
        "https://puzz.link/p?masyu/10/10/063o03000003oil032813601000ia9i030",
        "https://puzz.link/p?masyu/10/10/210030390600409i0182i00200010i0i20",
        "https://puzz.link/p?masyu/10/10/29602f009230300003369i20000i0306i0",
        "https://puzz.link/p?masyu/10/10/0063399k90i020i060k000029i0106300i",
        "https://puzz.link/p?masyu/10/10/31020ii0902100000006020391i1900i20",
        "https://puzz.link/p?masyu/10/10/1030602002130303i1203000000f3i0b00",
        "https://puzz.link/p?masyu/10/10/j0000i030i060007k6c000600i00006b00",
    ]
    run_generator_bench(
        "masyu",
        lambda: masyu.generate_masyu(height=10, width=10, symmetry=False, verbose=False),
        masyu.serialize_masyu,
        10,
        expected,
    )


def bench_slitherlink():
    # TODO: add URL serializer and use it
    def serializer(problem):
        res = []
        for row in problem:
            for x in row:
                if x == -1:
                    res.append(".")
                else:
                    res.append(str(x))
        return "".join(res)

    expected = [
        "....2....1.0..2.23..32.3.122....1.....201..3.......0....32.01.2.3..1........1.2.3..0..2..2...3.12..0",  # noqa: E501
        "3...221.3.3.2....1......32.3.120..2...0..1.3....32...01..1..1.3....1.10.1..02....3....3.3.1...32....",  # noqa: E501
        "...1.0..2..3.22...110.10.10...12.......0...3.....201.2.11.22.1.1.33..3......1.0.1...31.1..3.0.32.0..",  # noqa: E501
        "2...3..3..3.3...311.2..3...2.......3.0.101...3..31..12.....30.1......3.3.....202...3..3......3.13..1",  # noqa: E501
        "...23.0...2...03....0.22.30..........1........1.31.12.1.1...0..10.12.12.2.1.3..0.....0....3.0..2.0..",  # noqa: E501
        "....3...3.2.0..0.22.0.1.....02.22..3....2.30...1.12..2..113..1.13..3.....1.........3.231.210.......2",  # noqa: E501
        "...0.1...23...1..2.2..0...10..22..2.33....3.02....2.2.....020....2223...2...3.20..22.2.....022.1..1.",  # noqa: E501
        "3.2....0...110113..0..1.1.....1.....1.23..2...0...323....3.0...3.1.23110.1...1....33...1.0.1...2.2..",  # noqa: E501
        "...0.3.01.1.11..2...31....2.3...2..0.1.23....1.....3..22..33.1..12.1...12...3..3....3.3...11...2..0.",  # noqa: E501
        ".2....3333.1.3...1..3.022....31....03.....1.11...1221..0..01...1...2..0.1..1.0.1...223.......3.2..0.",  # noqa: E501
    ]

    run_generator_bench(
        "slitherlink",
        lambda: slitherlink.generate_slitherlink(
            height=10, width=10, symmetry=False, verbose=False
        ),
        serializer,
        10,
        expected,
    )


def bench_nurimisaki():
    expected = [
        "https://puzz.link/p?nurimisaki/10/10/g.i.w.j.i.h.k.h.g.y.h.i.i.h.g.h.n.k",
        "https://puzz.link/p?nurimisaki/10/10/h.g.g.w.g.q.h.g.h.m.h.n.m.h.q.h.g.k",
        "https://puzz.link/p?nurimisaki/10/10/h.n.j.m.j.zh.h.j.n.m.m.l.g.k",
        "https://puzz.link/p?nurimisaki/10/10/w.i.j.h.h.h.m.l.j.r.g.i.j.h.h.s.",
        "https://puzz.link/p?nurimisaki/10/10/h.l.g.j.k.g.j.g.g.h.w.h.n.g.g.g.h.g.z.g",
        "https://puzz.link/p?nurimisaki/10/10/i.k.j.l.k.g.h.r.g.j.i.i.m.u.h.i.n",
        "https://puzz.link/p?nurimisaki/10/10/g.n.l.l.j.h.i.r.l.j.q.g.l.k.l.j",
        "https://puzz.link/p?nurimisaki/10/10/s.g.k.s.g.g.p.g.i.p.m.h.g.s.h.h",
        "https://puzz.link/p?nurimisaki/10/10/j.r.n.h.i.i.h.g.z.g.g.g.g.p.j.p.g",
        "https://puzz.link/p?nurimisaki/10/10/g.g.p.g.h.q.h.n.k.l.r.j.n.n.m",
    ]
    run_generator_bench(
        "nurimisaki",
        lambda: nurimisaki.generate_nurimisaki(10, 10, verbose=False),
        nurimisaki.serialize_nurimisaki,
        10,
        expected,
    )


def bench_sudoku():
    expected = [
        "https://puzz.link/p?sudoku/9/9/l768g3g2g7o4h1j2h43h4g5h92h6j7h5o5g9g1g824l",
        "https://puzz.link/p?sudoku/9/9/i1k7j659h6j7j13j8g5g7g8g4g6j42j2j7h372j1k5i",
        "https://puzz.link/p?sudoku/9/9/i1g9k9j61j2h3i6h3g47j9j78g5h9i3h8j51j4k3g7i",
        "https://puzz.link/p?sudoku/9/9/h72j6g1g93q4h4i7g53j6j98g4i2h3q54g1g2j87h",
        "https://puzz.link/p?sudoku/9/9/g3m69i4l5g27h71m9g81g54g2m95h34g8l9i51m6g",
        "https://puzz.link/p?sudoku/9/9/2h4i8k15h6g7j5g1g2h3l4i2l6h9g1g2j6g6h98k4i7h5",
        "https://puzz.link/p?sudoku/9/9/4p8g2g9h21h6i8i4i5h53i47h8i9i7i3h46h5g4g7p5",
        "https://puzz.link/p?sudoku/9/9/6g8h4h9m83i6j5k2g7h5h7h4h1g4k5j9i84m1h5h2g6",
        "https://puzz.link/p?sudoku/9/9/7l3g16g9i2j65j3g6l4h8g9h7l1g6j25j8i3g65g7l2",
        "https://puzz.link/p?sudoku/9/9/n5k37g8g6g7m3h7g4i59168i9g5h2m5g6g9g82k2n",
    ]
    run_generator_bench(
        "sudoku",
        lambda: sudoku.generate_sudoku(3, symmetry=True, max_clue=24, verbose=False),
        sudoku.serialize_sudoku,
        10,
        expected,
    )


ALL_BENCHES = [
    (bench_masyu, "masyu"),
    (bench_slitherlink, "slitherlink"),
    (bench_nurimisaki, "nurimisaki"),
    (bench_sudoku, "sudoku"),
]


def main():
    flt = None
    if len(sys.argv) >= 2:
        flt = sys.argv[1].split(",")
    for bench, name in ALL_BENCHES:
        if flt is None or name in flt:
            bench()


if __name__ == "__main__":
    main()
