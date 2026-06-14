from typing import List, Optional, Dict, Any


class NQueensSolver:
    def __init__(self, n: int):
        self.n = n
        self.reset_stats()

    def reset_stats(self):
        self.backtrack_count = 0
        self.prune_count = 0
        self.nodes_visited = 0

    def count_solutions(self) -> int:
        self.reset_stats()
        if self.n == 0:
            return 0
        return self._count(0, 0, 0, 0)

    def _count(self, row: int, cols: int, diag1: int, diag2: int) -> int:
        self.nodes_visited += 1
        if row == self.n:
            return 1
        count = 0
        available = ((1 << self.n) - 1) & ~(cols | diag1 | diag2)
        while available:
            p = available & -available
            available -= p
            count += self._count(row + 1, cols | p, (diag1 | p) << 1, (diag2 | p) >> 1)
        return count

    def solve_one(self, include_stats: bool = False) -> Optional[List[int]]:
        self.reset_stats()
        if self.n == 0:
            result = None
            return (result, self._get_stats()) if include_stats else result
        solution = self._solve_one(0, 0, 0, 0, [])
        return (solution, self._get_stats()) if include_stats else solution

    def _solve_one(self, row: int, cols: int, diag1: int, diag2: int, placement: List[int]) -> Optional[List[int]]:
        self.nodes_visited += 1
        if row == self.n:
            return placement[:]
        available = ((1 << self.n) - 1) & ~(cols | diag1 | diag2)
        if available == 0:
            self.prune_count += 1
        while available:
            p = available & -available
            available -= p
            col = p.bit_length() - 1
            placement.append(col)
            result = self._solve_one(row + 1, cols | p, (diag1 | p) << 1, (diag2 | p) >> 1, placement)
            if result is not None:
                return result
            placement.pop()
            self.backtrack_count += 1
        return None

    def solve_all(self, limit: Optional[int] = None, include_stats: bool = False) -> List[List[int]]:
        self.reset_stats()
        if self.n == 0:
            result = []
            return (result, self._get_stats()) if include_stats else result
        solutions = []
        self._solve_all(0, 0, 0, 0, [], solutions, limit)
        return (solutions, self._get_stats()) if include_stats else solutions

    def _solve_all(self, row: int, cols: int, diag1: int, diag2: int,
                   placement: List[int], solutions: List[List[int]], limit: Optional[int]):
        self.nodes_visited += 1
        if limit is not None and len(solutions) >= limit:
            return
        if row == self.n:
            solutions.append(placement[:])
            return
        available = ((1 << self.n) - 1) & ~(cols | diag1 | diag2)
        if available == 0:
            self.prune_count += 1
        while available:
            p = available & -available
            available -= p
            col = p.bit_length() - 1
            placement.append(col)
            self._solve_all(row + 1, cols | p, (diag1 | p) << 1, (diag2 | p) >> 1, placement, solutions, limit)
            placement.pop()
            self.backtrack_count += 1

    def _get_stats(self) -> Dict[str, int]:
        return {
            "backtrack_count": self.backtrack_count,
            "prune_count": self.prune_count,
            "nodes_visited": self.nodes_visited
        }

    @staticmethod
    def to_board(placement: List[int]) -> List[str]:
        n = len(placement)
        return ["." * col + "Q" + "." * (n - col - 1) for col in placement]
