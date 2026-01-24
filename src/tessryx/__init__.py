"""TESSRYX - Universal Dependency Intelligence Infrastructure.

TessIR implementation with constraint solving, provenance tracking, and graph operations.
"""

__version__ = "0.1.0"

from tessryx.core.entity import Entity, EntityType
from tessryx.core.relation import Relation, RelationType
from tessryx.core.constraint import Constraint, ConstraintType, Priority
from tessryx.core.provenance import Provenance, Source, Evidence

__all__ = [
    "Entity",
    "EntityType",
    "Relation",
    "RelationType",
    "Constraint",
    "ConstraintType",
    "Priority",
    "Provenance",
    "Source",
    "Evidence",
]
