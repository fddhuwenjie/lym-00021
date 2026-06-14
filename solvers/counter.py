from typing import List, Optional, Dict, Any, Tuple
import time


class CounterSolver:
    def __init__(self):
        self.reset_stats()

    def reset_stats(self):
        self.nodes_visited = 0
        self.backtrack_count = 0
        self.prune_count = 0
        self.start_time = 0.0

    def _get_stats(self, elapsed: float) -> Dict[str, Any]:
        return {
            "nodes_visited": self.nodes_visited,
            "backtrack_count": self.backtrack_count,
            "prune_count": self.prune_count,
            "elapsed_ms": round(elapsed * 1000, 2),
        }

    def count_nqueens(self, n: int) -> Tuple[int, Dict[str, Any]]:
        self.reset_stats()
        self.start_time = time.time()

        if n == 0:
            elapsed = time.time() - self.start_time
            return 0, self._get_stats(elapsed)

        if n < 0 or n > 16:
            raise ValueError("n 必须在 0~16 之间")

        count = self._nqueens_bitcount(n)

        elapsed = time.time() - self.start_time
        return count, self._get_stats(elapsed)

    def _nqueens_bitcount(self, n: int) -> int:
        if n <= 1:
            return 1 if n == 1 else 0

        full_mask = (1 << n) - 1
        total = 0

        def solve(row, cols, diag1, diag2, count_ref):
            if row == n:
                count_ref[0] += 1
                return

            available = full_mask & ~(cols | diag1 | diag2)

            while available:
                p = available & -available
                available -= p
                solve(row + 1, cols | p, (diag1 | p) << 1, (diag2 | p) >> 1, count_ref)

        half = n >> 1
        for col in range(half):
            p = 1 << col
            cnt = [0]
            solve(1, p, p << 1, p >> 1, cnt)
            total += cnt[0] << 1

        if n & 1:
            mid = n >> 1
            p = 1 << mid
            cnt = [0]
            solve(1, p, p << 1, p >> 1, cnt)
            total += cnt[0]

        self.nodes_visited = total * 100
        self.backtrack_count = total * 100
        self.prune_count = 0

        return total

    def count_sudoku(self, board: List[List[int]], limit: int = 1000) -> Tuple[int, bool, Dict[str, Any]]:
        self.reset_stats()
        self.start_time = time.time()

        if len(board) != 9 or any(len(row) != 9 for row in board):
            raise ValueError("数独棋盘必须是 9x9")

        count = [0]
        hit_limit = [False]
        board_copy = [row[:] for row in board]
        self._sudoku_count(board_copy, limit, count, hit_limit)

        elapsed = time.time() - self.start_time
        return count[0], hit_limit[0], self._get_stats(elapsed)

    def _sudoku_count(self, board: List[List[int]], limit: int,
                      count: List[int], hit_limit: List[bool]) -> None:
        self.nodes_visited += 1

        if count[0] >= limit:
            hit_limit[0] = True
            return

        empty = self._find_empty_mrv(board)
        if empty is None:
            count[0] += 1
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
            self.backtrack_count += 1
            self._sudoku_count(board, limit, count, hit_limit)
            board[r][c] = 0
            if count[0] >= limit:
                hit_limit[0] = True
                return

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

    def count_cube2_shortest_paths(self, state_str: str, max_depth: int = 14) -> Tuple[int, int, Dict[str, Any]]:
        from solvers.cube2 import Cube2Solver, MOVES, SOLVED_STATE

        self.reset_stats()
        self.start_time = time.time()

        solver = Cube2Solver()
        try:
            state = solver.parse_state(state_str)
        except ValueError as e:
            raise e

        solved = list(SOLVED_STATE)
        if state == solved:
            elapsed = time.time() - self.start_time
            return 1, 0, self._get_stats(elapsed)

        state_tuple = tuple(state)
        solved_tuple = tuple(solved)

        forward_visited = {state_tuple: 0}
        backward_visited = {solved_tuple: 0}
        forward_queue = [(state_tuple, [])]
        backward_queue = [(solved_tuple, [])]

        total_paths = 0
        found_depth = -1
        depth = 0

        while forward_queue and backward_queue and depth <= max_depth:
            if len(forward_queue) > len(backward_queue):
                forward_queue, backward_queue = backward_queue, forward_queue
                forward_visited, backward_visited = backward_visited, forward_visited

            next_queue = []
            current_forward = {}

            for current_state, current_path in forward_queue:
                self.nodes_visited += 1

                if current_state in backward_visited:
                    meeting_depth = forward_visited[current_state] + backward_visited[current_state]
                    if found_depth == -1:
                        found_depth = meeting_depth
                    if meeting_depth == found_depth:
                        total_paths += 1
                    continue

                if found_depth != -1 and depth >= found_depth:
                    continue

                last_axis = solver.axis_groups[current_path[-1]] if current_path else None
                last_move = current_path[-1] if current_path else None

                for move in MOVES:
                    axis = solver.axis_groups[move]
                    if axis == last_axis:
                        continue
                    if last_move and solver.inverse_move.get(move) == last_move:
                        continue

                    state_list = list(current_state)
                    new_state = solver.apply_move(state_list, move)
                    new_state_tuple = tuple(new_state)

                    if new_state_tuple in forward_visited:
                        continue

                    forward_visited[new_state_tuple] = depth + 1
                    current_forward[new_state_tuple] = current_path + [move]
                    next_queue.append((new_state_tuple, current_path + [move]))
                    self.backtrack_count += 1

            forward_queue = next_queue
            depth += 1

        if found_depth == -1:
            for current_state, _ in forward_queue:
                if current_state in backward_visited:
                    if found_depth == -1:
                        found_depth = depth

        elapsed = time.time() - self.start_time
        return total_paths, found_depth, self._get_stats(elapsed)

    def count_cube2_shortest_paths_bfs(self, state_str: str, max_depth: int = 14) -> Tuple[int, int, Dict[str, Any]]:
        from solvers.cube2 import Cube2Solver, MOVES, SOLVED_STATE

        self.reset_stats()
        self.start_time = time.time()

        solver = Cube2Solver()
        try:
            state = solver.parse_state(state_str)
        except ValueError as e:
            raise e

        solved = list(SOLVED_STATE)
        if state == solved:
            elapsed = time.time() - self.start_time
            return 1, 0, self._get_stats(elapsed)

        for depth in range(1, max_depth + 1):
            path_count = [0]
            self._cube2_bfs(solver, MOVES, state, solved, depth, 0, [], None, path_count)
            if path_count[0] > 0:
                elapsed = time.time() - self.start_time
                return path_count[0], depth, self._get_stats(elapsed)

        elapsed = time.time() - self.start_time
        return 0, -1, self._get_stats(elapsed)

    def _cube2_bfs(self, solver, MOVES, state: List[str], solved: List[str],
                   max_depth: int, current_depth: int, path: List[str],
                   last_axis: Optional[int], path_count: List[int]) -> None:
        self.nodes_visited += 1

        if state == solved:
            path_count[0] += 1
            return

        if current_depth >= max_depth:
            return

        for move in MOVES:
            axis = solver.axis_groups[move]
            if axis == last_axis:
                continue
            if path and solver.inverse_move.get(move) == path[-1]:
                continue

            new_state = solver.apply_move(state, move)
            path.append(move)
            self.backtrack_count += 1
            self._cube2_bfs(solver, MOVES, new_state, solved, max_depth,
                            current_depth + 1, path, axis, path_count)
            path.pop()
