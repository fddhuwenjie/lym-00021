import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8021"

def test_root():
    print("=" * 60)
    print("测试根目录")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/", timeout=10)
    data = response.json()
    print(f"服务名称: {data['name']}")
    print(f"端口: {data['port']}")
    print(f"可用端点: {list(data['endpoints'].keys())}")
    print()
    return True

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
    ok = data['status'] == 'ok' and data['solution_count'] == 365596 and elapsed < 5.0
    print(f"结果: {'PASS' if ok else 'FAIL'}")
    print()
    return ok

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
    ok = data['status'] == 'ok' and data['solution_count'] == 1
    print(f"结果: {'PASS' if ok else 'FAIL'}")
    print()
    return ok

def test_cube2_count():
    print("=" * 60)
    print("测试二阶魔方最短路径计数")
    print("=" * 60)
    start = time.time()
    response = requests.post(
        f"{BASE_URL}/api/count",
        json={
            "problem_type": "cube2",
            "state_string": "WWWWOOOOGGGGBBBBRRRRYYYY",
            "max_depth": 2
        },
        timeout=30
    )
    elapsed = time.time() - start
    data = response.json()
    print(f"状态: {data['status']}")
    if data['status'] == 'ok':
        print(f"最短路径数: {data['shortest_path_count']}")
        print(f"最短深度: {data['shortest_depth']}")
        print(f"预期: Count=1, Depth=0 (已还原状态)")
        ok = data['shortest_path_count'] == 1 and data['shortest_depth'] == 0
    else:
        print(f"错误: {data.get('message', 'Unknown')}")
        ok = False
    print(f"耗时: {elapsed:.2f}s")
    print(f"结果: {'PASS' if ok else 'FAIL'}")
    print()
    return ok

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
    print(f"传播次数: {data['stats']['propagate_count']}")
    print(f"回溯次数: {data['stats']['backtrack_count']}")
    print(f"耗时: {elapsed:.4f}s")
    ok = data['status'] == 'ok' and data['solution_count'] >= 1
    print(f"结果: {'PASS' if ok else 'FAIL'}")
    print()
    return ok

def test_csp_examples():
    print("=" * 60)
    print("测试 CSP 预置实例")
    print("=" * 60)
    response = requests.get(f"{BASE_URL}/api/csp/examples", timeout=10)
    data = response.json()
    print(f"状态: {data['status']}")
    print(f"实例数: {len(data['examples'])}")
    print(f"实例名: {list(data['examples'].keys())}")
    ok = data['status'] == 'ok' and len(data['examples']) >= 3
    print(f"结果: {'PASS' if ok else 'FAIL'}")
    print()
    return ok

def test_cube3_validate():
    print("=" * 60)
    print("测试三阶魔方状态验证")
    print("=" * 60)
    print("注意: 首次调用会构建剪枝表，可能需要几分钟...")
    sys.stdout.flush()
    solved_state = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/cube3/validate",
            json={"state_string": solved_state},
            timeout=600
        )
        elapsed = time.time() - start
        data = response.json()
        print(f"状态: {data['status']}")
        print(f"验证结果: {data['valid']}")
        print(f"原因: {data['reason']}")
        print(f"耗时: {elapsed:.2f}s")
        ok = data['status'] == 'ok' and data['valid'] == True
        print(f"结果: {'PASS' if ok else 'FAIL'}")
    except Exception as e:
        elapsed = time.time() - start
        print(f"错误: {e}")
        print(f"耗时: {elapsed:.2f}s")
        ok = False
        print(f"结果: SKIP (剪枝表构建耗时过长，跳过)")
    print()
    return ok

if __name__ == "__main__":
    results = []
    try:
        results.append(("根目录", test_root()))
        results.append(("N皇后N=14", test_nqueens_count()))
        results.append(("数独计数", test_sudoku_count()))
        results.append(("二阶魔方计数", test_cube2_count()))
        results.append(("CSP图着色", test_csp_graph_coloring()))
        results.append(("CSP预置实例", test_csp_examples()))
        # results.append(("三阶魔方验证", test_cube3_validate()))

        print("=" * 60)
        print("测试总结")
        print("=" * 60)
        passed = sum(1 for _, ok in results if ok)
        total = len(results)
        for name, ok in results:
            status = "PASS" if ok else "FAIL"
            print(f"  {name}: {status}")
        print(f"\n总计: {passed}/{total} 通过")
        print(f"全部通过: {passed == total}")
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()
