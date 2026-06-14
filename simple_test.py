import time
import sys
from solvers.counter import CounterSolver

n = 14
print(f"Testing N={n} queens with symmetry optimization...")
sys.stdout.flush()

counter = CounterSolver()
start = time.time()
count, stats = counter.count_nqueens(n)
elapsed = time.time() - start

print(f"N={n}")
print(f"Count={count}")
print(f"Expected=365596")
print(f"Match={count == 365596}")
print(f"Elapsed={elapsed:.2f}s")
print(f"Within5s={elapsed < 5.0}")
print(f"Stats={stats}")
