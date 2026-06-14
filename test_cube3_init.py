import time
print("Starting Cube3Solver init...")
start = time.time()
try:
    from solvers.cube3 import Cube3Solver
    print("Import OK")
    solver = Cube3Solver()
    print("Init OK")
    elapsed = time.time() - start
    print(f"Elapsed: {elapsed:.2f}s")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
