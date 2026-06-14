import sys
import time
from solvers.counter import CounterSolver

def main():
    n = 14
    print(f"Testing N={n} queens...", file=sys.stderr)
    sys.stderr.flush()

    counter = CounterSolver()
    start = time.time()
    count, stats = counter.count_nqueens(n)
    elapsed = time.time() - start

    with open("nqueens_result.txt", "w") as f:
        f.write(f"N={n}\n")
        f.write(f"Count={count}\n")
        f.write(f"Expected=365596\n")
        f.write(f"Match={count == 365596}\n")
        f.write(f"Elapsed={elapsed:.2f}s\n")
        f.write(f"Within5s={elapsed < 5.0}\n")
        f.write(f"Stats={stats}\n")

    print(f"Done. Elapsed={elapsed:.2f}s", file=sys.stderr)

if __name__ == "__main__":
    main()
