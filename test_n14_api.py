import requests
import time

BASE_URL = "http://127.0.0.1:8021"

print("Testing N=14 queens (second run)...")
start = time.time()
response = requests.post(
    f"{BASE_URL}/api/count",
    json={"problem_type": "nqueens", "n": 14},
    timeout=30
)
elapsed = time.time() - start
data = response.json()
print(f"Status: {data['status']}")
print(f"Count: {data['solution_count']}")
print(f"Expected: 365596")
print(f"Elapsed: {elapsed:.2f}s (target < 5s)")
print(f"Match: {data['solution_count'] == 365596}")
print(f"Within 5s: {elapsed < 5.0}")

with open("n14_api_result.txt", "w") as f:
    f.write(f"Status: {data['status']}\n")
    f.write(f"Count: {data['solution_count']}\n")
    f.write(f"Expected: 365596\n")
    f.write(f"Elapsed: {elapsed:.2f}s\n")
    f.write(f"Match: {data['solution_count'] == 365596}\n")
    f.write(f"Within 5s: {elapsed < 5.0}\n")
