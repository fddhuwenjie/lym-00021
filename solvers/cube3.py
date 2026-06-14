from typing import List, Optional, Dict, Any, Tuple
import os
import pickle
import time
from collections import deque


CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cube3_cache")
os.makedirs(CACHE_DIR, exist_ok=True)


FACES = ['U', 'R', 'F', 'D', 'L', 'B']
FACE_ORDER = {'U': 0, 'R': 1, 'F': 2, 'D': 3, 'L': 4, 'B': 5}
COLORS = set('URFDLB')


FACE_LETTER_TO_COLOR = {
    'U': 'U', 'R': 'R', 'F': 'F', 'D': 'D', 'L': 'L', 'B': 'B'
}


CORNER_NAMES = [
    'URF', 'UFL', 'ULB', 'UBR',
    'DFR', 'DLF', 'DBL', 'DRB'
]

CORNER_POSITIONS = {
    'URF': (0, 8, 20),
    'UFL': (2, 11, 29),
    'ULB': (6, 15, 38),
    'UBR': (8, 18, 47),
    'DFR': (18, 20, 26),
    'DLF': (20, 29, 24),
    'DBL': (24, 38, 35),
    'DRB': (26, 47, 35),
}

CORNER_FACELETS = {
    'URF': [(0, 'U'), (2, 'R'), (2, 'F')],
    'UFL': [(0, 'U'), (2, 'F'), (0, 'L')],
    'ULB': [(0, 'U'), (2, 'L'), (0, 'B')],
    'UBR': [(0, 'U'), (2, 'B'), (0, 'R')],
    'DFR': [(2, 'D'), (0, 'F'), (2, 'R')],
    'DLF': [(2, 'D'), (0, 'L'), (2, 'F')],
    'DBL': [(2, 'D'), (0, 'B'), (2, 'L')],
    'DRB': [(2, 'D'), (0, 'R'), (2, 'B')],
}


EDGE_NAMES = [
    'UR', 'UF', 'UL', 'UB',
    'DR', 'DF', 'DL', 'DB',
    'FR', 'FL', 'BL', 'BR'
]

EDGE_POSITIONS = {
    'UR': (1, 5, None),
    'UF': (1, 1, None),
    'UL': (1, 3, None),
    'UB': (1, 7, None),
    'DR': (19, 5, None),
    'DF': (19, 1, None),
    'DL': (19, 3, None),
    'DB': (19, 7, None),
    'FR': (23, 5, None),
    'FL': (23, 3, None),
    'BL': (41, 3, None),
    'BR': (41, 5, None),
}

EDGE_FACELETS = {
    'UR': [(1, 'U'), (1, 'R')],
    'UF': [(1, 'U'), (1, 'F')],
    'UL': [(1, 'U'), (1, 'L')],
    'UB': [(1, 'U'), (1, 'B')],
    'DR': [(1, 'D'), (1, 'R')],
    'DF': [(1, 'D'), (1, 'F')],
    'DL': [(1, 'D'), (1, 'L')],
    'DB': [(1, 'D'), (1, 'B')],
    'FR': [(1, 'F'), (1, 'R')],
    'FL': [(1, 'F'), (1, 'L')],
    'BL': [(1, 'B'), (1, 'L')],
    'BR': [(1, 'B'), (1, 'R')],
}


SLICE_EDGES = [8, 9, 10, 11]


def facelet_index(face: str, row: int, col: int) -> int:
    face_idx = FACE_ORDER[face]
    return face_idx * 9 + row * 3 + col


def _build_corner_facelet_map():
    return [
        [facelet_index('U', 0, 2), facelet_index('R', 0, 0), facelet_index('F', 0, 2)],
        [facelet_index('U', 0, 0), facelet_index('F', 0, 0), facelet_index('L', 0, 2)],
        [facelet_index('U', 2, 0), facelet_index('L', 0, 0), facelet_index('B', 0, 2)],
        [facelet_index('U', 2, 2), facelet_index('B', 0, 0), facelet_index('R', 0, 2)],
        [facelet_index('D', 2, 2), facelet_index('F', 2, 2), facelet_index('R', 2, 0)],
        [facelet_index('D', 2, 0), facelet_index('L', 2, 2), facelet_index('F', 2, 0)],
        [facelet_index('D', 0, 0), facelet_index('B', 2, 2), facelet_index('L', 2, 0)],
        [facelet_index('D', 0, 2), facelet_index('R', 2, 2), facelet_index('B', 2, 0)],
    ]


CORNER_FACELET_MAP = _build_corner_facelet_map()


