import time
from cspuz.generator.srandom import use_deterministic_prng
import cspuz.puzzle.masyu as masyu


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


def main():
    bench_masyu()


if __name__ == "__main__":
    main()
