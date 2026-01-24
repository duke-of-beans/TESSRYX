"""Constraint primitive - first-class rules governing valid states and sequences."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from tessryx.core.types import ConstraintID, EntityID, Metadata


class Priority(str, Enum):
    """Constraint priority levels (solver behavior)."""

    HARD = "hard"  # MUST be satisfied (infeasible if violated)
    SOFT = "soft"  # SHOULD be satisfied (optimize to minimize violations)
    PREFERENCE = "pref"  # NICE to satisfy (lowest priority, tiebreaker)


class ConstraintType(str, Enum):
    """Core constraint types from taxonomy.

    Categories:
    - Temporal (T): Timing, sequencing, scheduling
    - Resource (R): Allocation, capacity, budgets
    - Logical (L): Boolean relationships, choices
    - Structural (S): Hierarchies, composition, interfaces
    """

    # Temporal Constraints (8 types)
    PRECEDENCE = "precedence"  # T1: A must complete before B starts
    TIME_WINDOW = "time_window"  # T2: Entity must occur within bounds
    DURATION = "duration"  # T3: Entity must take specified time
    DEADLINE = "deadline"  # T4: Hard completion cutoff
    DELAY = "delay"  # T5: Minimum gap between events
    SYNCHRONIZATION = "synchronization"  # T6: Simultaneous occurrence
    RECURRENCE = "recurrence"  # T7: Repeating schedule
    EXPIRATION = "expiration"  # T8: Validity ends at time

    # Resource Constraints (8 types)
    RESOURCE_CAPACITY = "resource_capacity"  # R1: Maximum concurrent usage
    RESOURCE_ALLOCATION = "resource_allocation"  # R2: Assign quantity to task
    RESOURCE_SHARING = "resource_sharing"  # R3: Shared allocation
    BUDGET = "budget"  # R4: Total cost constraint
    THROUGHPUT = "throughput"  # R5: Rate limiting
    RESERVATION = "reservation"  # R6: Exclusive access period
    UTILIZATION = "utilization"  # R7: Min/max usage percentage
    DEPENDENCY_QUOTA = "dependency_quota"  # R8: Limit complexity

    # Logical Constraints (7 types)
    MUTEX = "mutex"  # L1: Mutual exclusion (cannot co-occur)
    CHOICE = "choice"  # L2: Select exactly N of M
    CONDITIONAL = "conditional"  # L3: If-then rule
    IMPLICATION = "implication"  # L4: If A then B must occur
    EQUIVALENCE = "equivalence"  # L5: A if and only if B
    DISJUNCTION = "disjunction"  # L6: At least one must occur (OR)
    NEGATION = "negation"  # L7: Entity must not occur (prohibition)

    # Structural Constraints (5 types)
    HIERARCHY = "hierarchy"  # S1: Parent-child ordering
    COMPOSITION = "composition"  # S2: Whole requires all parts
    ENCAPSULATION = "encapsulation"  # S3: Internal entities hidden
    INTERFACE_COMPATIBILITY = "interface_compatibility"  # S4: Type checking
    CARDINALITY = "cardinality"  # S5: Relationship count constraints


class Constraint(BaseModel):
    """First-class rule governing valid entity states or sequences.

    Constraints are immutable once created. They can be context-dependent via
    the scope field (applies only when conditions are met).

    Examples:
        >>> from uuid import uuid4
        >>> constraint = Constraint(
        ...     id=uuid4(),
        ...     type="precedence",
        ...     entities=[uuid4(), uuid4()],
        ...     parameters={"before": "entity_a", "after": "entity_b"},
        ...     priority="hard"
        ... )
        >>> constraint.is_hard()
        True
    """

    id: ConstraintID = Field(
        ...,
        description="Unique identifier (UUID)",
    )

    type: str = Field(
        ...,
        description="Constraint type (from taxonomy)",
        min_length=1,
        max_length=50,
    )

    entities: list[EntityID] = Field(
        ...,
        description="Entities involved in this constraint",
        min_length=1,
    )

    parameters: dict[str, Any] = Field(
        ...,
        description="Type-specific parameters (e.g., min_gap for precedence)",
    )

    priority: Priority = Field(
        default=Priority.HARD,
        description="Constraint priority (hard, soft, preference)",
    )

    provenance: Metadata | None = Field(
        default=None,
        description="Evidence and confidence metadata",
    )

    scope: Metadata | None = Field(
        default=None,
        description="Context where this constraint applies (optional)",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC)",
    )

    model_config = {
        "frozen": True,  # Immutable
        "json_schema_extra": {
            "examples": [
                {
                    "id": "c1c2c3c4-d5d6-7890-abcd-ef1234567890",
                    "type": "precedence",
                    "entities": [
                        "550e8400-e29b-41d4-a716-446655440000",
                        "660e8400-e29b-41d4-a716-446655440111",
                    ],
                    "parameters": {"before": "entity_a", "after": "entity_b"},
                    "priority": "hard",
                }
            ]
        },
    }

    def __str__(self) -> str:
        """Human-readable string representation."""
        entity_count = len(self.entities)
        return f"{self.type} constraint ({entity_count} entities, {self.priority})"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Constraint(id={self.id}, type={self.type!r}, "
            f"entities={len(self.entities)}, priority={self.priority})"
        )

    def is_hard(self) -> bool:
        """Check if constraint is hard (must be satisfied)."""
        return self.priority == Priority.HARD

    def is_soft(self) -> bool:
        """Check if constraint is soft (should be satisfied)."""
        return self.priority == Priority.SOFT

    def is_preference(self) -> bool:
        """Check if constraint is preference (nice to have)."""
        return self.priority == Priority.PREFERENCE

    def is_temporal(self) -> bool:
        """Check if constraint is temporal (timing/sequencing)."""
        temporal_types = {
            "precedence",
            "time_window",
            "duration",
            "deadline",
            "delay",
            "synchronization",
            "recurrence",
            "expiration",
        }
        return self.type in temporal_types

    def is_resource(self) -> bool:
        """Check if constraint is resource-related (allocation/capacity)."""
        resource_types = {
            "resource_capacity",
            "resource_allocation",
            "resource_sharing",
            "budget",
            "throughput",
            "reservation",
            "utilization",
            "dependency_quota",
        }
        return self.type in resource_types

    def is_logical(self) -> bool:
        """Check if constraint is logical (boolean relationships)."""
        logical_types = {
            "mutex",
            "choice",
            "conditional",
            "implication",
            "equivalence",
            "disjunction",
            "negation",
        }
        return self.type in logical_types

    def is_structural(self) -> bool:
        """Check if constraint is structural (hierarchies/composition)."""
        structural_types = {
            "hierarchy",
            "composition",
            "encapsulation",
            "interface_compatibility",
            "cardinality",
        }
        return self.type in structural_types
