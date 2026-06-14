from flask import Flask, request, jsonify
import json
from solvers.nqueens import NQueensSolver
from solvers.sudoku import SudokuSolver
from solvers.sudoku_generator import SudokuGenerator
from solvers.cube2 import Cube2Solver
from solvers.counter import CounterSolver
from solvers.csp import CSPSolver
from solvers.benchmark import Benchmark

app = Flask(__name__)

_cube3_solver = None
_counter_solver = None

def get_cube3_solver():
    global _cube3_solver
    if _cube3_solver is None:
        from solvers.cube3 import Cube3Solver
        _cube3_solver = Cube3Solver()
    return _cube3_solver

def get_counter_solver():
    global _counter_solver
    if _counter_solver is None:
        _counter_solver = CounterSolver()
    return _counter_solver


def _error_response(message: str, code: int = 400):
    return jsonify({"status": "error", "message": message}), code


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "name": "CSP Solver API (约束满足问题求解服务)",
        "port": 8021,
        "endpoints": {
            "N皇后": {
                "POST /nqueens/solve": {
                    "params": {
                        "n": "int 棋盘大小",
                        "mode": "str 'one'|'all'|'count' (默认 'one')",
                        "limit": "int mode=all时限制返回解数 (可选)",
                        "include_board": "bool 是否返回棋盘字符串 (默认 false)",
                        "include_stats": "bool 是否返回搜索统计 (默认 true)"
                    }
                }
            },
            "数独": {
                "POST /sudoku/solve": {
                    "params": {
                        "board": "[[int]*9]*9 或 board_string: str (81字符)",
                        "mode": "str 'solve'|'unique'|'count' (默认 'solve')",
                        "include_stats": "bool (默认 true)"
                    }
                },
                "POST /sudoku/min_clues": {
                    "params": {
                        "board": "同上",
                        "board_string": "同上"
                    }
                },
                "POST /sudoku/generate": {
                    "params": {
                        "difficulty": "str 'easy'|'medium'|'hard'|'expert'|'evil' (默认 'medium')",
                        "max_attempts": "int (默认 2000)",
                        "seed": "int (可选)"
                    }
                },
                "GET /sudoku/standards": "获取难度判定标准"
            },
            "二阶魔方": {
                "POST /cube2/solve": {
                    "params": {
                        "state_string": "str 24字符 (WGRBOY各4个)",
                        "max_depth": "int (默认 14)",
                        "include_stats": "bool (默认 true)",
                        "verify": "bool 验证解是否正确 (默认 true)"
                    }
                },
                "GET /cube2/scramble": {
                    "params": {"length": "int (默认 8)"}
                }
            },
            "三阶魔方": {
                "POST /api/cube3/solve": {
                    "params": {
                        "state_string": "str 54字符 (URFDLB面序)",
                        "max_depth": "int (默认 20)",
                        "include_stats": "bool (默认 true)",
                        "verify": "bool 验证解是否正确 (默认 true)"
                    }
                },
                "POST /api/cube3/validate": {
                    "params": {
                        "state_string": "str 54字符 (URFDLB面序)"
                    }
                }
            },
            "解空间计数": {
                "POST /api/count": {
                    "params": {
                        "problem_type": "str 'nqueens' | 'sudoku' | 'cube2'",
                        "n": "int (nqueens时使用)",
                        "board": "[[int]*9]*9 或 board_string: str (sudoku时使用)",
                        "state_string": "str (cube2时使用)",
                        "include_stats": "bool (默认 true)"
                    }
                }
            },
            "通用CSP引擎": {
                "POST /api/csp/solve": {
                    "params": {
                        "problem": "CSP问题描述 (variables, domains, constraints)",
                        "mode": "str 'one' | 'all' (默认 'one')",
                        "solution_limit": "int mode=all时限制返回解数 (默认 100)",
                        "include_stats": "bool (默认 true)"
                    }
                },
                "GET /api/csp/examples": "获取预置经典CSP实例"
            },
            "基准测试": {
                "GET /benchmark": "运行预置10道混合题面",
                "POST /benchmark": "自定义题面列表运行"
            }
        }
    })