def _build_edge_facelet_map():
    return [
        [facelet_index('U', 0, 1), facelet_index('R', 0, 1)],
        [facelet_index('U', 1, 0), facelet_index('F', 0, 1)],
        [facelet_index('U', 2, 1), facelet_index('L', 0, 1)],
        [facelet_index('U', 1, 2), facelet_index('B', 0, 1)],
        [facelet_index('D', 2, 1), facelet_index('R', 2, 1)],
        [facelet_index('D', 1, 0), facelet_index('F', 2, 1)],
        [facelet_index('D', 0, 1), facelet_index('L', 2, 1)],
        [facelet_index('D', 1, 2), facelet_index('B', 2, 1)],
        [facelet_index('F', 1, 2), facelet_index('R', 1, 0)],
        [facelet_index('F', 1, 0), facelet_index('L', 1, 2)],
        [facelet_index('B', 1, 2), facelet_index('L', 1, 0)],
        [facelet_index('B', 1, 0), facelet_index('R', 1, 2)],
    ]


EDGE_FACELET_MAP = _build_edge_facelet_map()


MOVES_PHASE1 = ["U", "U'", "U2", "D", "D'", "D2",
                "F", "F'", "F2", "B", "B'", "B2",
                "L", "L'", "L2", "R", "R'", "R2"]

MOVES_PHASE2 = ["U", "U2", "D", "D2", "F2", "B2", "L2", "R2"]


MOVE_AXIS = {
    "U": 0, "U'": 0, "U2": 0,
    "D": 0, "D'": 0, "D2": 0,
    "F": 1, "F'": 1, "F2": 1,
    "B": 1, "B'": 1, "B2": 1,
    "L": 2, "L'": 2, "L2": 2,
    "R": 2, "R'": 2, "R2": 2,
}

INVERSE_MOVE = {
    "U": "U'", "U'": "U", "U2": "U2",
    "D": "D'", "D'": "D", "D2": "D2",
    "F": "F'", "F'": "F", "F2": "F2",
    "B": "B'", "B'": "B", "B2": "B2",
    "L": "L'", "L'": "L", "L2": "L2",
    "R": "R'", "R'": "R", "R2": "R2",
}


