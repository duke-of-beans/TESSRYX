"""Provenance primitive - trust infrastructure for every assertion."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from tessryx.core.types import EntityID


class Source(str, Enum):
    """Source types for provenance tracking."""

    USER_INPUT = "user_input"  # Manual entry
    DOC_IMPORT = "doc_import"  # Extracted from documentation
    MEASUREMENT = "measurement"  # Empirical observation
    TEMPLATE = "template"  # Domain pack default
    COMMUNITY = "community"  # Crowd-sourced
    INFERRED = "inferred"  # Derived by system
    EXTERNAL_API = "external_api"  # Third-party data


class Evidence(BaseModel):
    """Supporting evidence for an assertion.

    Evidence contributes to overall confidence and provides traceability.
    """

    type: str = Field(
        ...,
        description="Evidence type (document, measurement, historical, expert)",
    )

    reference: str = Field(
        ...,
        description="URL, citation, or identifier",
    )

    excerpt: str | None = Field(
        default=None,
        description="Relevant quote or excerpt",
    )

    timestamp: datetime | None = Field(
        default=None,
        description="When evidence was captured",
    )

    confidence_contribution: float = Field(
        default=0.1,
        description="How much this evidence adds to confidence (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    model_config = {"frozen": True}

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.type}: {self.reference[:50]}..."


class Provenance(BaseModel):
    """Trust infrastructure tracking source and confidence of assertions.

    Provenance enables:
    - Confidence propagation through dependency chains
    - Evidence-based decision making
    - Conflict detection and resolution
    - Audit trails for compliance

    Examples:
        >>> from uuid import uuid4
        >>> prov = Provenance(
        ...     source="measurement",
        ...     confidence=0.85,
        ...     asserted_by=uuid4(),
        ...     evidence=[
        ...         Evidence(
        ...             type="measurement",
        ...             reference="production_logs_2024_01",
        ...             confidence_contribution=0.2
        ...         )
        ...     ]
        ... )
        >>> prov.is_high_confidence()
        True
    """

    source: Source = Field(
        ...,
        description="Source type of this assertion",
    )

    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Supporting evidence items",
    )

    confidence: float = Field(
        ...,
        description="Confidence score (0.0-1.0, higher = more certain)",
        ge=0.0,
        le=1.0,
    )

    asserted_by: EntityID = Field(
        ...,
        description="User or system that made this assertion",
    )

    asserted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When assertion was made (UTC)",
    )

    last_validated: datetime | None = Field(
        default=None,
        description="Last validation timestamp",
    )

    validation_method: str | None = Field(
        default=None,
        description="How this was validated (e.g., 'automated_test')",
    )

    scope: dict[str, list[str]] | None = Field(
        default=None,
        description="Context where this provenance applies",
    )

    conflicts: list[EntityID] = Field(
        default_factory=list,
        description="Other provenances this contradicts",
    )

    model_config = {
        "frozen": True,
        "json_schema_extra": {
            "examples": [
                {
                    "source": "measurement",
                    "confidence": 0.85,
                    "asserted_by": "550e8400-e29b-41d4-a716-446655440000",
                    "evidence": [
                        {
                            "type": "historical",
                            "reference": "last_6_months_data",
                            "confidence_contribution": 0.3,
                        }
                    ],
                }
            ]
        },
    }

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"{self.source.value} (confidence: {self.confidence:.2f}, "
            f"evidence: {len(self.evidence)})"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Provenance(source={self.source}, confidence={self.confidence}, "
            f"evidence_count={len(self.evidence)})"
        )

    def is_high_confidence(self) -> bool:
        """Check if confidence is high (≥0.8)."""
        return self.confidence >= 0.8

    def is_medium_confidence(self) -> bool:
        """Check if confidence is medium (0.6-0.8)."""
        return 0.6 <= self.confidence < 0.8

    def is_low_confidence(self) -> bool:
        """Check if confidence is low (<0.6)."""
        return self.confidence < 0.6

    def is_validated(self) -> bool:
        """Check if assertion has been validated."""
        return self.last_validated is not None

    def total_evidence_contribution(self) -> float:
        """Calculate total confidence contribution from evidence."""
        return sum(e.confidence_contribution for e in self.evidence)

    def has_conflicts(self) -> bool:
        """Check if this provenance conflicts with others."""
        return len(self.conflicts) > 0
