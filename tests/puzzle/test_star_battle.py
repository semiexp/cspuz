from cspuz.puzzle import star_battle


def test_serialization() -> None:
    n = 6
    k = 1
    block_id = [
        [0, 0, 0, 0, 1, 1],
        [0, 2, 3, 0, 1, 1],
        [2, 2, 3, 3, 3, 1],
        [2, 1, 1, 1, 1, 1],
        [2, 4, 4, 1, 4, 5],
        [2, 2, 4, 4, 4, 5],
    ]
    expected = "http://pzv.jp/p.html?starbattle/6/6/1/2u9gn9c9jpmk"
    assert star_battle.problem_to_pzv_url(n, k, block_id) == expected