def _build_face_perm_tables():
    def rotate_face_cw(face_start):
        p = list(range(54))
        p[face_start + 0] = face_start + 6
        p[face_start + 1] = face_start + 3
        p[face_start + 2] = face_start + 0
        p[face_start + 3] = face_start + 7
        p[face_start + 5] = face_start + 1
        p[face_start + 6] = face_start + 8
        p[face_start + 7] = face_start + 5
        p[face_start + 8] = face_start + 2
        return p

    def rotate_face_ccw(face_start):
        p = list(range(54))
        p[face_start + 0] = face_start + 2
        p[face_start + 1] = face_start + 5
        p[face_start + 2] = face_start + 8
        p[face_start + 3] = face_start + 1
        p[face_start + 5] = face_start + 7
        p[face_start + 6] = face_start + 0
        p[face_start + 7] = face_start + 3
        p[face_start + 8] = face_start + 6
        return p

    def rotate_face_180(face_start):
        p = list(range(54))
        p[face_start + 0], p[face_start + 8] = face_start + 8, face_start + 0
        p[face_start + 1], p[face_start + 7] = face_start + 7, face_start + 1
        p[face_start + 2], p[face_start + 6] = face_start + 6, face_start + 2
        p[face_start + 3], p[face_start + 5] = face_start + 5, face_start + 3
        return p

    perm = {}

    u = facelet_index('U', 0, 0)
    r = facelet_index('R', 0, 0)
    f = facelet_index('F', 0, 0)
    d = facelet_index('D', 0, 0)
    l = facelet_index('L', 0, 0)
    b = facelet_index('B', 0, 0)

    U_cw = rotate_face_cw(u)
    ring = [facelet_index('F', 0, i) for i in range(3)] + \
           [facelet_index('R', 0, i) for i in range(3)] + \
           [facelet_index('B', 0, i) for i in range(3)] + \
           [facelet_index('L', 0, i) for i in range(3)]
    for i in range(3):
        U_cw[facelet_index('F', 0, i)] = facelet_index('R', 0, i)
        U_cw[facelet_index('R', 0, i)] = facelet_index('B', 0, i)
        U_cw[facelet_index('B', 0, i)] = facelet_index('L', 0, i)
        U_cw[facelet_index('L', 0, i)] = facelet_index('F', 0, i)
    perm['U'] = U_cw

    U_ccw = rotate_face_ccw(u)
    for i in range(3):
        U_ccw[facelet_index('F', 0, i)] = facelet_index('L', 0, i)
        U_ccw[facelet_index('L', 0, i)] = facelet_index('B', 0, i)
        U_ccw[facelet_index('B', 0, i)] = facelet_index('R', 0, i)
        U_ccw[facelet_index('R', 0, i)] = facelet_index('F', 0, i)
    perm["U'"] = U_ccw

    U_180 = rotate_face_180(u)
    for i in range(3):
        U_180[facelet_index('F', 0, i)], U_180[facelet_index('B', 0, i)] = \
            facelet_index('B', 0, i), facelet_index('F', 0, i)
        U_180[facelet_index('R', 0, i)], U_180[facelet_index('L', 0, i)] = \
            facelet_index('L', 0, i), facelet_index('R', 0, i)
    perm["U2"] = U_180

    D_cw = rotate_face_cw(d)
    for i in range(3):
        D_cw[facelet_index('F', 2, i)] = facelet_index('L', 2, i)
        D_cw[facelet_index('L', 2, i)] = facelet_index('B', 2, i)
        D_cw[facelet_index('B', 2, i)] = facelet_index('R', 2, i)
        D_cw[facelet_index('R', 2, i)] = facelet_index('F', 2, i)
    perm["D"] = D_cw

    D_ccw = rotate_face_ccw(d)
    for i in range(3):
        D_ccw[facelet_index('F', 2, i)] = facelet_index('R', 2, i)
        D_ccw[facelet_index('R', 2, i)] = facelet_index('B', 2, i)
        D_ccw[facelet_index('B', 2, i)] = facelet_index('L', 2, i)
        D_ccw[facelet_index('L', 2, i)] = facelet_index('F', 2, i)
    perm["D'"] = D_ccw

    D_180 = rotate_face_180(d)
    for i in range(3):
        D_180[facelet_index('F', 2, i)], D_180[facelet_index('B', 2, i)] = \
            facelet_index('B', 2, i), facelet_index('F', 2, i)
        D_180[facelet_index('R', 2, i)], D_180[facelet_index('L', 2, i)] = \
            facelet_index('L', 2, i), facelet_index('R', 2, i)
    perm["D2"] = D_180

    F_cw = rotate_face_cw(f)
    for i in range(3):
        F_cw[facelet_index('U', 2, i)] = facelet_index('L', 2 - i, 2)
        F_cw[facelet_index('R', i, 0)] = facelet_index('U', 2, i)
        F_cw[facelet_index('D', 0, 2 - i)] = facelet_index('R', i, 0)
        F_cw[facelet_index('L', i, 2)] = facelet_index('D', 0, 2 - i)
    perm["F"] = F_cw

    F_ccw = rotate_face_ccw(f)
    for i in range(3):
        F_ccw[facelet_index('U', 2, i)] = facelet_index('R', i, 0)
        F_ccw[facelet_index('R', i, 0)] = facelet_index('D', 0, 2 - i)
        F_ccw[facelet_index('D', 0, 2 - i)] = facelet_index('L', i, 2)
        F_ccw[facelet_index('L', i, 2)] = facelet_index('U', 2, i)
    perm["F'"] = F_ccw

    F_180 = rotate_face_180(f)
    for i in range(3):
        F_180[facelet_index('U', 2, i)], F_180[facelet_index('D', 0, 2 - i)] = \
            facelet_index('D', 0, 2 - i), facelet_index('U', 2, i)
        F_180[facelet_index('R', i, 0)], F_180[facelet_index('L', i, 2)] = \
            facelet_index('L', i, 2), facelet_index('R', i, 0)
    perm["F2"] = F_180

    B_cw = rotate_face_cw(b)
    for i in range(3):
        B_cw[facelet_index('U', 0, 2 - i)] = facelet_index('R', i, 2)
        B_cw[facelet_index('L', i, 0)] = facelet_index('U', 0, 2 - i)
        B_cw[facelet_index('D', 2, i)] = facelet_index('L', i, 0)
        B_cw[facelet_index('R', i, 2)] = facelet_index('D', 2, i)
    perm["B"] = B_cw

    B_ccw = rotate_face_ccw(b)
    for i in range(3):
        B_ccw[facelet_index('U', 0, 2 - i)] = facelet_index('L', i, 0)
        B_ccw[facelet_index('L', i, 0)] = facelet_index('D', 2, i)
        B_ccw[facelet_index('D', 2, i)] = facelet_index('R', i, 2)
        B_ccw[facelet_index('R', i, 2)] = facelet_index('U', 0, 2 - i)
    perm["B'"] = B_ccw

    B_180 = rotate_face_180(b)
    for i in range(3):
        B_180[facelet_index('U', 0, 2 - i)], B_180[facelet_index('D', 2, i)] = \
            facelet_index('D', 2, i), facelet_index('U', 0, 2 - i)
        B_180[facelet_index('L', i, 0)], B_180[facelet_index('R', i, 2)] = \
            facelet_index('R', i, 2), facelet_index('L', i, 0)
    perm["B2"] = B_180

    R_cw = rotate_face_cw(r)
    for i in range(3):
        R_cw[facelet_index('U', i, 2)] = facelet_index('F', i, 2)
        R_cw[facelet_index('B', 2 - i, 0)] = facelet_index('U', i, 2)
        R_cw[facelet_index('D', i, 2)] = facelet_index('B', 2 - i, 0)
        R_cw[facelet_index('F', i, 2)] = facelet_index('D', i, 2)
    perm["R"] = R_cw

    R_ccw = rotate_face_ccw(r)
    for i in range(3):
        R_ccw[facelet_index('U', i, 2)] = facelet_index('B', 2 - i, 0)
        R_ccw[facelet_index('B', 2 - i, 0)] = facelet_index('D', i, 2)
        R_ccw[facelet_index('D', i, 2)] = facelet_index('F', i, 2)
        R_ccw[facelet_index('F', i, 2)] = facelet_index('U', i, 2)
    perm["R'"] = R_ccw

    R_180 = rotate_face_180(r)
    for i in range(3):
        R_180[facelet_index('U', i, 2)], R_180[facelet_index('D', i, 2)] = \
            facelet_index('D', i, 2), facelet_index('U', i, 2)
        R_180[facelet_index('F', i, 2)], R_180[facelet_index('B', 2 - i, 0)] = \
            facelet_index('B', 2 - i, 0), facelet_index('F', i, 2)
    perm["R2"] = R_180

    L_cw = rotate_face_cw(l)
    for i in range(3):
        L_cw[facelet_index('U', i, 0)] = facelet_index('B', 2 - i, 2)
        L_cw[facelet_index('F', i, 0)] = facelet_index('U', i, 0)
        L_cw[facelet_index('D', i, 0)] = facelet_index('F', i, 0)
        L_cw[facelet_index('B', 2 - i, 2)] = facelet_index('D', i, 0)
    perm["L"] = L_cw

    L_ccw = rotate_face_ccw(l)
    for i in range(3):
        L_ccw[facelet_index('U', i, 0)] = facelet_index('F', i, 0)
        L_ccw[facelet_index('F', i, 0)] = facelet_index('D', i, 0)
        L_ccw[facelet_index('D', i, 0)] = facelet_index('B', 2 - i, 2)
        L_ccw[facelet_index('B', 2 - i, 2)] = facelet_index('U', i, 0)
    perm["L'"] = L_ccw

    L_180 = rotate_face_180(l)
    for i in range(3):
        L_180[facelet_index('U', i, 0)], L_180[facelet_index('D', i, 0)] = \
            facelet_index('D', i, 0), facelet_index('U', i, 0)
        L_180[facelet_index('F', i, 0)], L_180[facelet_index('B', 2 - i, 2)] = \
            facelet_index('B', 2 - i, 2), facelet_index('F', i, 0)
    perm["L2"] = L_180

    for name, p in perm.items():
        assert len(p) == 54
        assert set(p) == set(range(54)), f"{name} not permutation"

    return perm


