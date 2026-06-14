from typing import List, Optional, Dict, Any, Tuple
import random


MOVES = ["U", "U'", "U2", "D", "D'", "D2",
         "F", "F'", "F2", "B", "B'", "B2",
         "L", "L'", "L2", "R", "R'", "R2"]

SOLVED_STATE = "WWWWOOOOGGGGBBBBRRRRYYYY"


class Cube2Solver:
    """
    二阶魔方小面布局 (24 个位置):
          U (0-3)    行: 0,1 在上, 2,3 在下
         [0][1]
         [2][3]
    L(16-19)  F(4-7)  R(8-11)  B(12-15)
    [16][17] [4][5]  [8][9]   [12][13]
    [18][19] [6][7]  [10][11] [14][15]
          D (20-23)
         [20][21]
         [22][23]

    U=白(W), F=绿(G), R=红(R), B=蓝(B), L=橙(O), D=黄(Y)
    """
    FACE_COLORS = {'W': 'U', 'G': 'F', 'R': 'R', 'B': 'B', 'O': 'L', 'Y': 'D'}

    def __init__(self):
        self._build_perm_tables()
        self.reset_stats()

    def reset_stats(self):
        self.backtrack_count = 0
        self.nodes_visited = 0
        self.prune_count = 0

    def _build_perm_tables(self):
        """
        直接定义每种移动的位置循环。
        置换表 perm[move][i] = j: 新状态位置 i 的值 = 旧状态位置 j 的值
        即 new_state = [old_state[p[0]], old_state[p[1]], ..., old_state[p[23]]]
        """
        self.perm = {}

        U = [0, 1, 2, 3]
        F = [4, 5, 6, 7]
        R = [8, 9, 10, 11]
        B = [12, 13, 14, 15]
        L = [16, 17, 18, 19]
        D = [20, 21, 22, 23]

        def make_perm(face, face_cycle, ring_cycles):
            """
            face: 面的4个位置
            face_cycle: 面内4循环 (a,b,c,d) 表示 new[a]=old[d], new[b]=old[a], new[c]=old[b], new[d]=old[c] (顺时针)
            ring_cycles: 多个4循环, 每个是相邻面的边缘位置
            """
            p = list(range(24))

            a, b, c, d = face_cycle
            p[face[a]] = face[face_cycle[(a + 3) % 4]]
            p[face[b]] = face[face_cycle[(b + 3) % 4]]
            p[face[c]] = face[face_cycle[(c + 3) % 4]]
            p[face[d]] = face[face_cycle[(d + 3) % 4]]

            for ring in ring_cycles:
                for i in range(4):
                    src_idx = (i + 3) % 4
                    p[ring[i]] = ring[src_idx]
            return p

        def make_perm_ccw(face, face_cycle, ring_cycles):
            """逆时针: 和顺时针相反"""
            p = list(range(24))
            a, b, c, d = face_cycle
            p[face[a]] = face[face_cycle[(a + 1) % 4]]
            p[face[b]] = face[face_cycle[(b + 1) % 4]]
            p[face[c]] = face[face_cycle[(c + 1) % 4]]
            p[face[d]] = face[face_cycle[(d + 1) % 4]]
            for ring in ring_cycles:
                for i in range(4):
                    src_idx = (i + 1) % 4
                    p[ring[i]] = ring[src_idx]
            return p

        def make_perm_180(face, face_cycle, ring_cycles):
            """180度旋转"""
            p = list(range(24))
            for i in range(4):
                p[face[face_cycle[i]]] = face[face_cycle[(i + 2) % 4]]
            for ring in ring_cycles:
                for i in range(4):
                    p[ring[i]] = ring[(i + 2) % 4]
            return p

        FCW = (0, 1, 3, 2)  # 面顺时针4循环 (viewed from outside)

        # U: 从上方看顺时针。影响 F顶面[4,5], R顶面[8,9], B顶面[12,13], L顶面[16,17]
        # 顺时针旋转时: F顶 <- L顶 <- B顶 <- R顶 <- F顶
        # 即 new[F[0]]=old[L[0]], new[L[0]]=old[B[0]], new[B[0]]=old[R[0]], new[R[0]]=old[F[0]]
        u_ring = ([F[0], L[0], B[0], R[0]],
                  [F[1], L[1], B[1], R[1]])
        self.perm["U"] = make_perm(U, FCW, u_ring)
        self.perm["U'"] = make_perm_ccw(U, FCW, u_ring)
        self.perm["U2"] = make_perm_180(U, FCW, u_ring)

        # D: 从下方看顺时针。影响 F底面[6,7], L底面[18,19], B底面[14,15], R底面[10,11]
        # 顺时针时: F底 <- R底 <- B底 <- L底 <- F底
        d_ring = ([F[2], R[2], B[2], L[2]],
                  [F[3], R[3], B[3], L[3]])
        self.perm["D"] = make_perm(D, FCW, d_ring)
        self.perm["D'"] = make_perm_ccw(D, FCW, d_ring)
        self.perm["D2"] = make_perm_180(D, FCW, d_ring)

        # F: 从前方看顺时针。影响 U底面[2,3], R左面[9,11], D顶面[20,21], L右面[16,18]
        # 顺时针时: U底 -> L右 -> D顶 -> R左 -> U底
        # 即 new[U[2]]=old[L[2]], new[L[2]]=old[D[0]], new[D[0]]=old[R[1]], new[R[1]]=old[U[2]]
        #    new[U[3]]=old[L[0]], new[L[0]]=old[D[1]], new[D[1]]=old[R[3]], new[R[3]]=old[U[3]]
        # 注意: 这个映射是精心设计的
        f_ring = ([U[2], L[2], D[0], R[1]],
                  [U[3], L[0], D[1], R[3]])
        self.perm["F"] = make_perm(F, FCW, f_ring)
        self.perm["F'"] = make_perm_ccw(F, FCW, f_ring)
        self.perm["F2"] = make_perm_180(F, FCW, f_ring)

        # B: 从后方看顺时针。影响 U顶面[0,1], L左面[17,19], D底面[22,23], R右面[8,10]
        # 顺时针时: U顶 -> R右 -> D底 -> L左 -> U顶
        # new[U[0]]=old[R[0]], new[R[0]]=old[D[3]], new[D[3]]=old[L[1]], new[L[1]]=old[U[0]]
        # new[U[1]]=old[R[2]], new[R[2]]=old[D[2]], new[D[2]]=old[L[3]], new[L[3]]=old[U[1]]
        b_ring = ([U[0], R[0], D[3], L[1]],
                  [U[1], R[2], D[2], L[3]])
        self.perm["B"] = make_perm(B, FCW, b_ring)
        self.perm["B'"] = make_perm_ccw(B, FCW, b_ring)
        self.perm["B2"] = make_perm_180(B, FCW, b_ring)

        # L: 从左方看顺时针。影响 U左面[0,2], F左面[4,6], D左面[20,22], B右面[13,15]
        # 注意 B 的方向是反过来的
        # 顺时针时: U左 -> F左 -> D左 -> B右(反) -> U左
        # new[U[0]]=old[B[3]], new[F[0]]=old[U[0]], new[D[0]]=old[F[0]], new[B[3]]=old[D[0]]
        # new[U[2]]=old[B[1]], new[F[2]]=old[U[2]], new[D[2]]=old[F[2]], new[B[1]]=old[D[2]]
        l_ring = ([U[0], F[0], D[0], B[3]],
                  [U[2], F[2], D[2], B[1]])
        self.perm["L"] = make_perm(L, FCW, l_ring)
        self.perm["L'"] = make_perm_ccw(L, FCW, l_ring)
        self.perm["L2"] = make_perm_180(L, FCW, l_ring)

        # R: 从右方看顺时针。影响 U右面[1,3], B左面[12,14], D右面[21,23], F右面[5,7]
        # 顺时针时: U右 -> B左(反) -> D右 -> F右 -> U右
        # new[U[1]]=old[F[1]], new[B[2]]=old[U[1]], new[D[1]]=old[B[2]], new[F[1]]=old[D[1]]
        # new[U[3]]=old[F[3]], new[B[0]]=old[U[3]], new[D[3]]=old[B[0]], new[F[3]]=old[D[3]]
        r_ring = ([U[1], F[1], D[1], B[2]],
                  [U[3], F[3], D[3], B[0]])
        self.perm["R"] = make_perm(R, FCW, r_ring)
        self.perm["R'"] = make_perm_ccw(R, FCW, r_ring)
        self.perm["R2"] = make_perm_180(R, FCW, r_ring)

        # 验证所有置换表合法
        for name, p in self.perm.items():
            assert len(p) == 24, f"{name} length {len(p)}"
            assert set(p) == set(range(24)), f"{name} not permutation: {sorted(p)}"

        self.inverse_move = {
            "U": "U'", "U'": "U", "U2": "U2",
            "D": "D'", "D'": "D", "D2": "D2",
            "F": "F'", "F'": "F", "F2": "F2",
            "B": "B'", "B'": "B", "B2": "B2",
            "L": "L'", "L'": "L", "L2": "L2",
            "R": "R'", "R'": "R", "R2": "R2",
        }

        self.axis_groups = {
            "U": 0, "U'": 0, "U2": 0, "D": 0, "D'": 0, "D2": 0,
            "F": 1, "F'": 1, "F2": 1, "B": 1, "B'": 1, "B2": 1,
            "L": 2, "L'": 2, "L2": 2, "R": 2, "R'": 2, "R2": 2,
        }

    def parse_state(self, state_str: str) -> List[str]:
        state_str = state_str.strip().upper()
        if len(state_str) != 24:
            raise ValueError(f"状态字符串长度必须为24，当前为{len(state_str)}")
        valid = set("WGRBOY")
        for i, ch in enumerate(state_str):
            if ch not in valid:
                raise ValueError(f"位置{i}字符非法: {ch}")
        for color in valid:
            if state_str.count(color) != 4:
                raise ValueError(f"每种颜色必须恰好出现4次，{color}出现了{state_str.count(color)}次")
        return list(state_str)

    def apply_move(self, state_list: List[str], move: str) -> List[str]:
        p = self.perm[move]
        return [state_list[p[i]] for i in range(24)]

    def _heuristic(self, state_list: List[str]) -> int:
        """每个面不同颜色计数 / 4，作为下界启发式"""
        faces = [
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [8, 9, 10, 11],
            [12, 13, 14, 15],
            [16, 17, 18, 19],
            [20, 21, 22, 23],
        ]
        total_wrong = 0
        for face in faces:
            target = state_list[face[0]]
            for idx in face:
                if state_list[idx] != target:
                    total_wrong += 1
        return (total_wrong + 7) // 8

    def solve(self, state_str: str, include_stats: bool = False,
              max_depth: int = 14) -> Tuple[Optional[List[str]], Dict[str, Any]]:
        self.reset_stats()
        start = self.parse_state(state_str)
        solved = list(SOLVED_STATE)

        if start == solved:
            stats = {**self._get_stats(), "depth": 0, "status": "optimal"}
            return ([], stats) if include_stats else []

        for depth in range(1, max_depth + 1):
            result = self._ida_star(start, solved, depth, 0, [], None)
            if result is not None:
                stats = {**self._get_stats(), "depth": len(result), "status": "optimal"}
                return (result, stats) if include_stats else result

        stats = {**self._get_stats(), "depth": -1, "status": "not_found"}
        return (None, stats) if include_stats else None

    def _ida_star(self, state: List[str], solved: List[str], max_depth: int,
                  current_depth: int, path: List[str], last_axis: Optional[int]) -> Optional[List[str]]:
        self.nodes_visited += 1

        h = self._heuristic(state)
        if current_depth + h > max_depth:
            self.prune_count += 1
            return None

        if state == solved:
            return path[:]

        if current_depth >= max_depth:
            return None

        for move in MOVES:
            axis = self.axis_groups[move]
            if axis == last_axis:
                continue
            if path and self.inverse_move.get(move) == path[-1]:
                continue

            new_state = self.apply_move(state, move)
            path.append(move)
            result = self._ida_star(new_state, solved, max_depth,
                                    current_depth + 1, path, axis)
            if result is not None:
                return result
            path.pop()
            self.backtrack_count += 1

        return None

    def scramble(self, length: int = 8) -> Tuple[str, List[str]]:
        state = list(SOLVED_STATE)
        moves = []
        last_axis = None
        rng = random.Random()
        for _ in range(length):
            candidates = [m for m in MOVES if self.axis_groups[m] != last_axis
                          and (not moves or self.inverse_move.get(m) != moves[-1])]
            move = rng.choice(candidates)
            moves.append(move)
            state = self.apply_move(state, move)
            last_axis = self.axis_groups[move]
        return "".join(state), moves

    def verify_solution(self, state_str: str, moves: List[str]) -> Tuple[bool, str]:
        try:
            state = self.parse_state(state_str)
        except ValueError as e:
            return False, str(e)
        for move in moves:
            if move not in self.perm:
                return False, f"非法操作: {move}"
            state = self.apply_move(state, move)
        if state == list(SOLVED_STATE):
            return True, "已还原"
        return False, "未还原，最终状态: " + "".join(state)

    def _get_stats(self) -> Dict[str, int]:
        return {
            "backtrack_count": self.backtrack_count,
            "prune_count": self.prune_count,
            "nodes_visited": self.nodes_visited
        }
