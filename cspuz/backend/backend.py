from typing import Optional


class Backend:
    def solve(self):
        raise NotImplementedError

    def solve_irrefutably(self, is_answer_key):
        raise NotImplementedError

    def perf_stats(self) -> Optional[dict]:
        return None
