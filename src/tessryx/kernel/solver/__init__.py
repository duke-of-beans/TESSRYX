"""TESSRYX Solver Module - Constraint satisfaction and optimization.

This module provides the solver infrastructure for transforming dependency
constraints into actionable plans.

Core Components:
- base: Abstract solver interface
- or_tools_adapter: Google OR-Tools CP-SAT (discrete optimization)
- z3_adapter: Microsoft Z3 SMT (logical constraints, verification)
- encoder: TessIR → Solver encoding layer

Usage:
    >>> from tessryx.kernel.solver import ORToolsSolver, Objective
    >>> solver = ORToolsSolver()
    >>> solution = solver.solve(
    ...     entities=tasks,
    ...     constraints=precedence_constraints,
    ...     objective=Objective("minimize_time", "minimize", "makespan")
    ... )
"""

from tessryx.kernel.solver.base import (
    Assignment,
    Objective,
    Solution,
    SolutionSet,
    SolutionStatus,
    Solver,
    UnsatCore,
    validate_constraints_for_solver,
)
from tessryx.kernel.solver.or_tools_adapter import ORToolsSolver

__all__ = [
    # Base abstractions
    "Solver",
    "Solution",
    "SolutionSet",
    "SolutionStatus",
    "Assignment",
    "Objective",
    "UnsatCore",
    # Implementations
    "ORToolsSolver",
    # Utilities
    "validate_constraints_for_solver",
]