FACE_PERM = _build_face_perm_tables()


def apply_move(state: List[str], move: str) -> List[str]:
    p = FACE_PERM[move]
    return [state[p[i]] for i in range(54)]


def get_corners_and_edges(state: List[str]) -> Tuple[List[int], List[int], List[int], List[int]]:
    corner_perm = [0] * 8
    corner_ori = [0] * 8
    edge_perm = [0] * 12
    edge_ori = [0] * 12

    for ci in range(8):
        fl = CORNER_FACELET_MAP[ci]
        colors = [state[i] for i in fl]
        ref_color = None
        for i, c in enumerate(colors):
            if c in ('U', 'D'):
                ref_color = c
                ori = i
                break
        if ref_color is None:
            for i, c in enumerate(colors):
                if c in ('F', 'B'):
                    ref_color = c
                    ori = i
                    break
        if ref_color is None:
            ori = 0
            ref_color = colors[0]

        corner_ori[ci] = ori % 3

        name = None
        for ni, nm in enumerate(CORNER_NAMES):
            fl2 = CORNER_FACELET_MAP[ni]
            target_colors = {FACE_LETTER_TO_COLOR['U'], FACE_LETTER_TO_COLOR['R'], FACE_LETTER_TO_COLOR['F']}
            if ni == 0:
                target_colors = {'U', 'R', 'F'}
            elif ni == 1:
                target_colors = {'U', 'F', 'L'}
            elif ni == 2:
                target_colors = {'U', 'L', 'B'}
            elif ni == 3:
                target_colors = {'U', 'B', 'R'}
            elif ni == 4:
                target_colors = {'D', 'F', 'R'}
            elif ni == 5:
                target_colors = {'D', 'L', 'F'}
            elif ni == 6:
                target_colors = {'D', 'B', 'L'}
            elif ni == 7:
                target_colors = {'D', 'R', 'B'}
            if set(colors) == target_colors:
                name = ni
                break
        corner_perm[ci] = name if name is not None else ci

    for ei in range(12):
        fl = EDGE_FACELET_MAP[ei]
        colors = [state[i] for i in fl]
        edge_ori[ei] = 0
        if colors[0] not in ('U', 'D') and colors[1] not in ('U', 'D'):
            if colors[0] in ('F', 'B'):
                edge_ori[ei] = 0
            else:
                edge_ori[ei] = 1
        else:
            if colors[0] in ('F', 'B', 'L', 'R'):
                edge_ori[ei] = 1

        name = None
        for ni, nm in enumerate(EDGE_NAMES):
            target_colors = {
                0: {'U', 'R'}, 1: {'U', 'F'}, 2: {'U', 'L'}, 3: {'U', 'B'},
                4: {'D', 'R'}, 5: {'D', 'F'}, 6: {'D', 'L'}, 7: {'D', 'B'},
                8: {'F', 'R'}, 9: {'F', 'L'}, 10: {'B', 'L'}, 11: {'B', 'R'},
            }[ni]
            if set(colors) == target_colors:
                name = ni
                break
        edge_perm[ei] = name if name is not None else ei

    return corner_perm, corner_ori, edge_perm, edge_ori


