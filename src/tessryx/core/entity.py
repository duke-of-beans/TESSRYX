"""Entity primitive - discrete units that participate in dependencies."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from tessryx.core.types import EntityID, Metadata


class EntityType(str, Enum):
    """Base entity types (universal across domains)."""

    COMPONENT = "component"  # Generic building block
    RESOURCE = "resource"  # Consumable or capacity-limited
    TASK = "task"  # Work item or process step
    GATE = "gate"  # Checkpoint or decision point


class Entity(BaseModel):
    """A discrete unit that can participate in dependencies.

    Entities are immutable once created (frozen=True). Any changes require
    creating a new entity with updated fields.

    Examples:
        >>> from uuid import uuid4
        >>> entity = Entity(
        ...     id=uuid4(),
        ...     type="component",
        ...     name="react",
        ...     version="18.2.0"
        ... )
        >>> entity.name
        'react'
    """

    id: EntityID = Field(
        ...,
        description="Unique identifier (UUID)",
    )

    type: str = Field(
        ...,
        description="Entity type (domain-specific or base type)",
        min_length=1,
        max_length=50,
    )

    name: str = Field(
        ...,
        description="Human-readable name",
        min_length=1,
    )

    version: str | None = Field(
        default=None,
        description="Optional version string",
    )

    parent: EntityID | None = Field(
        default=None,
        description="Parent entity for hierarchical composition",
    )

    children: list[EntityID] = Field(
        default_factory=list,
        description="Child entities (for bundles/containers)",
    )

    metadata: Metadata = Field(
        default_factory=dict,
        description="Extensible properties (domain-specific)",
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
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "type": "package",
                    "name": "express",
                    "version": "4.18.2",
                    "metadata": {"language": "javascript", "license": "MIT"},
                }
            ]
        },
    }

    def __str__(self) -> str:
        """Human-readable string representation."""
        version_str = f"@{self.version}" if self.version else ""
        return f"{self.name}{version_str} ({self.type})"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Entity(id={self.id}, type={self.type!r}, name={self.name!r})"

    def has_parent(self) -> bool:
        """Check if entity has a parent (hierarchical composition)."""
        return self.parent is not None

    def has_children(self) -> bool:
        """Check if entity has children (is a container)."""
        return len(self.children) > 0

    def is_leaf(self) -> bool:
        """Check if entity is a leaf node (no children)."""
        return not self.has_children()
