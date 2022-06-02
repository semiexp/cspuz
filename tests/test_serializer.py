import pytest

from cspuz.problem_serializer import (
    CombinatorEnv,
    Dict,
    FixStr,
    Spaces,
    DecInt,
    HexInt,
    IntSpaces,
    MultiDigit,
    OneOf,
    Tupl,
    Seq,
    Grid,
    Rooms,
    ValuedRooms,
)
from cspuz.puzzle.nurikabe import serialize_nurikabe, deserialize_nurikabe
from cspuz.puzzle.masyu import serialize_masyu, deserialize_masyu
from cspuz.puzzle.norinori import serialize_norinori, deserialize_norinori
from cspuz.puzzle.slitherlink import serialize_slitherlink, deserialize_slitherlink


class TestSerializerCombinators:
    def test_dict(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = Dict([1, 2], ["x", "y"])

        assert combinator.serialize(env, [1, 2, 3], 0) == (1, "x")
        assert combinator.serialize(env, [1, 2, 3], 1) == (1, "y")
        assert combinator.serialize(env, [1, 2, 3], 2) is None
        assert combinator.serialize(env, [1, 2, 3], 3) is None
        assert combinator.serialize(env, [5], 0) is None

        assert combinator.deserialize(env, "xyz", 0) == (1, [1])
        assert combinator.deserialize(env, "xyz", 1) == (1, [2])
        assert combinator.deserialize(env, "xyz", 2) is None
        assert combinator.deserialize(env, "xyz", 3) is None

    def test_fixstr(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = FixStr("foo")

        assert combinator.serialize(env, [1, 2], 0) == (0, "foo")
        assert combinator.serialize(env, [1, 2], 2) == (0, "foo")

        assert combinator.deserialize(env, "foobar", 0) == (3, [])
        assert combinator.deserialize(env, "foobar", 1) is None
        assert combinator.deserialize(env, "foobar", 4) is None
        assert combinator.deserialize(env, "barfoo", 3) == (3, [])

    def test_spaces(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = Spaces(0, "f")

        assert combinator.serialize(env, [0, 0, 0], 0) == (3, "h")
        assert combinator.serialize(env, [0, 0, 0], 1) == (2, "g")
        assert combinator.serialize(env, [0, 0, 0], 3) is None
        assert combinator.serialize(env, [1, 2], 0) is None
        assert combinator.serialize(env, [0] * 30, 0) == (21, "z")

        assert combinator.deserialize(env, "fh", 0) == (1, [0])
        assert combinator.deserialize(env, "fh", 1) == (1, [0, 0, 0])
        assert combinator.deserialize(env, "e", 0) is None
        assert combinator.deserialize(env, "z", 0) == (1, [0] * 21)

    def test_decint(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = DecInt()

        assert combinator.serialize(env, [42, 0], 0) == (1, "42")
        assert combinator.serialize(env, [42, -3], 1) is None
        assert combinator.serialize(env, [42, 0], 2) is None

        assert combinator.deserialize(env, "42/-3", 0) == (2, [42])
        assert combinator.deserialize(env, "42/-3", 1) == (1, [2])
        assert combinator.deserialize(env, "42/-3", 2) is None
        assert combinator.deserialize(env, "42/-3", 3) is None
        assert combinator.deserialize(env, "42/-3", 4) == (1, [3])
        assert combinator.deserialize(env, "42/-3", 5) is None

    def test_hexint(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = HexInt()

        assert combinator.serialize(env, [0, 15, 30, 256], 0) == (1, "0")
        assert combinator.serialize(env, [0, 15, 30, 256], 1) == (1, "f")
        assert combinator.serialize(env, [0, 15, 30, 256], 2) == (1, "-1e")
        assert combinator.serialize(env, [0, 15, 30, 256], 3) == (1, "+100")
        assert combinator.serialize(env, [0, 15, 30, 256], 4) is None
        assert combinator.serialize(env, [4095, -1, 4096], 0) == (1, "+fff")
        assert combinator.serialize(env, [4095, -1, 4096], 1) is None
        assert combinator.serialize(env, [4095, -1, 4096], 2) is None

        assert combinator.deserialize(env, "0f-1e+100", 0) == (1, [0])
        assert combinator.deserialize(env, "0f-1e+100", 1) == (1, [15])
        assert combinator.deserialize(env, "0f-1e+100", 2) == (3, [30])
        assert combinator.deserialize(env, "0f-1e+100", 5) == (4, [256])
        assert combinator.deserialize(env, "+fff", 0) == (4, [4095])
        assert combinator.deserialize(env, "g0000", 0) is None
        assert combinator.deserialize(env, ".1234", 0) is None
        assert combinator.deserialize(env, "-1", 0) is None

    def test_int_spaces(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = IntSpaces(-1, 4, 2)

        assert combinator.serialize(env, [2, -1, 4], 0) == (2, "7")
        assert combinator.serialize(env, [2, -1, 4], 1) is None
        assert combinator.serialize(env, [2, -1, 4], 2) == (1, "4")
        assert combinator.serialize(env, [2, -1, 4], 3) is None
        assert combinator.serialize(env, [5, -1], 0) is None
        assert combinator.serialize(env, [-1, -1, -1], 0) is None
        assert combinator.serialize(env, [2, -1, -1, -1], 0) == (3, "c")

        assert combinator.deserialize(env, "74", 0) == (1, [2, -1])
        assert combinator.deserialize(env, "74", 1) == (1, [4])
        assert combinator.deserialize(env, "74", 2) is None
        assert combinator.deserialize(env, "f", 0) is None
        assert combinator.deserialize(env, "f", 0) is None
        assert combinator.deserialize(env, "c0", 0) == (1, [2, -1, -1])

    def test_multidigit(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = MultiDigit(base=4, digits=2)

        assert combinator.serialize(env, [1, 3, 2, 4], 0) == (2, "7")
        assert combinator.serialize(env, [1, 3, 2, 4], 1) == (2, "e")
        assert combinator.serialize(env, [1, 3, 2, 4], 2) is None
        assert combinator.serialize(env, [1, 3, 2, 4], 4) is None
        assert combinator.serialize(env, [1, 3, 2, 4, 3], 4) == (1, "c")

        assert combinator.deserialize(env, "7eg", 0) == (1, [1, 3])
        assert combinator.deserialize(env, "7eg", 1) == (1, [3, 2])
        assert combinator.deserialize(env, "7eg", 2) is None
        assert combinator.deserialize(env, "7eg", 3) is None

    def test_oneof(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = OneOf(Spaces(-1, "g"), HexInt())

        assert combinator.serialize(env, [-1, -1, 42, 0], 0) == (2, "h")
        assert combinator.serialize(env, [-1, -1, 42, 0], 1) == (1, "g")
        assert combinator.serialize(env, [-1, -1, 42, 0], 2) == (1, "-2a")
        assert combinator.serialize(env, [-1, -1, 42, 0], 3) == (1, "0")
        assert combinator.serialize(env, [-1, -1, 42, 0], 4) is None

        assert combinator.deserialize(env, "hg-2a0", 0) == (1, [-1, -1])
        assert combinator.deserialize(env, "hg-2a0", 1) == (1, [-1])
        assert combinator.deserialize(env, "hg-2a0", 2) == (3, [42])
        assert combinator.deserialize(env, "hg-2a0", 5) == (1, [0])
        assert combinator.deserialize(env, "hg-2a0", 6) is None
        assert combinator.deserialize(env, ".12345", 0) is None

    def test_tupl(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = Tupl(HexInt(), Spaces(-1, "g"))

        assert combinator.serialize(env, [([7], [-1, -1, 2])], 0) == (1, "7h")
        assert combinator.serialize(env, [([7], [-1, -1, 2])], 1) is None
        assert combinator.serialize(env, [([7], [2])], 0) is None

        assert combinator.deserialize(env, "7h", 0) == (2, [([7], [-1, -1])])
        assert combinator.deserialize(env, "7h", 1) is None
        assert combinator.deserialize(env, "775", 1) is None

    def test_seq(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = Seq(HexInt(), 3)

        assert combinator.serialize(env, [[1, 42, 256]], 0) == (1, "1-2a+100")
        assert combinator.serialize(env, [[1, 42, 256]], 1) is None

        assert combinator.deserialize(env, "1-2a+100", 0) == (8, [[1, 42, 256]])
        assert combinator.deserialize(env, "1-2a+100", 1) is None

    def test_grid(self):
        env = CombinatorEnv(height=2, width=3)
        combinator = Grid(HexInt())

        assert combinator.serialize(
            env,
            [
                [
                    [1, 42, 256],
                    [0, 1, 2],
                ]
            ],
            0,
        ) == (1, "1-2a+100012")
        assert (
            combinator.serialize(
                env,
                [
                    [
                        [1, 42, 256],
                        [0, 1, 2],
                    ]
                ],
                1,
            )
            is None
        )

        assert combinator.deserialize(env, "1-2a+100012", 0) == (11, [[[1, 42, 256], [0, 1, 2]]])
        assert combinator.deserialize(env, "1-2a+100012", 1) is None

    def test_grid_fixed_size(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = Grid(HexInt(), height=2, width=3)

        assert combinator.serialize(
            env,
            [
                [
                    [1, 42, 256],
                    [0, 1, 2],
                ]
            ],
            0,
        ) == (1, "1-2a+100012")
        assert (
            combinator.serialize(
                env,
                [
                    [
                        [1, 42, 256],
                        [0, 1, 2],
                    ]
                ],
                1,
            )
            is None
        )

        assert combinator.deserialize(env, "1-2a+100012", 0) == (11, [[[1, 42, 256], [0, 1, 2]]])
        assert combinator.deserialize(env, "1-2a+100012", 1) is None

    def test_rooms(self):
        env = CombinatorEnv(height=4, width=3)
        combinator = Rooms()

        assert combinator.serialize(
            env,
            [
                [
                    [(0, 0), (0, 1)],
                    [(0, 2), (1, 1), (1, 2)],
                    [(1, 0), (2, 0), (3, 0), (3, 1)],
                    [(2, 1), (2, 2), (3, 2)],
                ]
            ],
            0,
        ) == (1, "d4pk")

        with pytest.raises(ValueError):
            combinator.serialize(
                env,
                [
                    [
                        [(0, 0), (0, 1)],
                        [(0, 2), (1, 1), (1, 2)],
                        [(1, 0), (3, 0), (3, 1)],
                        [(2, 1), (2, 2), (3, 2)],
                    ]
                ],
                0,
            )  # (2, 0) does not belong to any room

        assert combinator.deserialize(env, "d4pk", 0) == (
            4,
            [
                [
                    [(0, 0), (0, 1)],
                    [(0, 2), (1, 1), (1, 2)],
                    [(1, 0), (2, 0), (3, 0), (3, 1)],
                    [(2, 1), (2, 2), (3, 2)],
                ]
            ],
        )

        with pytest.raises(ValueError):
            combinator.deserialize(env, "dkpg", 0)  # redundant border

    def test_valued_rooms(self):
        env = CombinatorEnv(height=4, width=3)
        combinator = ValuedRooms(OneOf(HexInt(), Spaces(-1, "g")))

        assert combinator.serialize(
            env,
            [
                (
                    [
                        [(0, 0), (0, 1)],
                        [(0, 2), (1, 2), (2, 1), (2, 2)],
                        [(1, 0), (1, 1), (2, 0), (3, 0)],
                        [(3, 1), (3, 2)],
                    ],
                    [1, 2, 0, -1],
                )
            ],
            0,
        ) == (1, "b8p6120g")

        assert combinator.deserialize(env, "b8p6120g", 0) == (
            8,
            [
                (
                    [
                        [(0, 0), (0, 1)],
                        [(0, 2), (1, 2), (2, 1), (2, 2)],
                        [(1, 0), (1, 1), (2, 0), (3, 0)],
                        [(3, 1), (3, 2)],
                    ],
                    [1, 2, 0, -1],
                )
            ],
        )


class TestSerializerPuzzles:
    def test_nurikabe(self):
        # https://twitter.com/semiexp/status/1222541993638678530
        url = "https://puzz.link/p?nurikabe/10/10/zj7n7j9n7t7i7n7zj"
        problem = deserialize_nurikabe(url)
        assert problem == [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 7, 0, 0, 0, 0, 0],
            [0, 0, 0, 7, 0, 0, 0, 0, 9, 0],
            [0, 0, 0, 0, 0, 0, 0, 7, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 7, 0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 0, 0, 7, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
        reserialized_url = serialize_nurikabe(problem)
        assert url == reserialized_url

    def test_masyu(self):
        # https://puzsq.jp/main/puzzle_play.php?pid=9833
        url = "https://puzz.link/p?masyu/10/10/0600003i06b1300600000a30600i090330"  # noqa: E501
        problem = deserialize_masyu(url)
        assert problem == [
            [0, 0, 0, 0, 2, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [0, 2, 0, 0, 0, 0, 0, 0, 2, 0],
            [1, 0, 2, 0, 0, 1, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 1, 0, 1, 0, 0],
            [0, 0, 0, 2, 0, 0, 0, 0, 0, 0],
            [0, 2, 0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 1, 0, 0],
        ]
        reserialized_url = serialize_masyu(problem)
        assert url == reserialized_url

    def test_norinori(self):
        # https://puzsq.jp/main/puzzle_play.php?pid=7919
        url = "https://puzz.link/p?norinori/6/6/93op35pb9vpq"
        problem = deserialize_norinori(url)
        assert problem == (
            6,
            6,
            [
                [(0, 0), (0, 1)],
                [(0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (3, 1)],
                [(0, 5), (1, 5)],
                [(1, 4), (2, 2), (2, 3), (2, 4), (2, 5)],
                [(2, 0), (3, 0)],
                [(3, 2), (3, 3), (3, 4), (4, 4)],
                [(3, 5), (4, 5), (5, 5)],
                [(4, 0), (4, 1), (4, 2), (4, 3), (5, 3), (5, 4)],
                [(5, 0), (5, 1), (5, 2)],
            ],
        )
        reserialized_url = serialize_norinori(*problem)
        assert url == reserialized_url

    def test_slitherlink(self):
        # https://puzz.link/p.html?slither/4/4/dgdh2c7b
        url = "https://puzz.link/p?slither/4/4/dgdh2c71"
        problem = deserialize_slitherlink(url)
        assert problem == [
            [3, -1, -1, -1],
            [3, -1, -1, -1],
            [-1, 2, 2, -1],
            [-1, 2, -1, 1],
        ]
        reserialized_url = serialize_slitherlink(problem)
        assert url == reserialized_url
