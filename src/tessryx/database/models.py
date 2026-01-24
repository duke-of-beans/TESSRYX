"""SQLAlchemy database models for TessIR primitives."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class EntityModel(Base):
    """Entity table - discrete units with hierarchical composition."""

    __tablename__ = "entities"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Core fields
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Hierarchy
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True
    )
    children_ids: Mapped[list[UUID]] = mapped_column(JSON, default=list)
    
    # Metadata
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    parent: Mapped["EntityModel | None"] = relationship(
        "EntityModel",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[list["EntityModel"]] = relationship(
        "EntityModel",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_entity_type", "type"),
        Index("idx_entity_name", "name"),
        Index("idx_entity_parent", "parent_id"),
        CheckConstraint("name != ''", name="entity_name_not_empty"),
        CheckConstraint("length(type) <= 100", name="entity_type_length"),
    )


class RelationModel(Base):
    """Relation table - typed connections between entities."""

    __tablename__ = "relations"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Core fields
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    from_entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False
    )
    to_entity_id: Mapped[UUID] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False
    )
    strength: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Optional fields
    contract: Mapped[dict[str, list[str]] | None] = mapped_column(JSON, nullable=True)
    provenance: Mapped[dict[str, float] | None] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    from_entity: Mapped[EntityModel] = relationship(
        "EntityModel",
        foreign_keys=[from_entity_id]
    )
    to_entity: Mapped[EntityModel] = relationship(
        "EntityModel",
        foreign_keys=[to_entity_id]
    )

    # Indexes for graph queries
    __table_args__ = (
        Index("idx_relation_from", "from_entity_id"),
        Index("idx_relation_to", "to_entity_id"),
        Index("idx_relation_type", "type"),
        Index("idx_relation_strength", "strength"),
        CheckConstraint("from_entity_id != to_entity_id", name="no_self_loops"),
        CheckConstraint("strength >= 0.0 AND strength <= 1.0", name="strength_bounds"),
        CheckConstraint("type != ''", name="relation_type_not_empty"),
        CheckConstraint("length(type) <= 100", name="relation_type_length"),
    )


class ConstraintModel(Base):
    """Constraint table - requirements and rules."""

    __tablename__ = "constraints"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Core fields
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    entities: Mapped[list[UUID]] = mapped_column(JSON, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Optional fields
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provenance: Mapped[dict[str, float] | None] = mapped_column(JSON, nullable=True)
    scope: Mapped[dict[str, list[str]] | None] = mapped_column(JSON, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_constraint_type", "type"),
        Index("idx_constraint_priority", "priority"),
        CheckConstraint("type != ''", name="constraint_type_not_empty"),
        CheckConstraint("length(type) <= 100", name="constraint_type_length"),
        CheckConstraint(
            "priority IN ('hard', 'soft', 'preference')",
            name="valid_priority"
        ),
    )


class ProvenanceModel(Base):
    """Provenance table - trust and evidence tracking."""

    __tablename__ = "provenance"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True)

    # Core fields
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    asserted_by: Mapped[UUID] = mapped_column(nullable=False)
    asserted_at: Mapped[datetime] = mapped_column(nullable=False)
    
    # Optional fields
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    conflicts: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    scope: Mapped[dict[str, list[str]] | None] = mapped_column(JSON, nullable=True)
    validation_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_validated: Mapped[datetime | None] = mapped_column(nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Indexes
    __table_args__ = (
        Index("idx_provenance_source", "source"),
        Index("idx_provenance_confidence", "confidence"),
        Index("idx_provenance_asserted_by", "asserted_by"),
        CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="confidence_bounds"
        ),
        CheckConstraint(
            "source IN ('measurement', 'inference', 'assertion', 'community', 'expert')",
            name="valid_source"
        ),
    )
