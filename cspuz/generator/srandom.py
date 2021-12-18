import random as pyrandom
from typing import Any, Optional, Sequence

import cspuz.generator.deterministic_random as drandom


_use_deterministic_prng = False


def use_deterministic_prng(enabled: bool, seed: Optional[int] = None) -> None:
    global _use_deterministic_prng
    _use_deterministic_prng = enabled
    if enabled:
        if seed is None:
            seed = 0
        drandom.seed(seed)


def is_use_deterministic_prng() -> bool:
    return _use_deterministic_prng


def randint(a: int, b: int) -> int:
    global _use_deterministic_prng
    if _use_deterministic_prng:
        return drandom.randint(a, b)
    else:
        return pyrandom.randint(a, b)


def choice(cand: Sequence[Any]) -> Any:
    global _use_deterministic_prng
    if _use_deterministic_prng:
        return drandom.choice(cand)
    else:
        return pyrandom.choice(cand)


def shuffle(seq: Sequence[Any]) -> None:
    global _use_deterministic_prng
    if _use_deterministic_prng:
        drandom.shuffle(seq)
    else:
        pyrandom.shuffle(seq)


def random() -> float:
    global _use_deterministic_prng
    if _use_deterministic_prng:
        return drandom.random()
    else:
        return pyrandom.random()
