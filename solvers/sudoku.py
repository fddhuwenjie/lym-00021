from typing import List, Optional, Tuple, Dict, Any
import copy


class SudokuSolver:
    def __init__(self, board: Optional[List[List[int]]] = None):
        self.board = None
        if board is not None:
            self.set_board(board)
        self.reset_stats()

    def reset_stats(self):
        self.backtrack_count = 0
        self.prune_count = 0
        self.nodes_visited = 0

    def set_board(self, board: List[List[int]]):
        if len(board) != 9 or any(len(row) != 9 for row in board):
            raise ValueError("数独棋盘必须是 9x9")
        self.board = [row[:] for row in board]

    def _get_candidates(self, row: int, col: int, board: List[List[int]]) -> int:
        used = 0
        for i in range(9):
            if board[row][i] != 0:
                used |= 1 << board[row][i]
            if board[i][col] != 0:
                used |= 1 << board[i][col]
        br, bc = (row // 3) * 3, (col // 3) * 3
        for i in range(3):
            for j in range(3):
                val = board[br + i][bc + j]
                if val != 0:
                    used |= 1 << val
        return 0x3FE & ~used

    def _find_empty_mrv(self, board: List[List[int]]) -> Optional[Tuple[int, int, int]]:
        best = None
        best_count = 10
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    cand = self._get_candidates(r, c, board)
                    cnt = bin(cand).count("1")
                    if cnt == 0:
                        return (r, c, 0)
                    if cnt < best_count:
                        best_count = cnt
                        best = (r, c, cand)
                        if cnt == 1:
                            return best
        return best

    def _solve_one_internal(self, board: List[List[int]]) -> bool:
        self.nodes_visited += 1
        empty = self._find_empty_mrv(board)
        if empty is None:
            ok, _ = SudokuSolver.validate_board(board)
            return ok
        r, c, cand = empty
        if cand == 0:
            self.prune_count += 1
            return False
        while cand:
            p = cand & -cand
            cand -= p
            val = p.bit_length() - 1
            board[r][c] = val
            if self._solve_one_internal(board):
                return True
            board[r][c] = 0
            self.backtrack_count += 1
        return False

    def solve_one(self, include_stats: bool = False) -> Tuple[Optional[List[List[int]]], Dict[str, Any]]:
        self.reset_stats()
        board = [row[:] for row in self.board]
        ok = self._solve_one_internal(board)
        result = board if ok else None
        stats = {**self._get_stats(), "status": "solved" if ok else "no_solution"}
        return (result, stats) if include_stats else result

    def _count_solutions_internal(self, board: List[List[int]], limit: int, current: List[int]) -> int:
        self.nodes_visited += 1
        if current[0] >= limit:
            return current[0]
        empty = self._find_empty_mrv(board)
        if empty is None:
            current[0] += 1
            return current[0]
        r, c, cand = empty
        if cand == 0:
            self.prune_count += 1
            return current[0]
        while cand:
            p = cand & -cand
            cand -= p
            val = p.bit_length() - 1
            board[r][c] = val
            self._count_solutions_internal(board, limit, current)
            board[r][c] = 0
            self.backtrack_count += 1
            if current[0] >= limit:
                return current[0]
        return current[0]

    def count_solutions(self, limit: int = 2) -> Tuple[int, Dict[str, Any]]:
        self.reset_stats()
        board = [row[:] for row in self.board]
        counter = [0]
        self._count_solutions_internal(board, limit, counter)
        return counter[0], self._get_stats()

    def check_uniqueness(self) -> Tuple[str, Optional[List[List[int]]], Dict[str, Any]]:
        self.reset_stats()
        board = [row[:] for row in self.board]
        solutions = []
        self._collect_solutions(board, 2, solutions)
        stats = self._get_stats()
        if len(solutions) == 0:
            return "no_solution", None, stats
        elif len(solutions) == 1:
            return "unique", solutions[0], stats
        else:
            return "multiple", solutions[:2], stats

    def _collect_solutions(self, board: List[List[int]], limit: int, solutions: List[List[List[int]]]):
        self.nodes_visited += 1
        if len(solutions) >= limit:
            return
        empty = self._find_empty_mrv(board)
        if empty is None:
            solutions.append([row[:] for row in board])
            return
        r, c, cand = empty
        if cand == 0:
            self.prune_count += 1
            return
        while cand:
            p = cand & -cand
            cand -= p
            val = p.bit_length() - 1
            board[r][c] = val
            self._collect_solutions(board, limit, solutions)
            board[r][c] = 0
            self.backtrack_count += 1
            if len(solutions) >= limit:
                return

    def analyze_min_clues(self) -> Dict[str, Any]:
        """
        分析:
        - 总线索数
        - 能否移除某些线索仍保持唯一解
        - 最少线索数下界估计
        """
        self.reset_stats()
        original_clues = []
        for r in range(9):
            for c in range(9):
                if self.board[r][c] != 0:
                    original_clues.append((r, c, self.board[r][c]))

        total_clues = len(original_clues)

        status, solution, _ = self.check_uniqueness()
        if status != "unique":
            return {
                "status": status,
                "total_clues": total_clues,
                "message": "非唯一解，无法进行最少线索分析"
            }

        removable = []
        for (r, c, v) in original_clues:
            test_board = [row[:] for row in self.board]
            test_board[r][c] = 0
            solver = SudokuSolver(test_board)
            s, _, _ = solver.check_uniqueness()
            if s == "unique":
                removable.append({"row": r, "col": c, "value": v})

        essential_clues = [x for x in original_clues
                           if not any(rm["row"] == x[0] and rm["col"] == x[1] for rm in removable)]

        min_clues_lower_bound = max(
            len(essential_clues),
            17
        )

        return {
            "status": "ok",
            "total_clues": total_clues,
            "removable_clues": removable,
            "essential_clues_count": len(essential_clues),
            "essential_clues": [{"row": r, "col": c, "value": v} for (r, c, v) in essential_clues],
            "min_clues_lower_bound": min_clues_lower_bound,
            "achievable_min_clues_estimate": total_clues - len(removable),
            "theoretical_minimum": 17
        }

    def _get_stats(self) -> Dict[str, int]:
        return {
            "backtrack_count": self.backtrack_count,
            "prune_count": self.prune_count,
            "nodes_visited": self.nodes_visited
        }

    @staticmethod
    def validate_board(board: List[List[int]]) -> Tuple[bool, Optional[str]]:
        if len(board) != 9:
            return False, "必须是9行"
        for i, row in enumerate(board):
            if len(row) != 9:
                return False, f"第{i}行必须是9列"
            for j, v in enumerate(row):
                if not isinstance(v, int) or v < 0 or v > 9:
                    return False, f"位置({i},{j})值非法: {v}"

        for i in range(9):
            row_vals = set()
            col_vals = set()
            for j in range(9):
                rv = board[i][j]
                if rv != 0:
                    if rv in row_vals:
                        return False, f"第{i}行有重复值{rv}"
                    row_vals.add(rv)
                cv = board[j][i]
                if cv != 0:
                    if cv in col_vals:
                        return False, f"第{i}列有重复值{cv}"
                    col_vals.add(cv)

        for br in range(3):
            for bc in range(3):
                box_vals = set()
                for i in range(3):
                    for j in range(3):
                        v = board[br * 3 + i][bc * 3 + j]
                        if v != 0:
                            if v in box_vals:
                                return False, f"宫({br},{bc})有重复值{v}"
                            box_vals.add(v)

        return True, None

    @staticmethod
    def board_from_string(s: str) -> List[List[int]]:
        s = s.replace(".", "0").replace(" ", "").replace("\n", "")
        if len(s) != 81:
            raise ValueError(f"字符串长度必须为81，当前为{len(s)}")
        board = []
        for i in range(9):
            row = []
            for j in range(9):
                row.append(int(s[i * 9 + j]))
            board.append(row)
        return board

    @staticmethod
    def board_to_string(board: List[List[int]]) -> str:
        return "".join(str(board[r][c]) for r in range(9) for c in range(9))
