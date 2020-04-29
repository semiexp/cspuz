from cspuz.puzzle import compass


def test_serialization():
    height = 5
    width = 5
    problem = [
        (1, 2, -1, 1, -1, -1),
        (2, 1, 2, -1, 5, 1),
        (2, 3, 5, -1, 3, -1),
        (3, 2, 1, -1, -1, 1)
    ]
    expected = 'https://puzz.link/p?compass/5/5/m..1.i25.1g53..i1..1m'
    assert compass.to_puzz_link_url(height, width, problem) == expected
