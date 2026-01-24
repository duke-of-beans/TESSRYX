"""Relation primitive - typed connections between entities."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from tessryx.core.types import EntityID, RelationID


class RelationType(str, Enum):
    """Core relation types (universal across domains)."""

    # Dependency Relations
    REQUIRES = "requires"  # A needs B to function
    ENABLES = "enables"  # A makes B possible
    BLOCKS = "blocks"  # A prevents B
    CONFLICTS = "conflicts"  # A and B are mutually exclusive

    # Temporal Relations
    PRECEDES = "precedes"  # A must happen before B
    FOLLOWS = "follows"  # A must happen after B
    CONCURRENT = "concurrent"  # A and B can/must happen simultaneously

    # Compositional Relations
    CONTAINS = "contains"  # A is composed of B
    PART_OF = "part_of"  # Inverse of contains
    REPLACES = "replaces"  # A is a substitute for B


class Relation(BaseModel):
    """A typed connection between entities representing a dependency relationship.

    Relations are immutable once created. Strength represents confidence or
    probabilistic weight (1.0 = hard dependency, 0.0-0.99 = soft/probabilistic).

    Examples:
        >>> from uuid import uuid4
        >>> rel = Relation(
        ...     id=uuid4(),
        ...     type="requires",
        ...     from_entity=uuid4(),
        ...     to_entity=uuid4(),
        ...     strength=0.95
        ... )
        >>> rel.is_hard_dependency()
        True
    """

    id: RelationID = Field(
        ...,
        description="Unique identifier (UUID)",
    )

    type: str = Field(
        ...,
        description="Semantic relationship type",
        min_length=1,
        max_length=50,
    )

    from_entity: EntityID = Field(
        ...,
        description="Source entity ID",
    )

    to_entity: EntityID = Field(
        ...,
        description="Target entity ID",
    )

    strength: float = Field(
        default=1.0,
        description="Dependency strength (0.0-1.0, where 1.0 = deterministic)",
        ge=0.0,
        le=1.0,
    )

    contract: dict[str, list[str]] | None = Field(
        default=None,
        description="Rich dependency contract (preconditions, postconditions, invariants)",
    )

    provenance: dict[str, float] | None = Field(
        default=None,
        description="Evidence and confidence metadata",
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC)",
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC)",
    )

    model_config = {
        "frozen": True,  # Immutable
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "type": "requires",
                    "from_entity": "550e8400-e29b-41d4-a716-446655440000",
                    "to_entity": "660e8400-e29b-41d4-a716-446655440111",
                    "strength": 1.0,
                    "provenance": {"confidence": 0.95},
                }
            ]
        },
    }

    @field_validator("from_entity", "to_entity", mode="before")
    @classmethod
    def validate_different_entities(cls, v: EntityID) -> EntityID:
        """Ensure from_entity != to_entity (no self-loops).
        
        Note: This validator runs before the model is fully constructed,
        so we can't check both fields here. The full check happens in 
        model_validator below.
        """
        return v

    def model_post_init(self, __context: object) -> None:
        """Validate after all fields are set."""
        if self.from_entity == self.to_entity:
            raise ValueError("Relation cannot connect entity to itself (self-loop)")

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.from_entity} --[{self.type}]--> {self.to_entity}"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Relation(id={self.id}, type={self.type!r}, "
            f"from={self.from_entity}, to={self.to_entity}, strength={self.strength})"
        )

    def is_hard_dependency(self) -> bool:
        """Check if this is a hard (deterministic) dependency."""
        return self.strength == 1.0

    def is_soft_dependency(self) -> bool:
        """Check if this is a soft (probabilistic) dependency."""
        return 0.0 < self.strength < 1.0

    def is_weak_dependency(self) -> bool:
        """Check if this is a weak dependency (strength < 0.5)."""
        return self.strength < 0.5

    def confidence(self) -> float:
        """Extract confidence score from provenance if available."""
        if self.provenance and "confidence" in self.provenance:
            return self.provenance["confidence"]
        return self.strength  # Fallback to strength