def get_twist(corner_ori: List[int]) -> int:
    twist = 0
    for i in range(7):
        twist = twist * 3 + corner_ori[i]
    return twist


def get_flip(edge_ori: List[int]) -> int:
    flip = 0
    for i in range(11):
        flip = flip * 2 + edge_ori[i]
    return flip


def get_slice_sorted(edge_perm: List[int]) -> int:
    slice_positions = sorted([i for i in range(12) if edge_perm[i] in SLICE_EDGES])
    n = 0
    k = 4
    for i, pos in enumerate(slice_positions):
        n += comb(pos, k - i)
    return n


def comb(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    result = 1
    for i in range(1, k + 1):
        result = result * (n - k + i) // i
    return result


def get_corner_perm_coord(cp: List[int]) -> int:
    perm = cp[:]
    n = 0
    for i in range(8):
        n *= 8 - i
        for j in range(i + 1, 8):
            if perm[j] < perm[i]:
                n += 1
        for j in range(i + 1, 8):
            if perm[j] > perm[i]:
                perm[j] -= 1
    return n


def get_ud_edge_perm_coord(ep: List[int]) -> int:
    ud_edges = [ep[i] for i in range(12) if ep[i] < 8]
    perm = ud_edges[:]
    n = 0
    for i in range(8):
        n *= 8 - i
        for j in range(i + 1, 8):
            if perm[j] < perm[i]:
                n += 1
        for j in range(i + 1, 8):
            if perm[j] > perm[i]:
                perm[j] -= 1
    return n


def get_slice_perm_coord(ep: List[int]) -> int:
    slice_edges = [ep[i] - 8 for i in range(12) if ep[i] >= 8]
    perm = slice_edges[:]
    n = 0
    for i in range(4):
        n *= 4 - i
        for j in range(i + 1, 4):
            if perm[j] < perm[i]:
                n += 1
        for j in range(i + 1, 4):
            if perm[j] > perm[i]:
                perm[j] -= 1
    return n


def _build_move_tables():
    twist_move = [[0] * len(MOVES_PHASE1) for _ in range(2187)]
    flip_move = [[0] * len(MOVES_PHASE1) for _ in range(2048)]
    slice_move = [[0] * len(MOVES_PHASE1) for _ in range(495)]

    solved = list('U' * 9 + 'R' * 9 + 'F' * 9 + 'D' * 9 + 'L' * 9 + 'B' * 9)
    cp_co, co_oo, ep_eo, eo_oo = get_corners_and_edges(solved)

    state_map = {}
    for twist in range(2187):
        corner_ori = [0] * 8
        t = twist
        for i in range(6, -1, -1):
            corner_ori[i] = t % 3
            t //= 3
        corner_ori[7] = (-sum(corner_ori[:7])) % 3
        for flip in range(2048):
            edge_ori = [0] * 12
            f = flip
            for i in range(10, -1, -1):
                edge_ori[i] = f % 2
                f //= 2
            edge_ori[11] = sum(edge_ori[:11]) % 2
            for mi, move in enumerate(MOVES_PHASE1):
                new_state = apply_move(solved, move)
                ncp, nco, nep, neo = get_corners_and_edges(new_state)
                nt = get_twist(nco)
                nf = get_flip(neo)
                ns = get_slice_sorted(nep)
                twist_move[twist][mi] = nt
                flip_move[flip][mi] = nf
                slice_move[0][mi] = ns

    for slice_val in range(495):
        edge_perm = _slice_to_perm(slice_val)
        for mi, move in enumerate(MOVES_PHASE1):
            new_ep = [0] * 12
            p = FACE_PERM[move]
            positions_map = {}
            for ei in range(12):
                fl = EDGE_FACELET_MAP[ei]
                new_fl = [p[x] for x in fl]
                for new_ei in range(12):
                    if set(EDGE_FACELET_MAP[new_ei]) == set(new_fl):
                        new_ep[new_ei] = edge_perm[ei]
                        break
            new_slice = get_slice_sorted(new_ep)
            slice_move[slice_val][mi] = new_slice

    return twist_move, flip_move, slice_move


def _slice_to_perm(slice_val: int) -> List[int]:
    edge_perm = [0] * 12
    remaining = set(range(12))
    s = slice_val
    positions = []
    k = 4
    for i in range(4):
        for pos in range(k - i - 1, 12):
            c = comb(pos, k - i - 1)
            if s < c:
                positions.append(pos)
                remaining.discard(pos)
                break
            s -= c
    for i, pos in enumerate(sorted(positions)):
        edge_perm[pos] = SLICE_EDGES[i]
    ud_remaining = [x for x in sorted(remaining) if x < 8]
    for i, pos in enumerate([x for x in range(12) if edge_perm[x] == 0 and x not in positions]):
        if i < len(ud_remaining):
            edge_perm[pos] = ud_remaining[i]
    return edge_perm


def _build_phase2_move_tables():
    cperm_move = [[0] * len(MOVES_PHASE2) for _ in range(40320)]
    eperm_move = [[0] * len(MOVES_PHASE2) for _ in range(40320)]
    sperm_move = [[0] * len(MOVES_PHASE2) for _ in range(24)]

    return cperm_move, eperm_move, sperm_move


def _bfs_pruning_table(size: int, move_table: List[List[int]],
                       target_state: int, moves_subset: List[int]) -> List[int]:
    table = [-1] * size
    table[target_state] = 0
    q = deque([target_state])

    while q:
        state = q.popleft()
        depth = table[state]
        for mi in moves_subset:
            new_state = move_table[state][mi]
            if table[new_state] == -1:
                table[new_state] = depth + 1
                q.append(new_state)

    return table


class Cube3Solver:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if Cube3Solver._initialized:
            return
        Cube3Solver._initialized = True
        self.reset_stats()
        self._load_or_build_tables()

    def reset_stats(self):
        self.nodes_visited = 0
        self.backtrack_count = 0
        self.prune_count = 0
        self.phase1_nodes = 0
        self.phase2_nodes = 0

    def _load_or_build_tables(self):
        cache_file = os.path.join(CACHE_DIR, "cube3_tables.pkl")
        if os.path.exists(cache_file):
            print("[Cube3] 加载缓存的剪枝表...")
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            self.twist_move = data['twist_move']
            self.flip_move = data['flip_move']
            self.slice_move = data['slice_move']
            self.phase1_prune = data['phase1_prune']
            self.cperm_move = data['cperm_move']
            self.eperm_move = data['eperm_move']
            self.sperm_move = data['sperm_move']
            self.phase2_cperm_prune = data['phase2_cperm_prune']
            self.phase2_eperm_prune = data['phase2_eperm_prune']
            self.phase2_sperm_prune = data['phase2_sperm_prune']
            print("[Cube3] 缓存加载完成")
            return

        print("[Cube3] 首次启动，构建剪枝表（这可能需要几分钟）...")
        start = time.time()

        self.twist_move, self.flip_move, self.slice_move = _build_move_tables()
        self.cperm_move, self.eperm_move, self.sperm_move = _build_phase2_move_tables()

        print("[Cube3] 构建 Phase 1 剪枝表...")
        p1_moves = list(range(len(MOVES_PHASE1)))
        p1_size = 2187 * 2048

        self.phase1_prune = [-1] * (2187 * 2048)
        target = 0
        self.phase1_prune[target] = 0
        q = deque([target])
        while q:
            idx = q.popleft()
            depth = self.phase1_prune[idx]
            twist = idx // 2048
            flip = idx % 2048
            for mi in p1_moves:
                nt = self.twist_move[twist][mi]
                nf = self.flip_move[flip][mi]
                nidx = nt * 2048 + nf
                if self.phase1_prune[nidx] == -1:
                    self.phase1_prune[nidx] = depth + 1
                    q.append(nidx)

        print("[Cube3] 构建 Phase 2 剪枝表...")
        p2_moves = [MOVES_PHASE1.index(m) for m in MOVES_PHASE2]

        self.phase2_cperm_prune = _bfs_pruning_table(40320, self.cperm_move, 0, p2_moves)
        self.phase2_eperm_prune = _bfs_pruning_table(40320, self.eperm_move, 0, p2_moves)
        self.phase2_sperm_prune = _bfs_pruning_table(24, self.sperm_move, 0, p2_moves)

        elapsed = time.time() - start
        print(f"[Cube3] 剪枝表构建完成，耗时 {elapsed:.1f}s")

        data = {
            'twist_move': self.twist_move,
            'flip_move': self.flip_move,
            'slice_move': self.slice_move,
            'phase1_prune': self.phase1_prune,
            'cperm_move': self.cperm_move,
            'eperm_move': self.eperm_move,
            'sperm_move': self.sperm_move,
            'phase2_cperm_prune': self.phase2_cperm_prune,
            'phase2_eperm_prune': self.phase2_eperm_prune,
            'phase2_sperm_prune': self.phase2_sperm_prune,
        }
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        print("[Cube3] 剪枝表已缓存到", cache_file)

    def parse_state(self, state_str: str) -> List[str]:
        state_str = state_str.strip().upper()
        if len(state_str) != 54:
            raise ValueError(f"状态字符串长度必须为54，当前为{len(state_str)}")
        for i, ch in enumerate(state_str):
            if ch not in COLORS:
                raise ValueError(f"位置{i}字符非法: {ch}")
        for color in COLORS:
            if state_str.count(color) != 9:
                raise ValueError(f"每种颜色必须恰好出现9次，{color}出现了{state_str.count(color)}次")
        return list(state_str)

    def validate_state(self, state_str: str) -> Tuple[bool, Optional[str]]:
        try:
            state = self.parse_state(state_str)
        except ValueError as e:
            return False, str(e)

        cp, co, ep, eo = get_corners_and_edges(state)

        if sum(co) % 3 != 0:
            return False, "角块朝向和不满足约束 (必须是3的倍数)"

        if sum(eo) % 2 != 0:
            return False, "棱块朝向和不满足约束 (必须是2的倍数)"

        corner_parity = 0
        for i in range(8):
            for j in range(i + 1, 8):
                if cp[i] > cp[j]:
                    corner_parity += 1

        edge_parity = 0
        for i in range(12):
            for j in range(i + 1, 12):
                if ep[i] > ep[j]:
                    edge_parity += 1

        if (corner_parity + edge_parity) % 2 != 0:
            return False, "角块排列与棱块排列的奇偶性不匹配"

        return True, None

    def _get_phase1_coords(self, state: List[str]) -> Tuple[int, int, int]:
        cp, co, ep, eo = get_corners_and_edges(state)
        twist = get_twist(co)
        flip = get_flip(eo)
        slice_sorted = get_slice_sorted(ep)
        return twist, flip, slice_sorted

    def _get_phase2_coords(self, state: List[str]) -> Tuple[int, int, int]:
        cp, co, ep, eo = get_corners_and_edges(state)
        cperm = get_corner_perm_coord(cp)
        eperm = get_ud_edge_perm_coord(ep)
        sperm = get_slice_perm_coord(ep)
        return cperm, eperm, sperm

    def _phase1_heuristic(self, twist: int, flip: int) -> int:
        return self.phase1_prune[twist * 2048 + flip]

    def _phase2_heuristic(self, cperm: int, eperm: int, sperm: int) -> int:
        return max(
            self.phase2_cperm_prune[cperm],
            self.phase2_eperm_prune[eperm],
            self.phase2_sperm_prune[sperm],
        )

    def solve(self, state_str: str, max_depth: int = 20, include_stats: bool = False) -> Tuple[Optional[List[str]], Dict[str, Any]]:
        self.reset_stats()
        try:
            state = self.parse_state(state_str)
        except ValueError as e:
            raise e

        valid, msg = self.validate_state(state_str)
        if not valid:
            raise ValueError(f"状态不合法: {msg}")

        solved = list('U' * 9 + 'R' * 9 + 'F' * 9 + 'D' * 9 + 'L' * 9 + 'B' * 9)
        if state == solved:
            stats = {**self._get_stats(), "depth": 0, "status": "solved"}
            return ([], stats) if include_stats else []

        t, f, s = self._get_phase1_coords(state)
        h = self._phase1_heuristic(t, f)

        for depth in range(h, max_depth + 1):
            path = []
            result = self._phase1_search(state, t, f, s, depth, 0, path, None)
            if result is not None:
                solution = self._optimize_solution(state, result)
                if len(solution) <= 20:
                    stats = {**self._get_stats(), "depth": len(solution), "status": "optimal"}
                    return (solution, stats) if include_stats else solution

        stats = {**self._get_stats(), "depth": -1, "status": "not_found"}
        return (None, stats) if include_stats else None

    def _phase1_search(self, state: List[str], twist: int, flip: int, slice_s: int,
                       max_depth: int, current_depth: int, path: List[str],
                       last_axis: Optional[int]) -> Optional[List[str]]:
        self.nodes_visited += 1
        self.phase1_nodes += 1

        if current_depth == max_depth:
            if twist == 0 and flip == 0 and slice_s == 0:
                return path[:]
            return None

        h = self._phase1_heuristic(twist, flip)
        if current_depth + h > max_depth:
            self.prune_count += 1
            return None

        for mi, move in enumerate(MOVES_PHASE1):
            axis = MOVE_AXIS[move]
            if axis == last_axis:
                continue
            if path and INVERSE_MOVE.get(move) == path[-1]:
                continue

            nt = self.twist_move[twist][mi]
            nf = self.flip_move[flip][mi]
            ns = self.slice_move[slice_s][mi]

            path.append(move)
            result = self._phase1_search(state, nt, nf, ns, max_depth,
                                         current_depth + 1, path, axis)
            if result is not None:
                return result
            path.pop()
            self.backtrack_count += 1

        return None

    def _optimize_solution(self, initial_state: List[str], phase1_solution: List[str]) -> List[str]:
        state = initial_state[:]
        for move in phase1_solution:
            state = apply_move(state, move)

        cperm, eperm, sperm = self._get_phase2_coords(state)

        for depth in range(0, 20 - len(phase1_solution) + 1):
            path = []
            result = self._phase2_search(state, cperm, eperm, sperm, depth, 0, path, None)
            if result is not None:
                full_solution = phase1_solution + result
                return self._simplify_solution(initial_state, full_solution)

        return phase1_solution

    def _phase2_search(self, state: List[str], cperm: int, eperm: int, sperm: int,
                       max_depth: int, current_depth: int, path: List[str],
                       last_axis: Optional[int]) -> Optional[List[str]]:
        self.nodes_visited += 1
        self.phase2_nodes += 1

        if current_depth == max_depth:
            if cperm == 0 and eperm == 0 and sperm == 0:
                return path[:]
            return None

        h = self._phase2_heuristic(cperm, eperm, sperm)
        if current_depth + h > max_depth:
            self.prune_count += 1
            return None

        for move in MOVES_PHASE2:
            mi = MOVES_PHASE1.index(move)
            axis = MOVE_AXIS[move]
            if axis == last_axis:
                continue
            if path and INVERSE_MOVE.get(move) == path[-1]:
                continue

            nc = self.cperm_move[cperm][mi] if mi < len(self.cperm_move[0]) else cperm
            ne = self.eperm_move[eperm][mi] if mi < len(self.eperm_move[0]) else eperm
            ns_ = self.sperm_move[sperm][mi] if mi < len(self.sperm_move[0]) else sperm

            path.append(move)
            result = self._phase2_search(state, nc, ne, ns_, max_depth,
                                         current_depth + 1, path, axis)
            if result is not None:
                return result
            path.pop()
            self.backtrack_count += 1

        return None

    def _simplify_solution(self, state: List[str], solution: List[str]) -> List[str]:
        simplified = solution[:]
        i = 0
        while i < len(simplified) - 1:
            if simplified[i] == INVERSE_MOVE[simplified[i + 1]]:
                simplified = simplified[:i] + simplified[i + 2:]
                i = max(0, i - 1)
            else:
                i += 1

        i = 0
        while i < len(simplified) - 1:
            m1, m2 = simplified[i], simplified[i + 1]
            if MOVE_AXIS[m1] == MOVE_AXIS[m2]:
                face = m1.rstrip("'2")
                cnt1 = 1 if m1 == face else (2 if m1 == face + '2' else 3)
                cnt2 = 1 if m2 == face else (2 if m2 == face + '2' else 3)
                total = (cnt1 + cnt2) % 4
                if total == 0:
                    simplified = simplified[:i] + simplified[i + 2:]
                    i = max(0, i - 1)
                elif total == 1:
                    simplified[i:i + 2] = [face]
                elif total == 2:
                    simplified[i:i + 2] = [face + '2']
                else:
                    simplified[i:i + 2] = [face + "'"]
            else:
                i += 1

        return simplified

    def verify_solution(self, state_str: str, moves: List[str]) -> Tuple[bool, str]:
        try:
            state = self.parse_state(state_str)
        except ValueError as e:
            return False, str(e)

        for move in moves:
            if move not in FACE_PERM:
                return False, f"非法操作: {move}"
            state = apply_move(state, move)

        solved = list('U' * 9 + 'R' * 9 + 'F' * 9 + 'D' * 9 + 'L' * 9 + 'B' * 9)
        if state == solved:
            return True, "已还原"
        return False, "未还原，最终状态: " + "".join(state)

    def _get_stats(self) -> Dict[str, int]:
        return {
            "nodes_visited": self.nodes_visited,
            "backtrack_count": self.backtrack_count,
            "prune_count": self.prune_count,
            "phase1_nodes": self.phase1_nodes,
            "phase2_nodes": self.phase2_nodes,
        }
