import time

def count_nqueens_fast(n):
    full_mask = (1 << n) - 1
    count = 0

    def backtrack(row, cols, diag1, diag2):
        nonlocal count
        if row == n:
            count += 1
            return

        available = full_mask & ~(cols | diag1 | diag2)
        while available:
            p = available & -available
            available -= p
            backtrack(row + 1, cols | p, (diag1 | p) << 1, (diag2 | p) >> 1)

    backtrack(0, 0, 0, 0)
    return count

n = 14
start = time.time()
result = count_nqueens_fast(n)
elapsed = time.time() - start

with open("n14_result.txt", "w") as f:
    f.write(f"N={n}\n")
    f.write(f"Count={result}\n")
    f.write(f"Expected=365596\n")
    f.write(f"Match={result == 365596}\n")
    f.write(f"Elapsed={elapsed:.2f}s\n")
    f.write(f"Within5s={elapsed < 5.0}\n")

print(f"Done: {elapsed:.2f}s, count={result}")
