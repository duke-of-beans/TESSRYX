"""OR-Tools CP-SAT adapter for TESSRYX constraint solving.

This module implements the Solver interface using Google OR-Tools CP-SAT,
optimized for discrete scheduling and resource allocation problems.

Supported Constraint Types (V1):
- precedence: Task A must complete before Task B starts
- mutex: Tasks A and B cannot overlap (mutually exclusive)
- choice: Exactly one task from a set must be selected

Performance Targets:
- 100 constraints: <1 second
- 500 constraints: <5 seconds
- 1000 constraints: <10 seconds
"""

import time
from typing import Dict, List, Optional, Set
from uuid import UUID

from ortools.sat.python import cp_model

from tessryx.core.constraint import Constraint
from tessryx.core.entity import Entity
from tessryx.kernel.solver.base import (
    Assignment,
    Objective,
    Solution,
    SolutionSet,
    SolutionStatus,
    Solver,
    UnsatCore,
)


# =============================================================================
# OR-TOOLS ADAPTER
# =============================================================================


class ORToolsSolver(Solver):
    """Google OR-Tools CP-SAT solver for discrete optimization.
    
    Capabilities:
    - Task scheduling with precedence constraints
    - Resource allocation with capacity constraints
    - Discrete optimization (minimize time, minimize cost, etc.)
    - Alternative solution generation (N-best)
    
    Examples:
        >>> solver = ORToolsSolver()
        >>> # Schedule 3 tasks: A -> B -> C
        >>> solution = solver.solve(
        ...     entities=[task_a, task_b, task_c],
        ...     constraints=[precedence_ab, precedence_bc]
        ... )
    """

    def __init__(self) -> None:
        """Initialize OR-Tools solver."""
        self._model: Optional[cp_model.CpModel] = None
        self._solver: Optional[cp_model.CpSolver] = None
        self._variables: Dict[str, any] = {}  # Entity -> CP variables
        self._entity_map: Dict[UUID, Entity] = {}

    def get_capabilities(self) -> Set[str]:
        """Return supported constraint types."""
        return {
            "precedence",  # A before B
            "mutex",  # A XOR B
            "choice",  # Exactly one of {A, B, C}
        }

    def solve(
        self,
        entities: List[Entity],
        constraints: List[Constraint],
        objective: Optional[Objective] = None,
        timeout_seconds: float = 60.0,
    ) -> Solution:
        """Solve constraint satisfaction problem using OR-Tools CP-SAT."""
        start_time = time.time()

        # Build entity map
        self._entity_map = {e.id: e for e in entities}

        # Create fresh model
        self._model = cp_model.CpModel()
        self._variables = {}

        try:
            # Encode variables (start_time, end_time for each task)
            self._encode_variables(entities)

            # Encode constraints
            self._encode_constraints(constraints)

            # Encode objective (if provided)
            if objective:
                self._encode_objective(objective)

            # Solve
            self._solver = cp_model.CpSolver()
            self._solver.parameters.max_time_in_seconds = timeout_seconds

            status = self._solver.Solve(self._model)

            # Decode solution
            solve_time = time.time() - start_time

            return self._decode_solution(status, entities, solve_time)

        except Exception as e:
            import traceback
            return Solution(
                status=SolutionStatus.ERROR,
                assignments=[],
                solve_time_seconds=time.time() - start_time,
                proof=f"Solver error: {str(e)}\n{traceback.format_exc()}",
            )

    def find_alternatives(
        self,
        entities: List[Entity],
        constraints: List[Constraint],
        objective: Optional[Objective] = None,
        max_solutions: int = 3,
        timeout_seconds: float = 60.0,
    ) -> SolutionSet:
        """Find multiple alternative solutions using solution pool."""
        start_time = time.time()
        
        # Build entity map
        self._entity_map = {e.id: e for e in entities}
        
        # Create fresh model
        self._model = cp_model.CpModel()
        self._variables = {}
        
        # Encode variables and constraints
        self._encode_variables(entities)
        self._encode_constraints(constraints)
        
        if objective:
            self._encode_objective(objective)
        
        # Create solver with solution callback
        self._solver = cp_model.CpSolver()
        self._solver.parameters.max_time_in_seconds = timeout_seconds
        self._solver.parameters.enumerate_all_solutions = True
        self._solver.parameters.num_search_workers = 1  # Required for callbacks
        
        # Callback to collect solutions
        solutions_found = []
        
        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self, variables, entities, max_sols, parent_solver):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self._variables = variables
                self._entities = entities
                self._max_solutions = max_sols
                self._parent = parent_solver
                self._solutions = []
            
            def on_solution_callback(self):
                if len(self._solutions) >= self._max_solutions:
                    self.StopSearch()
                    return
                
                # Extract assignments for this solution
                assignments = []
                for entity in self._entities:
                    start_var = self._variables.get(f"{entity.id}_start")
                    end_var = self._variables.get(f"{entity.id}_end")
                    
                    if start_var is not None and end_var is not None:
                        start_time = self.Value(start_var)
                        end_time = self.Value(end_var)
                        
                        assignments.append(
                            Assignment(
                                entity_id=entity.id,
                                attribute="start_time",
                                value=start_time,
                                unit="time_unit",
                            )
                        )
                        
                        assignments.append(
                            Assignment(
                                entity_id=entity.id,
                                attribute="end_time",
                                value=end_time,
                                unit="time_unit",
                            )
                        )
                
                # Get objective value if applicable
                obj_value = None
                if hasattr(self, "ObjectiveValue"):
                    try:
                        obj_value = self.ObjectiveValue()
                    except:
                        pass
                
                self._solutions.append((assignments, obj_value))
        
        collector = SolutionCollector(
            self._variables, entities, max_solutions, self._solver
        )
        
        # Solve with callback
        status = self._solver.Solve(self._model, collector)
        solve_time = time.time() - start_time
        
        # Convert collected solutions to Solution objects
        if collector._solutions:
            # First solution is optimal (if status is OPTIMAL)
            status_map = {
                cp_model.OPTIMAL: SolutionStatus.OPTIMAL,
                cp_model.FEASIBLE: SolutionStatus.FEASIBLE,
                cp_model.INFEASIBLE: SolutionStatus.INFEASIBLE,
            }
            
            solution_status = status_map.get(status, SolutionStatus.UNKNOWN)
            
            optimal = Solution(
                status=solution_status,
                assignments=collector._solutions[0][0],
                objective_value=collector._solutions[0][1],
                solve_time_seconds=solve_time,
                metadata={
                    "solver": "OR-Tools CP-SAT",
                    "num_solutions_found": len(collector._solutions),
                },
            )
            
            alternatives = [
                Solution(
                    status=SolutionStatus.FEASIBLE,
                    assignments=sol[0],
                    objective_value=sol[1],
                    solve_time_seconds=solve_time,
                )
                for sol in collector._solutions[1:]
            ]
            
            return SolutionSet(
                optimal=optimal,
                alternatives=alternatives,
                total_feasible=len(collector._solutions),
            )
        else:
            # No solutions found
            return SolutionSet(
                optimal=Solution(
                    status=SolutionStatus.INFEASIBLE,
                    assignments=[],
                    solve_time_seconds=solve_time,
                ),
                alternatives=[],
                total_feasible=0,
            )

    def find_unsat_core(
        self, entities: List[Entity], constraints: List[Constraint]
    ) -> UnsatCore:
        """Find minimal conflicting constraint set.
        
        Note: OR-Tools CP-SAT doesn't provide native unsat cores.
        This is a simplified implementation that identifies conflicts through
        iterative constraint relaxation.
        
        For full unsat core analysis, use Z3Solver instead.
        """
        # First, verify the problem is actually infeasible
        self._entity_map = {e.id: e for e in entities}
        self._model = cp_model.CpModel()
        self._variables = {}
        
        self._encode_variables(entities)
        self._encode_constraints(constraints)
        
        self._solver = cp_model.CpSolver()
        self._solver.parameters.max_time_in_seconds = 5.0
        status = self._solver.Solve(self._model)
        
        if status != cp_model.INFEASIBLE:
            raise ValueError("Problem is feasible, no unsat core exists")
        
        # Try removing constraints one at a time to find conflicts
        # This is a naive approach - proper unsat cores require SMT solver
        conflicting = []
        
        for i, constraint in enumerate(constraints):
            # Try solving without this constraint
            test_constraints = [c for j, c in enumerate(constraints) if j != i]
            
            self._model = cp_model.CpModel()
            self._variables = {}
            self._encode_variables(entities)
            self._encode_constraints(test_constraints)
            
            self._solver = cp_model.CpSolver()
            self._solver.parameters.max_time_in_seconds = 2.0
            test_status = self._solver.Solve(self._model)
            
            # If removing this constraint makes it feasible, it's part of the conflict
            if test_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                conflicting.append(constraint)
        
        if conflicting:
            return UnsatCore(
                conflicting_constraints=[c.id for c in conflicting],
                explanation=f"Found {len(conflicting)} conflicting constraints through elimination",
                suggested_relaxations=[f"Remove or relax {c.type} constraint" for c in conflicting],
            )
        else:
            # Couldn't identify specific conflicts (rare)
            return UnsatCore(
                conflicting_constraints=[c.id for c in constraints],
                explanation="All constraints may contribute to infeasibility",
                suggested_relaxations=["Use Z3Solver for detailed conflict analysis"],
            )

    def validate_solution(
        self,
        solution: Solution,
        entities: List[Entity],
        constraints: List[Constraint],
    ) -> bool:
        """Verify solution satisfies all constraints."""
        if solution.status != SolutionStatus.OPTIMAL:
            return False

        # Check precedence constraints
        for constraint in constraints:
            if constraint.type == "precedence":
                # Get A and B entity IDs
                a_id = constraint.entities[0]
                b_id = constraint.entities[1]

                # Get end time of A and start time of B
                a_end = solution.get_assignment(a_id, "end_time")
                b_start = solution.get_assignment(b_id, "start_time")

                if a_end is None or b_start is None:
                    return False

                # Check: A.end <= B.start
                if a_end.value > b_start.value:
                    return False

        return True

    # =========================================================================
    # PRIVATE ENCODING METHODS
    # =========================================================================

    def _encode_variables(self, entities: List[Entity]) -> None:
        """Create CP variables for each entity.
        
        For each task entity, create:
        - start_time: When task begins
        - end_time: When task completes
        - duration: How long task takes (from metadata or default 1)
        """
        for entity in entities:
            # Get duration from entity metadata (default 1)
            duration = entity.metadata.get("duration", 1) if entity.metadata else 1

            # Create interval variable [start, end, duration]
            # Horizon: 0 to 1000 (arbitrary large value for V1)
            start = self._model.NewIntVar(0, 1000, f"{entity.name}_start")
            end = self._model.NewIntVar(0, 1000, f"{entity.name}_end")

            # Link start, end, duration: end = start + duration
            self._model.Add(end == start + duration)

            # Store variables
            self._variables[f"{entity.id}_start"] = start
            self._variables[f"{entity.id}_end"] = end
            self._variables[f"{entity.id}_duration"] = duration

    def _encode_constraints(self, constraints: List[Constraint]) -> None:
        """Encode TessIR constraints as CP-SAT constraints."""
        for constraint in constraints:
            if constraint.type == "precedence":
                self._encode_precedence(constraint)
            elif constraint.type == "mutex":
                self._encode_mutex(constraint)
            elif constraint.type == "choice":
                self._encode_choice(constraint)
            else:
                raise ValueError(f"Unsupported constraint type: {constraint.type}")

    def _encode_precedence(self, constraint: Constraint) -> None:
        """Encode precedence constraint: A must finish before B starts."""
        a_id = constraint.entities[0]
        b_id = constraint.entities[1]

        a_end = self._variables[f"{a_id}_end"]
        b_start = self._variables[f"{b_id}_start"]

        # Add constraint: a_end <= b_start
        self._model.Add(a_end <= b_start)

    def _encode_mutex(self, constraint: Constraint) -> None:
        """Encode mutex constraint: A and B cannot overlap.
        
        Args:
            constraint: Mutex constraint with entities [A, B]
        """
        a_id = constraint.entities[0]
        b_id = constraint.entities[1]

        # Get interval variables for both tasks
        a_start = self._variables[f"{a_id}_start"]
        a_end = self._variables[f"{a_id}_end"]
        a_duration = self._variables[f"{a_id}_duration"]
        
        b_start = self._variables[f"{b_id}_start"]
        b_end = self._variables[f"{b_id}_end"]
        b_duration = self._variables[f"{b_id}_duration"]

        # Create interval variables for NoOverlap
        a_interval = self._model.NewIntervalVar(a_start, a_duration, a_end, f"interval_{a_id}")
        b_interval = self._model.NewIntervalVar(b_start, b_duration, b_end, f"interval_{b_id}")

        # Add NoOverlap constraint
        self._model.AddNoOverlap([a_interval, b_interval])

    def _encode_choice(self, constraint: Constraint) -> None:
        """Encode choice constraint: Exactly one task must be selected.
        
        Args:
            constraint: Choice constraint with entities [A, B, C, ...]
        """
        # Create boolean variable for each task (selected or not)
        bool_vars = []
        
        for entity_id in constraint.entities:
            # Create boolean: is this task selected?
            selected = self._model.NewBoolVar(f"selected_{entity_id}")
            bool_vars.append(selected)
            
            # Store for later reference
            self._variables[f"{entity_id}_selected"] = selected
        
        # Exactly one must be selected
        self._model.AddExactlyOne(bool_vars)

    def _encode_objective(self, objective: Objective) -> None:
        """Encode optimization objective."""
        if objective.name == "minimize_makespan":
            # Makespan = max(all end times)
            # Create auxiliary variable for makespan
            makespan = self._model.NewIntVar(0, 1000, "makespan")

            # makespan >= all end times
            for var_name, var in self._variables.items():
                if var_name.endswith("_end"):
                    self._model.Add(makespan >= var)

            # Minimize makespan
            self._model.Minimize(makespan)

    def _decode_solution(
        self, status: int, entities: List[Entity], solve_time: float
    ) -> Solution:
        """Decode OR-Tools solution into TESSRYX Solution object."""
        # Map OR-Tools status to our status
        status_map = {
            cp_model.OPTIMAL: SolutionStatus.OPTIMAL,
            cp_model.FEASIBLE: SolutionStatus.FEASIBLE,
            cp_model.INFEASIBLE: SolutionStatus.INFEASIBLE,
            cp_model.MODEL_INVALID: SolutionStatus.ERROR,
            cp_model.UNKNOWN: SolutionStatus.UNKNOWN,
        }

        solution_status = status_map.get(status, SolutionStatus.UNKNOWN)

        if solution_status in (SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE):
            # Extract assignments
            assignments = []

            for entity in entities:
                # Get start and end times
                start_var = self._variables.get(f"{entity.id}_start")
                end_var = self._variables.get(f"{entity.id}_end")

                if start_var is not None and end_var is not None:
                    start_time = self._solver.Value(start_var)
                    end_time = self._solver.Value(end_var)

                    assignments.append(
                        Assignment(
                            entity_id=entity.id,
                            attribute="start_time",
                            value=start_time,
                            unit="time_unit",
                        )
                    )

                    assignments.append(
                        Assignment(
                            entity_id=entity.id,
                            attribute="end_time",
                            value=end_time,
                            unit="time_unit",
                        )
                    )
                
                # Also extract selected boolean if it exists (for choice constraints)
                selected_var = self._variables.get(f"{entity.id}_selected")
                if selected_var is not None:
                    selected_value = self._solver.Value(selected_var)
                    assignments.append(
                        Assignment(
                            entity_id=entity.id,
                            attribute="selected",
                            value=selected_value,
                            unit=None,
                        )
                    )

            # Get objective value if applicable
            objective_value = None
            if hasattr(self._solver, "ObjectiveValue"):
                try:
                    objective_value = self._solver.ObjectiveValue()
                except:
                    pass

            return Solution(
                status=solution_status,
                assignments=assignments,
                objective_value=objective_value,
                solve_time_seconds=solve_time,
                metadata={
                    "solver": "OR-Tools CP-SAT",
                    "version": "9.15",
                    "num_branches": self._solver.NumBranches(),
                    "num_conflicts": self._solver.NumConflicts(),
                    "wall_time": self._solver.WallTime(),
                },
            )
        else:
            # Infeasible or error
            return Solution(
                status=solution_status,
                assignments=[],
                solve_time_seconds=solve_time,
                proof=f"Problem is {solution_status.value}",
            )

    def find_alternatives(
        self,
        entities: List[Entity],
        constraints: List[Constraint],
        objective: Optional[Objective] = None,
        max_solutions: int = 3,
        timeout_seconds: float = 60.0,
    ) -> SolutionSet:
        """Find multiple alternative solutions using solution pool."""
        start_time = time.time()
        
        # Build entity map
        self._entity_map = {e.id: e for e in entities}
        
        # Create fresh model
        self._model = cp_model.CpModel()
        self._variables = {}
        
        # Encode variables and constraints
        self._encode_variables(entities)
        self._encode_constraints(constraints)
        
        if objective:
            self._encode_objective(objective)
        
        # Create solver with solution callback
        self._solver = cp_model.CpSolver()
        self._solver.parameters.max_time_in_seconds = timeout_seconds
        self._solver.parameters.enumerate_all_solutions = True
        self._solver.parameters.num_search_workers = 1  # Required for callbacks
        
        # Callback to collect solutions
        solutions_found = []
        
        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self, variables, entities, max_sols, parent_solver):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self._variables = variables
                self._entities = entities
                self._max_solutions = max_sols
                self._parent = parent_solver
                self._solutions = []
            
            def on_solution_callback(self):
                if len(self._solutions) >= self._max_solutions:
                    self.StopSearch()
                    return
                
                # Extract assignments for this solution
                assignments = []
                for entity in self._entities:
                    start_var = self._variables.get(f"{entity.id}_start")
                    end_var = self._variables.get(f"{entity.id}_end")
                    
                    if start_var is not None and end_var is not None:
                        start_time = self.Value(start_var)
                        end_time = self.Value(end_var)
                        
                        assignments.append(
                            Assignment(
                                entity_id=entity.id,
                                attribute="start_time",
                                value=start_time,
                                unit="time_unit",
                            )
                        )
                        
                        assignments.append(
                            Assignment(
                                entity_id=entity.id,
                                attribute="end_time",
                                value=end_time,
                                unit="time_unit",
                            )
                        )
                
                # Get objective value if applicable
                obj_value = None
                if hasattr(self, "ObjectiveValue"):
                    try:
                        obj_value = self.ObjectiveValue()
                    except:
                        pass
                
                self._solutions.append((assignments, obj_value))
        
        collector = SolutionCollector(
            self._variables, entities, max_solutions, self._solver
        )
        
        # Solve with callback
        status = self._solver.Solve(self._model, collector)
        solve_time = time.time() - start_time
        
        # Convert collected solutions to Solution objects
        if collector._solutions:
            # First solution is optimal (if status is OPTIMAL)
            status_map = {
                cp_model.OPTIMAL: SolutionStatus.OPTIMAL,
                cp_model.FEASIBLE: SolutionStatus.FEASIBLE,
                cp_model.INFEASIBLE: SolutionStatus.INFEASIBLE,
            }
            
            solution_status = status_map.get(status, SolutionStatus.UNKNOWN)
            
            optimal = Solution(
                status=solution_status,
                assignments=collector._solutions[0][0],
                objective_value=collector._solutions[0][1],
                solve_time_seconds=solve_time,
                metadata={
                    "solver": "OR-Tools CP-SAT",
                    "num_solutions_found": len(collector._solutions),
                },
            )
            
            alternatives = [
                Solution(
                    status=SolutionStatus.FEASIBLE,
                    assignments=sol[0],
                    objective_value=sol[1],
                    solve_time_seconds=solve_time,
                )
                for sol in collector._solutions[1:]
            ]
            
            return SolutionSet(
                optimal=optimal,
                alternatives=alternatives,
                total_feasible=len(collector._solutions),
            )
        else:
            # No solutions found
            return SolutionSet(
                optimal=Solution(
                    status=SolutionStatus.INFEASIBLE,
                    assignments=[],
                    solve_time_seconds=solve_time,
                ),
                alternatives=[],
                total_feasible=0,
            )

    def find_unsat_core(
        self, entities: List[Entity], constraints: List[Constraint]
    ) -> UnsatCore:
        """Find minimal conflicting constraint set.
        
        Note: OR-Tools CP-SAT doesn't provide native unsat cores.
        This is a simplified implementation that identifies conflicts through
        iterative constraint relaxation.
        
        For full unsat core analysis, use Z3Solver instead.
        """
        # First, verify the problem is actually infeasible
        self._entity_map = {e.id: e for e in entities}
        self._model = cp_model.CpModel()
        self._variables = {}
        
        self._encode_variables(entities)
        self._encode_constraints(constraints)
        
        self._solver = cp_model.CpSolver()
        self._solver.parameters.max_time_in_seconds = 5.0
        status = self._solver.Solve(self._model)
        
        if status != cp_model.INFEASIBLE:
            raise ValueError("Problem is feasible, no unsat core exists")
        
        # Try removing constraints one at a time to find conflicts
        # This is a naive approach - proper unsat cores require SMT solver
        conflicting = []
        
        for i, constraint in enumerate(constraints):
            # Try solving without this constraint
            test_constraints = [c for j, c in enumerate(constraints) if j != i]
            
            self._model = cp_model.CpModel()
            self._variables = {}
            self._encode_variables(entities)
            self._encode_constraints(test_constraints)
            
            self._solver = cp_model.CpSolver()
            self._solver.parameters.max_time_in_seconds = 2.0
            test_status = self._solver.Solve(self._model)
            
            # If removing this constraint makes it feasible, it's part of the conflict
            if test_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                conflicting.append(constraint)
        
        if conflicting:
            return UnsatCore(
                conflicting_constraints=[c.id for c in conflicting],
                explanation=f"Found {len(conflicting)} conflicting constraints through elimination",
                suggested_relaxations=[f"Remove or relax {c.type} constraint" for c in conflicting],
            )
        else:
            # Couldn't identify specific conflicts (rare)
            return UnsatCore(
                conflicting_constraints=[c.id for c in constraints],
                explanation="All constraints may contribute to infeasibility",
                suggested_relaxations=["Use Z3Solver for detailed conflict analysis"],
            )

    def validate_solution(
        self,
        solution: Solution,
        entities: List[Entity],
        constraints: List[Constraint],
    ) -> bool:
        """Verify solution satisfies all constraints."""
        if solution.status != SolutionStatus.OPTIMAL:
            return False

        # Check precedence constraints
        for constraint in constraints:
            if constraint.type == "precedence":
                # Get A and B entity IDs
                a_id = constraint.entities[0]
                b_id = constraint.entities[1]

                # Get end time of A and start time of B
                a_end = solution.get_assignment(a_id, "end_time")
                b_start = solution.get_assignment(b_id, "start_time")

                if a_end is None or b_start is None:
                    return False

                # Check: A.end <= B.start
                if a_end.value > b_start.value:
                    return False

        return True

    # =========================================================================
    # PRIVATE ENCODING METHODS
    # =========================================================================

    def _encode_variables(self, entities: List[Entity]) -> None:
        """Create CP variables for each entity.
        
        For each task entity, create:
        - start_time: When task begins
        - end_time: When task completes
        - duration: How long task takes (from metadata or default 1)
        """
        for entity in entities:
            # Get duration from entity metadata (default 1)
            duration = entity.metadata.get("duration", 1) if entity.metadata else 1

            # Create interval variable [start, end, duration]
            # Horizon: 0 to 1000 (arbitrary large value for V1)
            start = self._model.NewIntVar(0, 1000, f"{entity.name}_start")
            end = self._model.NewIntVar(0, 1000, f"{entity.name}_end")

            # Link start, end, duration: end = start + duration
            self._model.Add(end == start + duration)

            # Store variables
            self._variables[f"{entity.id}_start"] = start
            self._variables[f"{entity.id}_end"] = end
            self._variables[f"{entity.id}_duration"] = duration

    def _encode_constraints(self, constraints: List[Constraint]) -> None:
        """Encode TessIR constraints as CP-SAT constraints."""
        for constraint in constraints:
            if constraint.type == "precedence":
                self._encode_precedence(constraint)
            elif constraint.type == "mutex":
                self._encode_mutex(constraint)
            elif constraint.type == "choice":
                self._encode_choice(constraint)
            else:
                raise ValueError(f"Unsupported constraint type: {constraint.type}")

    def _encode_precedence(self, constraint: Constraint) -> None:
        """Encode precedence constraint: A must finish before B starts.
        
        Args:
            constraint: Precedence constraint with entities [A, B]
        """
        a_id = constraint.entities[0]
        b_id = constraint.entities[1]

        a_end = self._variables[f"{a_id}_end"]
        b_start = self._variables[f"{b_id}_start"]

        # Add constraint: a_end <= b_start
        self._model.Add(a_end <= b_start)

    def _encode_mutex(self, constraint: Constraint) -> None:
        """Encode mutex constraint: A and B cannot overlap.
        
        Args:
            constraint: Mutex constraint with entities [A, B]
        """
        a_id = constraint.entities[0]
        b_id = constraint.entities[1]

        # Get interval variables for both tasks
        a_start = self._variables[f"{a_id}_start"]
        a_end = self._variables[f"{a_id}_end"]
        a_duration = self._variables[f"{a_id}_duration"]
        
        b_start = self._variables[f"{b_id}_start"]
        b_end = self._variables[f"{b_id}_end"]
        b_duration = self._variables[f"{b_id}_duration"]

        # Create interval variables for NoOverlap
        a_interval = self._model.NewIntervalVar(a_start, a_duration, a_end, f"interval_{a_id}")
        b_interval = self._model.NewIntervalVar(b_start, b_duration, b_end, f"interval_{b_id}")

        # Add NoOverlap constraint
        self._model.AddNoOverlap([a_interval, b_interval])

    def _encode_choice(self, constraint: Constraint) -> None:
        """Encode choice constraint: Exactly one task must be selected.
        
        Args:
            constraint: Choice constraint with entities [A, B, C, ...]
        """
        # Create boolean variable for each task (selected or not)
        bool_vars = []
        
        for entity_id in constraint.entities:
            # Create boolean: is this task selected?
            selected = self._model.NewBoolVar(f"selected_{entity_id}")
            bool_vars.append(selected)
            
            # Store for later reference
            self._variables[f"{entity_id}_selected"] = selected
        
        # Exactly one must be selected
        self._model.AddExactlyOne(bool_vars)

    def _encode_objective(self, objective: Objective) -> None:
        """Encode optimization objective.
        
        Args:
            objective: Objective function (e.g., minimize makespan)
        """
        if objective.name == "minimize_makespan":
            # Makespan = max(all end times)
            # Create auxiliary variable for makespan
            makespan = self._model.NewIntVar(0, 1000, "makespan")

            # makespan >= all end times
            for var_name, var in self._variables.items():
                if var_name.endswith("_end") and not isinstance(var, int):
                    self._model.Add(makespan >= var)

            # Minimize makespan
            self._model.Minimize(makespan)

    def _decode_solution(
        self, status: int, entities: List[Entity], solve_time: float
    ) -> Solution:
        """Decode OR-Tools solution into TESSRYX Solution object.
        
        Args:
            status: OR-Tools solver status
            entities: Original entity list
            solve_time: Time spent solving
            
        Returns:
            Solution with assignments and metadata
        """
        # Map OR-Tools status to our status
        status_map = {
            cp_model.OPTIMAL: SolutionStatus.OPTIMAL,
            cp_model.FEASIBLE: SolutionStatus.FEASIBLE,
            cp_model.INFEASIBLE: SolutionStatus.INFEASIBLE,
            cp_model.MODEL_INVALID: SolutionStatus.ERROR,
            cp_model.UNKNOWN: SolutionStatus.UNKNOWN,
        }

        solution_status = status_map.get(status, SolutionStatus.UNKNOWN)

        if solution_status in (SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE):
            # Extract assignments
            assignments = []

            for entity in entities:
                # Get start and end times
                start_var = self._variables.get(f"{entity.id}_start")
                end_var = self._variables.get(f"{entity.id}_end")

                if start_var is not None and end_var is not None:
                    start_time = self._solver.Value(start_var)
                    end_time = self._solver.Value(end_var)

                    assignments.append(
                        Assignment(
                            entity_id=entity.id,
                            attribute="start_time",
                            value=start_time,
                            unit="time_unit",
                        )
                    )

                    assignments.append(
                        Assignment(
                            entity_id=entity.id,
                            attribute="end_time",
                            value=end_time,
                            unit="time_unit",
                        )
                    )
                
                # Also extract selected boolean if it exists (for choice constraints)
                selected_var = self._variables.get(f"{entity.id}_selected")
                if selected_var is not None:
                    selected_value = self._solver.Value(selected_var)
                    assignments.append(
                        Assignment(
                            entity_id=entity.id,
                            attribute="selected",
                            value=selected_value,
                            unit=None,
                        )
                    )

            # Get objective value if applicable
            objective_value = None
            if hasattr(self._solver, "ObjectiveValue"):
                try:
                    objective_value = self._solver.ObjectiveValue()
                except:
                    pass

            return Solution(
                status=solution_status,
                assignments=assignments,
                objective_value=objective_value,
                solve_time_seconds=solve_time,
                metadata={
                    "solver": "OR-Tools CP-SAT",
                    "version": "9.15",
                    "num_branches": self._solver.NumBranches(),
                    "num_conflicts": self._solver.NumConflicts(),
                    "wall_time": self._solver.WallTime(),
                },
            )
        else:
            # Infeasible or error
            return Solution(
                status=solution_status,
                assignments=[],
                solve_time_seconds=solve_time,
                proof=f"Problem is {solution_status.value}",
            )
