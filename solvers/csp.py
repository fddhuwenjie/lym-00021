from typing import List, Optional, Dict, Any, Tuple, Set, Callable
from collections import deque
import time


class CSPSolver:
    def __init__(self):
        self.reset_stats()

    def reset_stats(self):
        self.nodes_visited = 0
        self.backtrack_count = 0
        self.prune_count = 0
        self.propagate_count = 0
        self.revise_count = 0
        self.start_time = 0.0

    def _get_stats(self, elapsed: float) -> Dict[str, Any]:
        return {
            "nodes_visited": self.nodes_visited,
            "backtrack_count": self.backtrack_count,
            "prune_count": self.prune_count,
            "propagate_count": self.propagate_count,
            "revise_count": self.revise_count,
            "elapsed_ms": round(elapsed * 1000, 2),
        }

    def solve(self, problem: Dict[str, Any], mode: str = "one",
              solution_limit: int = 100) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        self.reset_stats()
        self.start_time = time.time()

        variables = problem.get("variables", [])
        domains = problem.get("domains", {})
        constraints = problem.get("constraints", [])

        if not variables:
            raise ValueError("必须指定 variables 列表")
        if not domains:
            raise ValueError("必须指定 domains 字典")

        for var in variables:
            if var not in domains:
                raise ValueError(f"变量 {var} 没有对应的定义域")

        current_domains = {var: set(domains[var]) for var in variables}
        constraint_map = self._build_constraint_map(variables, constraints)

        consistent = self._ac3(variables, current_domains, constraint_map)
        if not consistent:
            elapsed = time.time() - self.start_time
            return [], self._get_stats(elapsed)

        for var in variables:
            if len(current_domains[var]) == 0:
                elapsed = time.time() - self.start_time
                return [], self._get_stats(elapsed)

        assignment = {}
        for var in variables:
            if len(current_domains[var]) == 1:
                assignment[var] = list(current_domains[var])[0]

        solutions = []

        if mode == "one":
            result = self._backtrack_one(assignment, variables, current_domains,
                                         constraint_map, solution_limit)
            if result is not None:
                solutions = [result]
        else:
            solutions = []
            self._backtrack_all(assignment, variables, current_domains,
                                constraint_map, solution_limit, solutions)

        elapsed = time.time() - self.start_time
        return solutions, self._get_stats(elapsed)

    def _build_constraint_map(self, variables: List[str],
                              constraints: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        constraint_map = {var: [] for var in variables}

        for constraint in constraints:
            ctype = constraint.get("type")
            if ctype == "all_different":
                vars_list = constraint.get("variables", [])
                for i, var1 in enumerate(vars_list):
                    for j, var2 in enumerate(vars_list):
                        if i != j:
                            constraint_map[var1].append({
                                "type": "binary_different",
                                "var1": var1,
                                "var2": var2,
                            })
                            constraint_map[var2].append({
                                "type": "binary_different",
                                "var1": var2,
                                "var2": var1,
                            })

            elif ctype == "binary_relation":
                var1 = constraint.get("var1")
                var2 = constraint.get("var2")
                relation = constraint.get("relation")
                if var1 not in variables or var2 not in variables:
                    continue
                constraint_map[var1].append({
                    "type": "binary_relation",
                    "var1": var1,
                    "var2": var2,
                    "relation": relation,
                })
                constraint_map[var2].append({
                    "type": "binary_relation",
                    "var1": var2,
                    "var2": var1,
                    "relation": self._inverse_relation(relation),
                })

            elif ctype == "table_constraint":
                vars_list = constraint.get("variables", [])
                tuples = constraint.get("tuples", [])
                for i, var1 in enumerate(vars_list):
                    for j, var2 in enumerate(vars_list):
                        if i != j:
                            allowed = set()
                            for t in tuples:
                                allowed.add((t[i], t[j]))
                            constraint_map[var1].append({
                                "type": "table_binary",
                                "var1": var1,
                                "var2": var2,
                                "allowed": allowed,
                                "i": i,
                                "j": j,
                            })

        return constraint_map

    def _inverse_relation(self, relation: str) -> str:
        inverse_map = {
            "==": "==",
            "!=": "!=",
            "<": ">",
            ">": "<",
            "<=": ">=",
            ">=": "<=",
        }
        return inverse_map.get(relation, relation)

    def _ac3(self, variables: List[str], domains: Dict[str, Set[Any]],
             constraint_map: Dict[str, List[Dict[str, Any]]]) -> bool:
        queue = deque()

        for var in variables:
            for constraint in constraint_map[var]:
                other_var = constraint["var2"]
                queue.append((var, other_var, constraint))

        while queue:
            xi, xj, constraint = queue.popleft()
            self.propagate_count += 1

            if self._revise(xi, xj, domains, constraint):
                self.revise_count += 1
                if len(domains[xi]) == 0:
                    return False

                for c in constraint_map[xi]:
                    if c["var2"] != xj:
                        queue.append((c["var2"], xi, c))

        return True

    def _revise(self, xi: str, xj: str, domains: Dict[str, Set[Any]],
                constraint: Dict[str, Any]) -> bool:
        revised = False
        to_remove = []

        for x in domains[xi]:
            satisfied = False
            for y in domains[xj]:
                if self._check_constraint(x, y, constraint):
                    satisfied = True
                    break
            if not satisfied:
                to_remove.append(x)
                revised = True

        for x in to_remove:
            domains[xi].discard(x)
            self.prune_count += 1

        return revised

    def _check_constraint(self, x_val: Any, y_val: Any,
                          constraint: Dict[str, Any]) -> bool:
        ctype = constraint["type"]

        if ctype == "binary_different":
            return x_val != y_val

        elif ctype == "binary_relation":
            rel = constraint["relation"]
            if rel == "==":
                return x_val == y_val
            elif rel == "!=":
                return x_val != y_val
            elif rel == "<":
                return x_val < y_val
            elif rel == ">":
                return x_val > y_val
            elif rel == "<=":
                return x_val <= y_val
            elif rel == ">=":
                return x_val >= y_val

        elif ctype == "table_binary":
            return (x_val, y_val) in constraint["allowed"]

        return True

    def _select_unassigned_variable(self, assignment: Dict[str, Any],
                                    variables: List[str],
                                    domains: Dict[str, Set[Any]]) -> Optional[str]:
        unassigned = [v for v in variables if v not in assignment]
        if not unassigned:
            return None

        best_var = None
        best_size = float('inf')

        for var in unassigned:
            size = len(domains[var])
            if size < best_size:
                best_size = size
                best_var = var

        return best_var

    def _order_domain_values(self, var: str, assignment: Dict[str, Any],
                             domains: Dict[str, Set[Any]]) -> List[Any]:
        return list(domains[var])

    def _backtrack_one(self, assignment: Dict[str, Any], variables: List[str],
                       domains: Dict[str, Set[Any]],
                       constraint_map: Dict[str, List[Dict[str, Any]]],
                       limit: int) -> Optional[Dict[str, Any]]:
        self.nodes_visited += 1

        if len(assignment) == len(variables):
            return assignment.copy()

        var = self._select_unassigned_variable(assignment, variables, domains)
        if var is None:
            return None

        for value in self._order_domain_values(var, assignment, domains):
            if self._is_consistent(var, value, assignment, constraint_map):
                assignment[var] = value

                saved_domain = domains[var].copy()
                domains[var] = {value}

                inferences = self._forward_check(var, assignment, domains, constraint_map)
                if inferences is not None:
                    result = self._backtrack_one(assignment, variables, domains,
                                                 constraint_map, limit)
                    if result is not None:
                        return result

                assignment.pop(var)
                domains[var] = saved_domain
                self.backtrack_count += 1

        return None

    def _backtrack_all(self, assignment: Dict[str, Any], variables: List[str],
                       domains: Dict[str, Set[Any]],
                       constraint_map: Dict[str, List[Dict[str, Any]]],
                       limit: int, solutions: List[Dict[str, Any]]) -> None:
        self.nodes_visited += 1

        if len(solutions) >= limit:
            return

        if len(assignment) == len(variables):
            solutions.append(assignment.copy())
            return

        var = self._select_unassigned_variable(assignment, variables, domains)
        if var is None:
            return

        for value in self._order_domain_values(var, assignment, domains):
            if self._is_consistent(var, value, assignment, constraint_map):
                assignment[var] = value

                saved_domain = domains[var].copy()
                domains[var] = {value}

                inferences = self._forward_check(var, assignment, domains, constraint_map)
                if inferences is not None:
                    self._backtrack_all(assignment, variables, domains,
                                        constraint_map, limit, solutions)

                assignment.pop(var)
                domains[var] = saved_domain
                self.backtrack_count += 1

                if len(solutions) >= limit:
                    return

    def _is_consistent(self, var: str, value: Any, assignment: Dict[str, Any],
                       constraint_map: Dict[str, List[Dict[str, Any]]]) -> bool:
        for constraint in constraint_map[var]:
            other_var = constraint["var2"]
            if other_var in assignment:
                if not self._check_constraint(value, assignment[other_var], constraint):
                    return False
        return True

    def _forward_check(self, var: str, assignment: Dict[str, Any],
                       domains: Dict[str, Set[Any]],
                       constraint_map: Dict[str, List[Dict[str, Any]]]) -> Optional[Dict[str, Set[Any]]]:
        inferences = {}

        for constraint in constraint_map[var]:
            other_var = constraint["var2"]
            if other_var in assignment:
                continue

            to_remove = []
            for val in domains[other_var]:
                if not self._check_constraint(val, assignment[var], constraint):
                    to_remove.append(val)

            if to_remove:
                inferences[other_var] = set(to_remove)
                for val in to_remove:
                    domains[other_var].discard(val)
                    self.prune_count += 1

                if len(domains[other_var]) == 0:
                    for ov, removed in inferences.items():
                        domains[ov].update(removed)
                    return None

        return inferences

    @staticmethod
    def get_examples() -> Dict[str, Dict[str, Any]]:
        return {
            "graph_coloring": CSPSolver._graph_coloring_example(),
            "latin_square": CSPSolver._latin_square_example(),
            "scheduling": CSPSolver._scheduling_example(),
        }

    @staticmethod
    def _graph_coloring_example() -> Dict[str, Any]:
        return {
            "name": "4色图着色问题",
            "description": "澳大利亚地图着色：7个区域用4种颜色着色，相邻区域颜色不同",
            "problem": {
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
            },
            "color_names": ["红", "蓝", "绿", "黄"],
        }

    @staticmethod
    def _latin_square_example() -> Dict[str, Any]:
        return {
            "name": "3阶拉丁方",
            "description": "3x3方格，每行每列数字1-3不重复",
            "problem": {
                "variables": [
                    "r0c0", "r0c1", "r0c2",
                    "r1c0", "r1c1", "r1c2",
                    "r2c0", "r2c1", "r2c2",
                ],
                "domains": {var: [1, 2, 3] for var in [
                    "r0c0", "r0c1", "r0c2",
                    "r1c0", "r1c1", "r1c2",
                    "r2c0", "r2c1", "r2c2",
                ]},
                "constraints": [
                    {"type": "all_different", "variables": ["r0c0", "r0c1", "r0c2"]},
                    {"type": "all_different", "variables": ["r1c0", "r1c1", "r1c2"]},
                    {"type": "all_different", "variables": ["r2c0", "r2c1", "r2c2"]},
                    {"type": "all_different", "variables": ["r0c0", "r1c0", "r2c0"]},
                    {"type": "all_different", "variables": ["r0c1", "r1c1", "r2c1"]},
                    {"type": "all_different", "variables": ["r0c2", "r1c2", "r2c2"]},
                ],
            },
        }

    @staticmethod
    def _scheduling_example() -> Dict[str, Any]:
        return {
            "name": "排课问题",
            "description": "4门课程安排到3个时段，满足先修约束和教师约束",
            "problem": {
                "variables": ["Math", "Physics", "Chemistry", "Biology"],
                "domains": {
                    "Math": [1, 2, 3],
                    "Physics": [1, 2, 3],
                    "Chemistry": [1, 2, 3],
                    "Biology": [1, 2, 3],
                },
                "constraints": [
                    {"type": "all_different", "variables": ["Math", "Physics"]},
                    {"type": "all_different", "variables": ["Physics", "Chemistry"]},
                    {"type": "binary_relation", "var1": "Math", "var2": "Chemistry", "relation": "<"},
                    {"type": "binary_relation", "var1": "Biology", "var2": "Physics", "relation": "!="},
                ],
            },
            "time_slots": {
                1: "周一上午",
                2: "周一下午",
                3: "周二上午",
            },
        }