# ==================== N皇后 ====================
@app.route("/nqueens/solve", methods=["POST"])
def nqueens_solve():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    n = data.get("n")
    if n is None:
        return _error_response("缺少参数: n")
    if not isinstance(n, int) or n < 0 or n > 20:
        return _error_response("n 必须是 0~20 的整数")

    mode = data.get("mode", "one")
    if mode not in ("one", "all", "count"):
        return _error_response("mode 必须是 'one' | 'all' | 'count'")

    limit = data.get("limit")
    include_board = data.get("include_board", False)
    include_stats = data.get("include_stats", True)

    solver = NQueensSolver(n)

    response = {"status": "ok", "n": n, "mode": mode}

    if mode == "count":
        count = solver.count_solutions()
        response["solution_count"] = count
        if include_stats:
            response["stats"] = solver._get_stats()

    elif mode == "one":
        sol = solver.solve_one(include_stats=False)
        if sol is None:
            response["solution"] = None
        else:
            response["solution"] = sol
            if include_board:
                response["board"] = NQueensSolver.to_board(sol)
        if include_stats:
            response["stats"] = solver._get_stats()

    elif mode == "all":
        sols = solver.solve_all(limit=limit, include_stats=False)
        response["solution_count"] = len(sols)
        if limit is not None:
            response["limit"] = limit
            response["reached_limit"] = len(sols) >= limit if limit is not None else False
        if sols:
            response["first_solution"] = sols[0]
            response["solutions_preview"] = sols[:min(3, len(sols))]
            if include_board:
                response["first_board"] = NQueensSolver.to_board(sols[0])
        if include_stats:
            response["stats"] = solver._get_stats()

    return jsonify(response)


# ==================== 数独 ====================
def _parse_sudoku_input(data):
    board = data.get("board")
    board_string = data.get("board_string")

    if board is None and board_string is None:
        return None, None, "缺少参数: board 或 board_string"

    if board_string is not None:
        try:
            board = SudokuSolver.board_from_string(board_string)
        except ValueError as e:
            return None, None, str(e)

    if board is not None:
        ok, err = SudokuSolver.validate_board(board)
        if not ok:
            return None, None, f"棋盘校验失败: {err}"

    return board, board_string, None


@app.route("/sudoku/solve", methods=["POST"])
def sudoku_solve():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    board, _, err = _parse_sudoku_input(data)
    if err:
        return _error_response(err)

    mode = data.get("mode", "solve")
    include_stats = data.get("include_stats", True)

    if mode not in ("solve", "unique", "count"):
        return _error_response("mode 必须是 'solve' | 'unique' | 'count'")

    solver = SudokuSolver(board)

    response = {"status": "ok", "mode": mode}

    if mode == "solve":
        sol, stats = solver.solve_one(include_stats=True)
        if sol is None:
            response["result"] = "no_solution"
            response["solution"] = None
        else:
            response["result"] = "solved"
            response["solution"] = sol
            response["solution_string"] = SudokuSolver.board_to_string(sol)
        if include_stats:
            response["stats"] = stats

    elif mode == "unique":
        status, sols, stats = solver.check_uniqueness()
        response["result"] = status
        if status == "unique":
            response["solution"] = sols
            response["solution_string"] = SudokuSolver.board_to_string(sols)
        elif status == "multiple":
            response["solution_count_hint"] = ">=2"
            response["solutions_preview"] = [
                SudokuSolver.board_to_string(s) for s in sols[:2]
            ]
        else:
            response["solution"] = None
        if include_stats:
            response["stats"] = stats

    elif mode == "count":
        count, stats = solver.count_solutions(limit=1000)
        response["solution_count"] = count
        response["count_limit"] = 1000
        response["hit_limit"] = count >= 1000
        if include_stats:
            response["stats"] = stats

    return jsonify(response)


@app.route("/sudoku/min_clues", methods=["POST"])
def sudoku_min_clues():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    board, _, err = _parse_sudoku_input(data)
    if err:
        return _error_response(err)

    solver = SudokuSolver(board)
    result = solver.analyze_min_clues()

    return jsonify({"status": "ok", "analysis": result})


@app.route("/sudoku/generate", methods=["POST"])
def sudoku_generate():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    difficulty = data.get("difficulty", "medium")
    max_attempts = data.get("max_attempts", 2000)
    seed = data.get("seed")

    if difficulty not in SudokuGenerator.DIFFICULTY_CONFIG:
        return _error_response(
            f"未知难度 {difficulty}，可选: {list(SudokuGenerator.DIFFICULTY_CONFIG.keys())}"
        )

    generator = SudokuGenerator()
    result = generator.generate(difficulty, max_attempts=max_attempts, seed=seed)

    return jsonify(result)


