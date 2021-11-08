from cspuz.problem_serializer import (CombinatorEnv, Dict, Spaces, HexInt,
                                      OneOf, Seq, Grid)
from cspuz.puzzle.nurikabe import serialize_nurikabe, deserialize_nurikabe


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

    def test_spaces(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = Spaces(0, 'f')

        assert combinator.serialize(env, [0, 0, 0], 0) == (3, "h")
        assert combinator.serialize(env, [0, 0, 0], 1) == (2, "g")
        assert combinator.serialize(env, [0, 0, 0], 3) is None
        assert combinator.serialize(env, [1, 2], 0) is None
        assert combinator.serialize(env, [0] * 30, 0) == (21, "z")

        assert combinator.deserialize(env, "fh", 0) == (1, [0])
        assert combinator.deserialize(env, "fh", 1) == (1, [0, 0, 0])
        assert combinator.deserialize(env, "e", 0) is None
        assert combinator.deserialize(env, "z", 0) == (1, [0] * 21)

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

    def test_seq(self):
        env = CombinatorEnv(height=1, width=1)
        combinator = Seq(HexInt(), 3)

        assert combinator.serialize(env, [[1, 42, 256]], 0) == (1, "1-2a+100")
        assert combinator.serialize(env, [[1, 42, 256]], 1) is None

        assert combinator.deserialize(env, "1-2a+100", 0) == (8, [[1, 42,
                                                                   256]])
        assert combinator.deserialize(env, "1-2a+100", 1) is None

    def test_grid(self):
        env = CombinatorEnv(height=2, width=3)
        combinator = Grid(HexInt())

        assert combinator.serialize(env, [[
            [1, 42, 256],
            [0, 1, 2],
        ]], 0) == (1, "1-2a+100012")
        assert combinator.serialize(env, [[
            [1, 42, 256],
            [0, 1, 2],
        ]], 1) is None

        assert combinator.deserialize(env, "1-2a+100012",
                                      0) == (11, [[[1, 42, 256], [0, 1, 2]]])
        assert combinator.deserialize(env, "1-2a+100012", 1) is None


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
