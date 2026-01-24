"""Abstract solver interface for constraint satisfaction and optimization.

This module defines the core abstractions that all TESSRYX solvers must implement.
Solvers transform TessIR constraints into actionable plans through optimization.

Design Philosophy:
- Solver-agnostic interface (swap OR-Tools, Z3, custom solvers)
- Type-safe encoding/decoding
- Rich solution metadata (proof, alternatives, explanation)
- Performance-conscious (lazy evaluation, caching)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from tessryx.core.constraint import Constraint
from tessryx.core.entity import Entity


# =============================================================================
# SOLUTION STATUS
# =============================================================================


class SolutionStatus(str, Enum):
    """Status of solver execution."""

    OPTIMAL = "optimal"  # Found provably optimal solution
    FEASIBLE = "feasible"  # Found valid solution (may not be optimal)
    INFEASIBLE = "infeasible"  # No valid solution exists
    UNKNOWN = "unknown"  # Solver couldn't determine
    TIMEOUT = "timeout"  # Exceeded time limit
    ERROR = "error"  # Solver error


# =============================================================================
# SOLUTION REPRESENTATION
# =============================================================================


@dataclass(frozen=True)
class Assignment:
    """A single variable assignment in the solution.
    
    Examples:
        >>> Assignment(
        ...     entity_id=uuid4(),
        ...     attribute="start_time",
        ...     value=100,
        ...     unit="seconds"
        ... )
    """

    entity_id: UUID
    attribute: str  # e.g., "start_time", "selected_version", "assigned_worker"
    value: Any  # The assigned value
    unit: Optional[str] = None  # Optional unit (for time, cost, etc.)


@dataclass(frozen=True)
class Solution:
    """A complete solution from the solver.
    
    Contains:
    - Status (optimal, feasible, infeasible, etc.)
    - Variable assignments (if feasible)
    - Objective value (if applicable)
    - Proof/explanation
    - Solver statistics
    
    Examples:
        >>> solution = Solution(
        ...     status=SolutionStatus.OPTIMAL,
        ...     assignments=[...],
        ...     objective_value=42.0,
        ...     objective_name="minimize_time"
        ... )
    """

    status: SolutionStatus
    assignments: List[Assignment]
    objective_value: Optional[float] = None
    objective_name: Optional[str] = None
    solve_time_seconds: float = 0.0
    proof: Optional[str] = None  # Human-readable explanation
    metadata: Dict[str, Any] = None  # Solver-specific metadata

    def __post_init__(self) -> None:
        """Validate solution consistency."""
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

        # Feasible/optimal solutions must have assignments
        if self.status in (SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE):
            if not self.assignments:
                raise ValueError(
                    f"Status {self.status} requires non-empty assignments"
                )

    def get_assignment(
        self, entity_id: UUID, attribute: str
    ) -> Optional[Assignment]:
        """Get assignment for specific entity and attribute."""
        for assignment in self.assignments:
            if (
                assignment.entity_id == entity_id
                and assignment.attribute == attribute
            ):
                return assignment
        return None

    def get_entity_assignments(self, entity_id: UUID) -> List[Assignment]:
        """Get all assignments for a specific entity."""
        return [a for a in self.assignments if a.entity_id == entity_id]


@dataclass(frozen=True)
class SolutionSet:
    """Multiple solutions (e.g., N best alternatives).
    
    Examples:
        >>> solution_set = SolutionSet(
        ...     optimal=solution1,
        ...     alternatives=[solution2, solution3],
        ...     total_feasible=10  # Found 10 feasible, returning top 3
        ... )
    """

    optimal: Solution  # Best solution found
    alternatives: List[Solution]  # Other good solutions
    total_feasible: int = 1  # Total number of feasible solutions found


# =============================================================================
# OBJECTIVE FUNCTIONS
# =============================================================================


@dataclass(frozen=True)
class Objective:
    """Optimization objective.
    
    Examples:
        >>> Objective(
        ...     name="minimize_time",
        ...     direction="minimize",
        ...     expression="max(task.end_time)"
        ... )
    """

    name: str
    direction: str  # "minimize" or "maximize"
    expression: str  # Solver-specific expression
    weight: float = 1.0  # For multi-objective optimization


# =============================================================================
# MINIMAL UNSAT CORE
# =============================================================================


@dataclass(frozen=True)
class UnsatCore:
    """Minimal conflicting constraint set (when infeasible).
    
    This is the smallest subset of constraints that makes the problem unsolvable.
    Removing any one constraint from the core makes the problem feasible.
    
    Examples:
        >>> core = UnsatCore(
        ...     conflicting_constraints=[constraint1.id, constraint2.id],
        ...     explanation="Task A must start before B, but B must start before A",
        ...     suggested_relaxations=["Remove precedence A→B", "Remove precedence B→A"]
        ... )
    """

    conflicting_constraints: List[UUID]  # IDs of conflicting constraints
    explanation: str  # Human-readable conflict description
    suggested_relaxations: List[str]  # Actionable suggestions


# =============================================================================
# ABSTRACT SOLVER INTERFACE
# =============================================================================


class Solver(ABC):
    """Abstract base class for all constraint solvers.
    
    Implementations:
    - ORToolsSolver: Google OR-Tools CP-SAT (discrete optimization)
    - Z3Solver: Microsoft Z3 SMT (logical constraints, verification)
    - CustomSolver: Domain-specific heuristics
    
    Examples:
        >>> solver = ORToolsSolver()
        >>> solution = solver.solve(
        ...     entities=[task_a, task_b, task_c],
        ...     constraints=[precedence_ab, precedence_bc],
        ...     objective=Objective("minimize_time", "minimize", "makespan")
        ... )
        >>> if solution.status == SolutionStatus.OPTIMAL:
        ...     print(f"Optimal time: {solution.objective_value}")
    """

    @abstractmethod
    def solve(
        self,
        entities: List[Entity],
        constraints: List[Constraint],
        objective: Optional[Objective] = None,
        timeout_seconds: float = 60.0,
    ) -> Solution:
        """Solve the constraint satisfaction problem.
        
        Args:
            entities: Entities to assign/schedule
            constraints: Constraints to satisfy
            objective: Optimization objective (optional)
            timeout_seconds: Maximum solve time
            
        Returns:
            Solution with status, assignments, and metadata
            
        Raises:
            ValueError: Invalid input (e.g., unknown constraint type)
            TimeoutError: Solver exceeded timeout
        """
        pass

    @abstractmethod
    def find_alternatives(
        self,
        entities: List[Entity],
        constraints: List[Constraint],
        objective: Optional[Objective] = None,
        max_solutions: int = 3,
        timeout_seconds: float = 60.0,
    ) -> SolutionSet:
        """Find multiple alternative solutions.
        
        Returns N best solutions, ranked by objective value.
        
        Args:
            entities: Entities to assign/schedule
            constraints: Constraints to satisfy
            objective: Optimization objective (optional)
            max_solutions: Maximum number of solutions to return
            timeout_seconds: Maximum solve time
            
        Returns:
            SolutionSet with optimal solution and alternatives
        """
        pass

    @abstractmethod
    def find_unsat_core(
        self, entities: List[Entity], constraints: List[Constraint]
    ) -> UnsatCore:
        """Find minimal conflicting constraint set (when infeasible).
        
        Args:
            entities: Entities involved
            constraints: Constraints to analyze
            
        Returns:
            UnsatCore with conflicting constraints and suggestions
            
        Raises:
            ValueError: Problem is actually feasible
        """
        pass

    @abstractmethod
    def validate_solution(
        self,
        solution: Solution,
        entities: List[Entity],
        constraints: List[Constraint],
    ) -> bool:
        """Verify that a solution satisfies all constraints.
        
        Args:
            solution: Solution to validate
            entities: Entities involved
            constraints: Constraints to check
            
        Returns:
            True if solution is valid, False otherwise
        """
        pass

    def get_capabilities(self) -> Set[str]:
        """Return set of constraint types this solver supports.
        
        Examples: {"precedence", "mutex", "choice", "capacity", "time_window"}
        """
        return set()

    def get_metadata(self) -> Dict[str, Any]:
        """Return solver metadata (version, capabilities, etc.)."""
        return {
            "solver_name": self.__class__.__name__,
            "capabilities": list(self.get_capabilities()),
        }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def validate_constraints_for_solver(
    constraints: List[Constraint], solver: Solver
) -> List[str]:
    """Check if all constraints are supported by the solver.
    
    Args:
        constraints: Constraints to validate
        solver: Solver to check against
        
    Returns:
        List of unsupported constraint types (empty if all supported)
    """
    capabilities = solver.get_capabilities()
    unsupported = []

    for constraint in constraints:
        if constraint.type not in capabilities:
            unsupported.append(constraint.type)

    return list(set(unsupported))  # Remove duplicates