@app.route("/sudoku/standards", methods=["GET"])
def sudoku_standards():
    return jsonify({
        "status": "ok",
        "standards": SudokuGenerator.get_difficulty_standards()
    })


@app.route("/sudoku/classify", methods=["POST"])
def sudoku_classify():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    board, _, err = _parse_sudoku_input(data)
    if err:
        return _error_response(err)

    generator = SudokuGenerator()
    result = generator.classify_difficulty(board)
    return jsonify({"status": "ok", "classification": result})


# ==================== 二阶魔方 ====================
@app.route("/cube2/solve", methods=["POST"])
def cube2_solve():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    state_string = data.get("state_string")
    if not state_string:
        return _error_response("缺少参数: state_string")

    max_depth = data.get("max_depth", 14)
    include_stats = data.get("include_stats", True)
    verify = data.get("verify", True)

    solver = Cube2Solver()

    try:
        moves, stats = solver.solve(state_string, include_stats=True, max_depth=max_depth)
    except ValueError as e:
        return _error_response(str(e))

    response = {"status": "ok"}
    if moves is None:
        response["result"] = "not_found"
        response["moves"] = None
        response["message"] = f"在 max_depth={max_depth} 内未找到解"
    else:
        response["result"] = "optimal"
        response["moves"] = moves
        response["move_count"] = len(moves)
        response["move_sequence"] = " ".join(moves)
        if verify:
            ok, msg = solver.verify_solution(state_string, moves)
            response["verified"] = ok
            response["verify_message"] = msg

    if include_stats:
        response["stats"] = stats

    return jsonify(response)


@app.route("/cube2/scramble", methods=["GET"])
def cube2_scramble():
    length = request.args.get("length", default=8, type=int)
    if length < 1 or length > 20:
        return _error_response("length 必须在 1~20 之间")

    solver = Cube2Solver()
    state, moves = solver.scramble(length)

    return jsonify({
        "status": "ok",
        "state_string": state,
        "scramble_moves": moves,
        "scramble_sequence": " ".join(moves),
        "length": length
    })


@app.route("/cube2/verify", methods=["POST"])
def cube2_verify():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    state_string = data.get("state_string")
    moves = data.get("moves")

    if not state_string:
        return _error_response("缺少参数: state_string")
    if not isinstance(moves, list):
        return _error_response("参数 moves 必须是操作序列数组")

    solver = Cube2Solver()
    try:
        ok, msg = solver.verify_solution(state_string, moves)
    except ValueError as e:
        return _error_response(str(e))

    return jsonify({
        "status": "ok",
        "verified": ok,
        "message": msg
    })


# ==================== 基准测试 ====================
@app.route("/benchmark", methods=["GET", "POST"])
def benchmark_run():
    bench = Benchmark()

    if request.method == "POST":
        try:
            data = request.get_json(force=True) or {}
        except Exception:
            return _error_response("无效的 JSON 请求体")
        puzzles = data.get("puzzles")
        if not isinstance(puzzles, list) or not puzzles:
            return _error_response("参数 puzzles 必须是非空数组")
        result = bench.run(puzzles)
    else:
        result = bench.run()

    return jsonify({"status": "ok", "benchmark": result})


@app.route("/benchmark/presets", methods=["GET"])
def benchmark_presets():
    return jsonify({
        "status": "ok",
        "presets": Benchmark.PRESET_PUZZLES
    })


# ==================== 三阶魔方 ====================
@app.route("/api/cube3/validate", methods=["POST"])
def cube3_validate():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    state_string = data.get("state_string")
    if not state_string:
        return _error_response("缺少参数: state_string")

    solver = get_cube3_solver()
    valid, reason = solver.validate_state(state_string)

    return jsonify({
        "status": "ok",
        "valid": valid,
        "reason": reason,
    })


