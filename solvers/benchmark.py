from typing import List, Dict, Any
import time
import copy
from .nqueens import NQueensSolver
from .sudoku import SudokuSolver
from .sudoku_generator import SudokuGenerator
from .cube2 import Cube2Solver


EASY_SUDOKU = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"
MEDIUM_SUDOKU = "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
HARD_SUDOKU = "800000000003600000070090200050007000000045700000100030001000068008500010090000400"
EXPERT_SUDOKU = "000000907000420180000705026100904000050000040000507009920108000034059000507000000"
EVIL_SUDOKU = "000000001000000230000400005000003000000060070020000008800009400050006000003100000"
MULTI_SOLUTION_SUDOKU = "123456789456789123789123456234567891567891234891234567345678912000000000000000000"
NO_SOLUTION_SUDOKU = "123456789145678923789123456234567891567891234891234567345678912678912345912345678"

CUBE_SCRAMBLE_1 = "WWWWRROOOOGGGGBBBBRRYYYY"  # 1步: U' 还原
CUBE_SCRAMBLE_2 = "WWWWOOGGGGBBBBRRRROOYYYY"  # 1步: D 还原
CUBE_SCRAMBLE_3 = "YWYWBBOORRGGOOBBRRGGWYWY"  # 2步: U2 L2 还原
CUBE_SCRAMBLE_4 = "YWYWBRGOOOGGGOBRRRBBWYWY"  # 2步: U' L2 还原
CUBE_SCRAMBLE_5 = "BWBWWOWOGGGGBYBYRRRROYOY"  # 1步: L' 还原


