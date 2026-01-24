"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..core.constraint import ConstraintType, Priority
from ..core.entity import EntityType
from ..core.provenance import Source
from ..core.relation import RelationType


# === Entity Schemas ===


class EntityCreate(BaseModel):
    """Schema for creating a new entity."""

    name: str = Field(..., min_length=1, max_length=500)
    type: str = Field(..., min_length=1, max_length=100)
    version: str | None = Field(None, max_length=50)
    parent_id: UUID | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class EntityUpdate(BaseModel):
    """Schema for updating an entity."""

    name: str | None = Field(None, min_length=1, max_length=500)
    type: str | None = Field(None, min_length=1, max_length=100)
    version: str | None = Field(None, max_length=50)
    parent_id: UUID | None = None
    attributes: dict[str, Any] | None = None
    tags: list[str] | None = None


class EntityResponse(BaseModel):
    """Schema for entity response."""

    id: UUID
    name: str
    type: str
    version: str | None
    parent_id: UUID | None
    children_ids: list[UUID]
    attributes: dict[str, Any]
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Relation Schemas ===


class RelationCreate(BaseModel):
    """Schema for creating a new relation."""

    type: str = Field(..., min_length=1, max_length=100)
    from_entity_id: UUID
    to_entity_id: UUID
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    contract: dict[str, list[str]] | None = None
    provenance: dict[str, float] | None = None


class RelationUpdate(BaseModel):
    """Schema for updating a relation."""

    type: str | None = Field(None, min_length=1, max_length=100)
    strength: float | None = Field(None, ge=0.0, le=1.0)
    contract: dict[str, list[str]] | None = None
    provenance: dict[str, float] | None = None


class RelationResponse(BaseModel):
    """Schema for relation response."""

    id: UUID
    type: str
    from_entity_id: UUID
    to_entity_id: UUID
    strength: float
    contract: dict[str, list[str]] | None
    provenance: dict[str, float] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Constraint Schemas ===


class ConstraintCreate(BaseModel):
    """Schema for creating a new constraint."""

    type: str = Field(..., min_length=1, max_length=100)
    entities: list[UUID] = Field(..., min_length=1)
    priority: str = Field(..., pattern="^(hard|soft|preference)$")
    parameters: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, float] | None = None
    scope: dict[str, list[str]] | None = None


class ConstraintUpdate(BaseModel):
    """Schema for updating a constraint."""

    type: str | None = Field(None, min_length=1, max_length=100)
    entities: list[UUID] | None = Field(None, min_length=1)
    priority: str | None = Field(None, pattern="^(hard|soft|preference)$")
    parameters: dict[str, Any] | None = None
    provenance: dict[str, float] | None = None
    scope: dict[str, list[str]] | None = None


class ConstraintResponse(BaseModel):
    """Schema for constraint response."""

    id: UUID
    type: str
    entities: list[UUID]
    priority: str
    parameters: dict[str, Any]
    provenance: dict[str, float] | None
    scope: dict[str, list[str]] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Provenance Schemas ===


class ProvenanceCreate(BaseModel):
    """Schema for creating provenance."""

    source: str = Field(..., pattern="^(measurement|inference|assertion|community|expert)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    asserted_by: UUID
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    conflicts: list[str] | None = None
    scope: dict[str, list[str]] | None = None
    validation_method: str | None = Field(None, max_length=100)
    last_validated: datetime | None = None


class ProvenanceUpdate(BaseModel):
    """Schema for updating provenance."""

    source: str | None = Field(None, pattern="^(measurement|inference|assertion|community|expert)$")
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    evidence: list[dict[str, Any]] | None = None
    conflicts: list[str] | None = None
    scope: dict[str, list[str]] | None = None
    validation_method: str | None = Field(None, max_length=100)
    last_validated: datetime | None = None


class ProvenanceResponse(BaseModel):
    """Schema for provenance response."""

    id: UUID
    source: str
    confidence: float
    asserted_by: UUID
    asserted_at: datetime
    evidence: list[dict[str, Any]]
    conflicts: list[str] | None
    scope: dict[str, list[str]] | None
    validation_method: str | None
    last_validated: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# === Common Schemas ===


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
    error_type: str | None = None


class SuccessResponse(BaseModel):
    """Schema for success responses."""

    message: str
    data: dict[str, Any] | None = None
