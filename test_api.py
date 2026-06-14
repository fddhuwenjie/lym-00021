import requests
import json
import time

BASE_URL = "http://127.0.0.1:8021"

def test_nqueens_count():
    print("=" * 60)
    print("测试 N 皇后 N=14 解计数")
    print("=" * 60)
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/count",
        json={"problem_type": "nqueens", "n": 14},
        timeout=30
    )
    elapsed = time.time() - start
    data = response.json()
    print(f"状态: {data['status']}")
    print(f"解数: {data['solution_count']}")
    print(f"预期: 365596")
    print(f"耗时: {elapsed:.2f}s (目标 < 5s)")
    print(f"正确: {data['solution_count'] == 365596 and elapsed < 5.0}")
    print(f"统计: {data.get('stats', {})}")
    print()

def test_csp_graph_coloring():
    print("=" * 60)
    print("测试通用 CSP 引擎 - 4色图着色")
    print("=" * 60)
    problem = {
        "variables": ["WA", "NT", "SA", "Q", "NSW", "V", "T"],
        "domains": {
            "WA": [0, 1, 2, 3],
            "NT": [0, 1, 2, 3],
            "SA": [0, 1, 2, 3],
            "Q": [0, 1, 2, 3],
            "NSW": [0, 1, 2, 3],
            "V": [0, 1, 2, 3],
            "T": [0, 1, 2, 3],
        },
        "constraints": [
            {"type": "all_different", "variables": ["WA", "NT"]},
            {"type": "all_different", "variables": ["WA", "SA"]},
            {"type": "all_different", "variables": ["NT", "SA"]},
            {"type": "all_different", "variables": ["NT", "Q"]},
            {"type": "all_different", "variables": ["SA", "Q"]},
            {"type": "all_different", "variables": ["SA", "NSW"]},
            {"type": "all_different", "variables": ["SA", "V"]},
            {"type": "all_different", "variables": ["Q", "NSW"]},
            {"type": "all_different", "variables": ["NSW", "V"]},
        ],
    }
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/csp/solve",
        json={"problem": problem, "mode": "one"},
        timeout=30
    )
    elapsed = time.time() - start
    data = response.json()
    print(f"状态: {data['status']}")
    print(f"解数: {data['solution_count']}")
    print(f"解: {data['solution']}")
    print(f"耗时: {elapsed:.4f}s")
    print(f"正确: {data['solution_count'] >= 1}")
    print(f"统计: {data.get('stats', {})}")
    print()

def test_csp_examples():
    print("=" * 60)
    print("测试 CSP 预置实例")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/api/csp/examples", timeout=10)
    data = response.json()
    print(f"状态: {data['status']}")
    print(f"实例数: {len(data['examples'])}")
    print(f"实例名: {list(data['examples'].keys())}")
    print()

def test_sudoku_count():
    print("=" * 60)
    print("测试数独解计数")
    print("=" * 60)
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/count",
        json={
            "problem_type": "sudoku",
            "board_string": "003020600900305001001806400008102900700000008006708200002609500800203009005010300"
        },
        timeout=30
    )
    elapsed = time.time() - start
    data = response.json()
    print(f"状态: {data['status']}")
    print(f"解数: {data['solution_count']}")
    print(f"是否达到上限: {data['hit_limit']}")
    print(f"耗时: {elapsed:.2f}s")
    print(f"统计: {data.get('stats', {})}")
    print()

def test_cube3_validate():
    print("=" * 60)
    print("测试三阶魔方状态验证")
    print("=" * 60)
    solved_state = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/cube3/validate",
        json={"state_string": solved_state},
        timeout=120
    )
    elapsed = time.time() - start
    data = response.json()
    print(f"状态: {data['status']}")
    print(f"验证结果: {data['valid']}")
    print(f"原因: {data['reason']}")
    print(f"耗时: {elapsed:.2f}s")
    print()

def test_cube2_count():
    print("=" * 60)
    print("测试二阶魔方最短路径计数")
    print("=" * 60)
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/count",
        json={
            "problem_type": "cube2",
            "state_string": "YBOORRYOWORGWBGGBYRGBYWW",
            "max_depth": 11
        },
        timeout=30
    )
    elapsed = time.time() - start
    data = response.json()
    print(f"状态: {data['status']}")
    print(f"最短路径数: {data['shortest_path_count']}")
    print(f"最短深度: {data['shortest_depth']}")
    print(f"耗时: {elapsed:.2f}s")
    print(f"统计: {data.get('stats', {})}")
    print()

if __name__ == "__main__":
    try:
        test_nqueens_count()
        test_csp_graph_coloring()
        test_csp_examples()
        test_sudoku_count()
        test_cube2_count()
        print("=" * 60)
        print("所有非魔方测试完成！")
        print("魔方测试需要先构建剪枝表，可能需要几分钟...")
        print("=" * 60)
        test_cube3_validate()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
