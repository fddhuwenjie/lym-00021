from typing import List, Dict, Any, Tuple, Optional
import random
from .sudoku import SudokuSolver


class SudokuGenerator:
    """
    难度判定标准:
    ==============
    1. easy (简单):
       - 线索数: 40~50
       - 求解回溯次数: < 50
       - 可通过「唯一候选数法」和「宫/行/列排除法」直接解出
       - 大部分格子在某一步有唯一候选数(MRV=1)

    2. medium (普通/中等):
       - 线索数: 32~39
       - 求解回溯次数: 50 ~ 1,000
       - 需要用到「隐藏唯一数」或「数对」技巧
       - 普通难度需在 100ms 内返回

    3. hard (困难):
       - 线索数: 28~31
       - 求解回溯次数: 1,000 ~ 50,000
       - 需要用到「X-Wing」「XY-Wing」等高级技巧

    4. expert (专家):
       - 线索数: 24~27
       - 求解回溯次数: 50,000 ~ 1,000,000
       - 需要「链」「鱼」等高级技巧

    5. evil (地狱):
       - 线索数: 17~23 (17是理论最小值)
       - 求解回溯次数: > 1,000,000
       - 人类几乎无法手动解出
    """

    DIFFICULTY_CONFIG = {
        "easy": {
            "clue_min": 40,
            "clue_max": 50,
            "backtrack_min": 0,
            "backtrack_max": 50,
            "description": "40-50线索，回溯<50。新手可解。"
        },
        "medium": {
            "clue_min": 32,
            "clue_max": 39,
            "backtrack_min": 50,
            "backtrack_max": 1000,
            "description": "32-39线索，回溯50-1000。需简单技巧。"
        },
        "hard": {
            "clue_min": 28,
            "clue_max": 31,
            "backtrack_min": 1000,
            "backtrack_max": 50000,
            "description": "28-31线索，回溯1K-50K。需高级技巧。"
        },
        "expert": {
            "clue_min": 24,
            "clue_max": 27,
            "backtrack_min": 50000,
            "backtrack_max": 1000000,
            "description": "24-27线索，回溯50K-1M。需链/鱼技巧。"
        },
        "evil": {
            "clue_min": 17,
            "clue_max": 23,
            "backtrack_min": 1000000,
            "backtrack_max": 100000000,
            "description": "17-23线索，回溯>1M。人类几乎不可解。"
        }
    }

    @classmethod
    def get_difficulty_standards(cls) -> Dict[str, Any]:
        return {
            name: {
                **config,
                "is_difficulty_match": cls._is_difficulty_match.__doc__
            }
            for name, config in cls.DIFFICULTY_CONFIG.items()
        }

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def _generate_full_solution(self) -> List[List[int]]:
        board = [[0] * 9 for _ in range(9)]
        self._fill_board(board)
        return board

    def _fill_board(self, board: List[List[int]]) -> bool:
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    nums = list(range(1, 10))
                    self._rng.shuffle(nums)
                    for n in nums:
                        if self._can_place(board, r, c, n):
                            board[r][c] = n
                            if self._fill_board(board):
                                return True
                            board[r][c] = 0
                    return False
        return True

    def _can_place(self, board: List[List[int]], row: int, col: int, val: int) -> bool:
        for i in range(9):
            if board[row][i] == val or board[i][col] == val:
                return False
        br, bc = (row // 3) * 3, (col // 3) * 3
        for i in range(3):
            for j in range(3):
                if board[br + i][bc + j] == val:
                    return False
        return True

    @staticmethod
    def _count_clues(board: List[List[int]]) -> int:
        return sum(1 for r in range(9) for c in range(9) if board[r][c] != 0)

    @staticmethod
    def _measure_backtracks(board: List[List[int]]) -> int:
        solver = SudokuSolver(board)
        solver.solve_one(include_stats=True)
        return solver.backtrack_count

    @classmethod
    def _is_difficulty_match(cls, board: List[List[int]], difficulty: str) -> Tuple[bool, Dict[str, Any]]:
        config = cls.DIFFICULTY_CONFIG[difficulty]
        clues = cls._count_clues(board)
        backtracks = cls._measure_backtracks(board)

        clue_match = config["clue_min"] <= clues <= config["clue_max"]
        backtrack_match = config["backtrack_min"] <= backtracks <= config["backtrack_max"]

        return (clue_match and backtrack_match, {
            "clues": clues,
            "clue_range": [config["clue_min"], config["clue_max"]],
            "clue_match": clue_match,
            "backtracks": backtracks,
            "backtrack_range": [config["backtrack_min"], config["backtrack_max"]],
            "backtrack_match": backtrack_match,
        })

    def generate(self, difficulty: str = "medium", max_attempts: int = 2000,
                 seed: Optional[int] = None) -> Dict[str, Any]:
        if difficulty not in self.DIFFICULTY_CONFIG:
            raise ValueError(f"未知难度: {difficulty}，可选: {list(self.DIFFICULTY_CONFIG.keys())}")

        if seed is not None:
            self._rng = random.Random(seed)

        config = self.DIFFICULTY_CONFIG[difficulty]
        clue_target = self._rng.randint(config["clue_min"], config["clue_max"])

        for attempt in range(max_attempts):
            full_solution = self._generate_full_solution()
            puzzle = self._remove_cells_to_target(full_solution, clue_target)
            if puzzle is None:
                continue

            matched, info = self._is_difficulty_match(puzzle, difficulty)
            if matched:
                solver = SudokuSolver(puzzle)
                _, stats = solver.solve_one(include_stats=True)
                return {
                    "status": "ok",
                    "difficulty": difficulty,
                    "difficulty_description": config["description"],
                    "attempts": attempt + 1,
                    "puzzle": puzzle,
                    "puzzle_string": SudokuSolver.board_to_string(puzzle),
                    "full_solution": full_solution,
                    "full_solution_string": SudokuSolver.board_to_string(full_solution),
                    "metrics": {
                        "clues": info["clues"],
                        "backtrack_count": info["backtracks"],
                        "nodes_visited": stats.get("nodes_visited", 0),
                    }
                }
            else:
                pass

        return {
            "status": "max_attempts_exceeded",
            "difficulty": difficulty,
            "message": f"经过{max_attempts}次尝试仍未生成符合难度的题目，请尝试降低难度或增加max_attempts"
        }

    def _remove_cells_to_target(self, solution: List[List[int]],
                                target_clues: int) -> Optional[List[List[int]]]:
        board = [row[:] for row in solution]
        positions = [(r, c) for r in range(9) for c in range(9)]
        self._rng.shuffle(positions)

        clues = 81
        for r, c in positions:
            if clues <= target_clues:
                break
            saved = board[r][c]
            board[r][c] = 0
            solver = SudokuSolver(board)
            status, _, _ = solver.check_uniqueness()
            if status != "unique":
                board[r][c] = saved
            else:
                clues -= 1

        if clues < target_clues - 5:
            return None

        return board

    def classify_difficulty(self, board: List[List[int]]) -> Dict[str, Any]:
        clues = self._count_clues(board)
        backtracks = self._measure_backtracks(board)

        result = {
            "clues": clues,
            "backtrack_count": backtracks,
            "matches": {}
        }

        best_name = None
        best_score = -1

        for name, config in self.DIFFICULTY_CONFIG.items():
            clue_match = config["clue_min"] <= clues <= config["clue_max"]
            backtrack_match = config["backtrack_min"] <= backtracks <= config["backtrack_max"]
            score = 0
            if clue_match:
                score += 1
            if backtrack_match:
                score += 1
            result["matches"][name] = {
                "clue_match": clue_match,
                "backtrack_match": backtrack_match,
                "match_score": score,
                "description": config["description"]
            }
            if score > best_score:
                best_score = score
                best_name = name

        result["predicted_difficulty"] = best_name
        result["prediction_confidence"] = best_score / 2
        return result
