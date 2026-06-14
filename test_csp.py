from solvers.csp import CSPSolver

solver = CSPSolver()
examples = CSPSolver.get_examples()
print("Examples available:", list(examples.keys()))

problem = examples['graph_coloring']['problem']
solutions, stats = solver.solve(problem, mode='one')
print(f"\nGraph coloring solution: {solutions[0] if solutions else None}")
print(f"Stats: {stats}")

problem2 = examples['latin_square']['problem']
solutions2, stats2 = solver.solve(problem2, mode='one')
print(f"\nLatin square solution: {solutions2[0] if solutions2 else None}")
print(f"Stats: {stats2}")
