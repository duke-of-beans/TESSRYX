"""Core TessIR primitives."""

from tessryx.core.constraint import Constraint, ConstraintType, Priority
from tessryx.core.entity import Entity, EntityType
from tessryx.core.provenance import Evidence, Provenance, Source
from tessryx.core.relation import Relation, RelationType

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
