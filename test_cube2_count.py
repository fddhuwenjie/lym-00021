import sys
import time
from solvers.counter import CounterSolver

counter = CounterSolver()
state = "YBOORRYOWORGWBGGBYRGBYWW"
print(f"Testing cube2 count for state: {state}")
sys.stdout.flush()

try:
    start = time.time()
    count, depth, stats = counter.count_cube2_shortest_paths_bfs(state, max_depth=11)
    elapsed = time.time() - start
    print(f"Count: {count}")
    print(f"Depth: {depth}")
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"Stats: {stats}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
