from cspuz.puzzle import compass


def test_serialization():
    height = 5
    width = 4
    problem = [(1, 1, 1, 2, -1, 3), (2, 3, -1, 6, -1, -1), (3, 1, 4, -1, -1, 5)]
    expected = "https://puzz.link/p?compass/4/5/k1.23k..6.g4..5l"
    assert compass.to_puzz_link_url(height, width, problem) == expected
