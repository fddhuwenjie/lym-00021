import time
from solvers.counter import CounterSolver

counter = CounterSolver()
start = time.time()
count, stats = counter.count_nqueens(14)
elapsed = time.time() - start
print(f'N=14, count={count}, elapsed={elapsed:.2f}s')
print(f'Stats: {stats}')
print(f'Expected: 365596, Match: {count == 365596}')
print(f'Within 5s: {elapsed < 5.0}')