class Benchmark:
    PRESET_PUZZLES = [
        {
            "id": 1,
            "category": "nqueens",
            "name": "8皇后 - 所有解",
            "difficulty": "easy",
            "input": {"n": 8, "mode": "all"}
        },
        {
            "id": 2,
            "category": "nqueens",
            "name": "12皇后 - 解总数",
            "difficulty": "medium",
            "input": {"n": 12, "mode": "count"}
        },
        {
            "id": 3,
            "category": "nqueens",
            "name": "16皇后 - 单解",
            "difficulty": "hard",
            "input": {"n": 16, "mode": "one"}
        },
        {
            "id": 4,
            "category": "sudoku",
            "name": "数独简单",
            "difficulty": "easy",
            "input": {"board_string": EASY_SUDOKU, "mode": "solve"}
        },
        {
            "id": 5,
            "category": "sudoku",
            "name": "数独普通(含唯一解校验)",
            "difficulty": "medium",
            "input": {"board_string": MEDIUM_SUDOKU, "mode": "unique"}
        },
        {
            "id": 6,
            "category": "sudoku",
            "name": "数独困难",
            "difficulty": "hard",
            "input": {"board_string": HARD_SUDOKU, "mode": "solve"}
        },
        {
            "id": 7,
            "category": "sudoku",
            "name": "数独专家",
            "difficulty": "expert",
            "input": {"board_string": EXPERT_SUDOKU, "mode": "solve"}
        },
        {
            "id": 8,
            "category": "cube2",
            "name": "二阶魔方 简单(1步打乱)",
            "difficulty": "easy",
            "input": {"state_string": CUBE_SCRAMBLE_1}
        },
        {
            "id": 9,
            "category": "cube2",
            "name": "二阶魔方 中等(2步打乱)",
            "difficulty": "medium",
            "input": {"state_string": CUBE_SCRAMBLE_3}
        },
        {
            "id": 10,
            "category": "cube2",
            "name": "二阶魔方 困难(1步打乱变种)",
            "difficulty": "hard",
            "input": {"state_string": CUBE_SCRAMBLE_5}
        },
    ]

    def __init__(self):
        self.queens_solver_cache = {}
        self.cube_solver = Cube2Solver()

    def _run_nqueens(self, puzzle: Dict[str, Any]) -> Dict[str, Any]:
        inp = puzzle["input"]
        n = inp["n"]
        mode = inp["mode"]

        t0 = time.perf_counter()
        if n not in self.queens_solver_cache:
            self.queens_solver_cache[n] = NQueensSolver(n)
        solver = self.queens_solver_cache[n]

        if mode == "count":
            result = solver.count_solutions()
            output = {"count": result}
        elif mode == "one":
            solution, stats = solver.solve_one(include_stats=True)
            output = {"solution": solution, "stats": stats}
        elif mode == "all":
            solutions, stats = solver.solve_all(include_stats=True)
            output = {"solutions_count": len(solutions), "stats": stats,
                      "first_solution": solutions[0] if solutions else None}
        else:
            output = {"error": f"unknown mode: {mode}"}

        elapsed = (time.perf_counter() - t0) * 1000
        return {
            "puzzle_id": puzzle["id"],
            "name": puzzle["name"],
            "category": puzzle["category"],
            "difficulty": puzzle["difficulty"],
            "elapsed_ms": round(elapsed, 3),
            "success": True,
            "output": output
        }

    def _run_sudoku(self, puzzle: Dict[str, Any]) -> Dict[str, Any]:
        inp = puzzle["input"]
        board_str = inp["board_string"]
        mode = inp.get("mode", "solve")

        t0 = time.perf_counter()
        try:
            board = SudokuSolver.board_from_string(board_str)
            solver = SudokuSolver(board)

            if mode == "solve":
                solution, stats = solver.solve_one(include_stats=True)
                output = {"solution_string": SudokuSolver.board_to_string(solution) if solution else None,
                          "stats": stats}
            elif mode == "unique":
                status, sols, stats = solver.check_uniqueness()
                if status == "unique":
                    output = {"status": status,
                              "solution_string": SudokuSolver.board_to_string(sols),
                              "stats": stats}
                elif status == "multiple":
                    output = {"status": status,
                              "solution_strings": [SudokuSolver.board_to_string(s) for s in sols[:2]],
                              "stats": stats}
                else:
                    output = {"status": status, "stats": stats}
            else:
                output = {"error": f"unknown mode: {mode}"}

            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "puzzle_id": puzzle["id"],
                "name": puzzle["name"],
                "category": puzzle["category"],
                "difficulty": puzzle["difficulty"],
                "elapsed_ms": round(elapsed, 3),
                "success": True,
                "output": output
            }
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "puzzle_id": puzzle["id"],
                "name": puzzle["name"],
                "category": puzzle["category"],
                "difficulty": puzzle["difficulty"],
                "elapsed_ms": round(elapsed, 3),
                "success": False,
                "error": str(e)
            }

    def _run_cube(self, puzzle: Dict[str, Any]) -> Dict[str, Any]:
        inp = puzzle["input"]
        state = inp["state_string"]

        t0 = time.perf_counter()
        try:
            result = self.cube_solver.solve(state, include_stats=True, max_depth=6)
            if result is None:
                moves, stats = None, {"error": "solver max_depth exceeded"}
            else:
                moves, stats = result
            if moves is not None:
                ok, msg = self.cube_solver.verify_solution(state, moves)
                output = {
                    "moves": moves,
                    "move_count": len(moves),
                    "verified": ok,
                    "verify_message": msg,
                    "stats": stats
                }
            else:
                output = {"moves": None, "stats": stats}

            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "puzzle_id": puzzle["id"],
                "name": puzzle["name"],
                "category": puzzle["category"],
                "difficulty": puzzle["difficulty"],
                "elapsed_ms": round(elapsed, 3),
                "success": moves is not None,
                "output": output
            }
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            return {
                "puzzle_id": puzzle["id"],
                "name": puzzle["name"],
                "category": puzzle["category"],
                "difficulty": puzzle["difficulty"],
                "elapsed_ms": round(elapsed, 3),
                "success": False,
                "error": str(e)
            }

    def run(self, puzzles: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if puzzles is None:
            puzzles = self.PRESET_PUZZLES

        results = []
        for puzzle in puzzles:
            cat = puzzle["category"]
            if cat == "nqueens":
                results.append(self._run_nqueens(puzzle))
            elif cat == "sudoku":
                results.append(self._run_sudoku(puzzle))
            elif cat == "cube2":
                results.append(self._run_cube(puzzle))
            else:
                results.append({
                    "puzzle_id": puzzle["id"],
                    "name": puzzle["name"],
                    "category": cat,
                    "difficulty": puzzle["difficulty"],
                    "elapsed_ms": 0,
                    "success": False,
                    "error": f"unknown category: {cat}"
                })

        sorted_by_time = sorted(results, key=lambda r: r["elapsed_ms"])
        total_ms = sum(r["elapsed_ms"] for r in results)
        success_count = sum(1 for r in results if r["success"])

        return {
            "total_puzzles": len(results),
            "success_count": success_count,
            "failure_count": len(results) - success_count,
            "total_elapsed_ms": round(total_ms, 3),
            "avg_elapsed_ms": round(total_ms / len(results), 3) if results else 0,
            "leaderboard": sorted_by_time,
            "slowest_5": sorted(results, key=lambda r: r["elapsed_ms"], reverse=True)[:5],
            "category_stats": self._category_stats(results)
        }

    def _category_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        cats = {}
        for r in results:
            c = r["category"]
            if c not in cats:
                cats[c] = {"count": 0, "total_ms": 0, "success": 0}
            cats[c]["count"] += 1
            cats[c]["total_ms"] += r["elapsed_ms"]
            if r["success"]:
                cats[c]["success"] += 1
        for c in cats:
            cats[c]["avg_ms"] = round(cats[c]["total_ms"] / cats[c]["count"], 3)
            cats[c]["total_ms"] = round(cats[c]["total_ms"], 3)
        return cats