@app.route("/api/cube3/solve", methods=["POST"])
def cube3_solve():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    state_string = data.get("state_string")
    if not state_string:
        return _error_response("缺少参数: state_string")

    max_depth = data.get("max_depth", 20)
    include_stats = data.get("include_stats", True)
    verify = data.get("verify", True)

    solver = get_cube3_solver()

    try:
        moves, stats = solver.solve(state_string, include_stats=True, max_depth=max_depth)
    except ValueError as e:
        return _error_response(str(e))

    response = {"status": "ok"}
    if moves is None:
        response["result"] = "not_found"
        response["moves"] = None
        response["message"] = f"在 max_depth={max_depth} 内未找到解"
    else:
        response["result"] = "optimal"
        response["moves"] = moves
        response["move_count"] = len(moves)
        response["move_sequence"] = " ".join(moves)
        if verify:
            ok, msg = solver.verify_solution(state_string, moves)
            response["verified"] = ok
            response["verify_message"] = msg

    if include_stats:
        response["stats"] = stats

    return jsonify(response)


# ==================== 解空间计数 ====================
@app.route("/api/count", methods=["POST"])
def count_solutions():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    problem_type = data.get("problem_type")
    if not problem_type:
        return _error_response("缺少参数: problem_type")

    if problem_type not in ("nqueens", "sudoku", "cube2"):
        return _error_response("problem_type 必须是 'nqueens' | 'sudoku' | 'cube2'")

    include_stats = data.get("include_stats", True)
    counter = get_counter_solver()

    try:
        if problem_type == "nqueens":
            n = data.get("n")
            if n is None:
                return _error_response("缺少参数: n")
            if not isinstance(n, int) or n < 0 or n > 16:
                return _error_response("n 必须是 0~16 的整数")

            count, stats = counter.count_nqueens(n)
            response = {
                "status": "ok",
                "problem_type": "nqueens",
                "n": n,
                "solution_count": count,
                "exact": True,
            }
            if include_stats:
                response["stats"] = stats

        elif problem_type == "sudoku":
            board, board_string, err = _parse_sudoku_input(data)
            if err:
                return _error_response(err)

            count, hit_limit, stats = counter.count_sudoku(board, limit=1000)
            response = {
                "status": "ok",
                "problem_type": "sudoku",
                "solution_count": count,
                "count_limit": 1000,
                "hit_limit": hit_limit,
                "exact": not hit_limit,
                "message": "超过 1000 解" if hit_limit else "精确计数",
            }
            if include_stats:
                response["stats"] = stats

        elif problem_type == "cube2":
            state_string = data.get("state_string")
            if not state_string:
                return _error_response("缺少参数: state_string")

            max_depth = data.get("max_depth", 14)
            count, depth, stats = counter.count_cube2_shortest_paths_bfs(
                state_string, max_depth=max_depth
            )
            response = {
                "status": "ok",
                "problem_type": "cube2",
                "shortest_path_count": count,
                "shortest_depth": depth,
                "exact": depth != -1,
            }
            if include_stats:
                response["stats"] = stats

    except ValueError as e:
        return _error_response(str(e))

    return jsonify(response)


# ==================== 通用CSP引擎 ====================
@app.route("/api/csp/examples", methods=["GET"])
def csp_examples():
    examples = CSPSolver.get_examples()
    return jsonify({
        "status": "ok",
        "examples": examples,
    })


@app.route("/api/csp/solve", methods=["POST"])
def csp_solve():
    try:
        data = request.get_json(force=True) or {}
    except Exception:
        return _error_response("无效的 JSON 请求体")

    problem = data.get("problem")
    if not problem:
        return _error_response("缺少参数: problem")

    mode = data.get("mode", "one")
    if mode not in ("one", "all"):
        return _error_response("mode 必须是 'one' | 'all'")

    solution_limit = data.get("solution_limit", 100)
    include_stats = data.get("include_stats", True)

    solver = CSPSolver()

    try:
        solutions, stats = solver.solve(
            problem, mode=mode, solution_limit=solution_limit
        )
    except ValueError as e:
        return _error_response(str(e))

    response = {
        "status": "ok",
        "mode": mode,
        "solution_count": len(solutions),
    }

    if mode == "one":
        response["solution"] = solutions[0] if solutions else None
    else:
        response["solutions"] = solutions
        if solution_limit is not None:
            response["solution_limit"] = solution_limit
            response["reached_limit"] = len(solutions) >= solution_limit

    if include_stats:
        response["stats"] = stats

    return jsonify(response)


if __name__ == "__main__":
    print("=" * 60)
    print("  CSP Solver API - 约束满足问题求解服务")
    print("  监听端口: 8021")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8021, debug=False, threaded=True)
