from typing import Any, List, Sequence


class XorShift:
    """An XorShift pseudo-random number generator (PRNG) with period 2^128-1.

    Although Python supplies an easy-to-use :obj:`random` module, it does not
    necessarily ensure the reproducibility across different versions of Python.
    If reproducibility is the top priority in your application (e.g. bench-
    marks), you may consider using this PRNG.

    Reference:
    Marsaglia, G. (2003). Xorshift RNGs. Journal of Statistical Software,
    8(14), 1-6. https://doi.org/10.18637/jss.v008.i14
    """

    def __init__(self, seed: int) -> None:
        """Initialize an XorShift PRNG with a seed.

        Args:
            seed (:obj:`int`): Seed for initialization.
            Note that only the lowest 32 bits in :obj:`seed` are used to seed
            this PRNG.
        """
        self._x = 123456789
        self._y = 362436069
        self._z = 521288629
        self._w = 88675123 ^ (seed & 0xFFFFFFFF)

    def next(self) -> int:
        """Return a random integer, modifying the internal states.

        Returns:
            int: A random integer in range [0, 2^31-1].
        """
        t = (self._x ^ (self._x << 11)) & 0xFFFFFFFF
        self._x = self._y
        self._y = self._z
        self._z = self._w
        self._w = (self._w ^ (self._w >> 19)) ^ (t ^ (t >> 8))
        return self._w


_XORSHIFT_DOMAIN_SIZE = 1 << 32
_rng = XorShift(0)


def seed(s: int) -> None:
    """Initialize the global PRNG with the given seed :obj:`s`.

    Args:
        s (int): Seed for initialization. See :obj:`XorShift::__init__` for
        details.
    """
    global _rng
    _rng = XorShift(s)


def randint(a: int, b: int) -> int:
    """Return an uniform random integer in range [:obj:`a`, :obj:`b`],
    inclusive.

    Args:
        a (int): The lower bound.
        b (int): The upper bound.

    Raises:
        ValueError: If the domain specified by :obj:`a` and :obj:`b` is
        invalid, i.e., :obj:`a` > :obj:`b` or :obj:`b` >= :obj:`a` + 2^32.

    Returns:
        int: A random integer.
    """
    global _rng

    if a > b:
        raise ValueError("`b` must be at least `a`")

    w = b - a + 1
    if w > _XORSHIFT_DOMAIN_SIZE:
        raise ValueError(f"domain size is too large: {w}")

    limit = _XORSHIFT_DOMAIN_SIZE - _XORSHIFT_DOMAIN_SIZE % w
    while True:
        x = _rng.next()
        if x < limit:
            return x % w


def choice(cand: Sequence[Any]) -> Any:
    """Pick an element in :obj:`cand` uniformly at random.

    Args:
        cand (:obj:`Sequence[Any]`): Candidates for choice.

    Raises:
        ValueError: If `cand` contains no element.

    Returns:
        :obj:`Any`: The picked element.
    """
    if len(cand) == 0:
        raise ValueError("`cand` is empty")

    idx = randint(0, len(cand) - 1)
    return cand[idx]


def shuffle(seq: List[Any]) -> None:
    """Shuffle :obj:`seq` uniformly at random. :obj:`seq` is modified.

    Args:
        seq (:obj:`List[Any]`): Sequence to be shuffled.
    """
    for i in range(1, len(seq)):
        j = randint(0, i)
        if i != j:
            seq[i], seq[j] = seq[j], seq[i]


def random() -> float:
    """Return a uniform random float number in [0, 1).

    Returns:
        :obj:`float`: A random number.
    """

    global _rng
    return float(_rng.next()) / _XORSHIFT_DOMAIN_SIZE
