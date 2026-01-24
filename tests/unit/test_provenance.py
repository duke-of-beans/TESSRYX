"""Unit tests for Provenance primitive."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tessryx.core.provenance import Evidence, Provenance, Source


class TestEvidenceCreation:
    """Test evidence creation and validation."""

    def test_create_minimal_evidence(self) -> None:
        """Test creating evidence with minimal required fields."""
        evidence = Evidence(
            type="document",
            reference="https://example.com/spec.pdf",
        )

        assert evidence.type == "document"
        assert evidence.reference == "https://example.com/spec.pdf"
        assert evidence.excerpt is None
        assert evidence.timestamp is None
        assert evidence.confidence_contribution == 0.1  # Default

    def test_create_full_evidence(self) -> None:
        """Test creating evidence with all fields."""
        timestamp = datetime.utcnow()
        evidence = Evidence(
            type="measurement",
            reference="production_logs_2024_01",
            excerpt="Success rate: 99.7%",
            timestamp=timestamp,
            confidence_contribution=0.3,
        )

        assert evidence.excerpt == "Success rate: 99.7%"
        assert evidence.timestamp == timestamp
        assert evidence.confidence_contribution == 0.3

    def test_evidence_immutable(self) -> None:
        """Test that evidence is immutable (frozen)."""
        evidence = Evidence(
            type="document",
            reference="test.pdf",
        )

        with pytest.raises(ValidationError):
            evidence.confidence_contribution = 0.5  # type: ignore

    def test_confidence_contribution_bounds(self) -> None:
        """Test confidence contribution is bounded [0.0, 1.0]."""
        # Valid bounds
        Evidence(type="test", reference="ref", confidence_contribution=0.0)
        Evidence(type="test", reference="ref", confidence_contribution=1.0)

        # Out of bounds
        with pytest.raises(ValidationError):
            Evidence(type="test", reference="ref", confidence_contribution=1.5)

        with pytest.raises(ValidationError):
            Evidence(type="test", reference="ref", confidence_contribution=-0.1)


class TestEvidenceStringRepresentation:
    """Test evidence string representations."""

    def test_str_truncates_long_reference(self) -> None:
        """Test __str__ truncates references longer than 50 chars."""
        long_ref = "a" * 100
        evidence = Evidence(
            type="document",
            reference=long_ref,
        )

        result = str(evidence)
        assert "document" in result
        assert "..." in result
        assert len(result) < len(long_ref)


class TestProvenanceCreation:
    """Test provenance creation and validation."""

    def test_create_minimal_provenance(self) -> None:
        """Test creating provenance with minimal required fields."""
        asserted_by = uuid4()
        prov = Provenance(
            source=Source.USER_INPUT,
            confidence=0.75,
            asserted_by=asserted_by,
        )

        assert prov.source == Source.USER_INPUT
        assert prov.confidence == 0.75
        assert prov.asserted_by == asserted_by
        assert prov.evidence == []  # Default
        assert prov.last_validated is None
        assert prov.validation_method is None
        assert prov.scope is None
        assert prov.conflicts == []

    def test_create_full_provenance(self) -> None:
        """Test creating provenance with all fields."""
        asserted_by = uuid4()
        evidence = [
            Evidence(
                type="measurement",
                reference="prod_logs",
                confidence_contribution=0.2,
            )
        ]
        validated_at = datetime.utcnow()
        scope = {"environment": ["production"], "region": ["us-west"]}
        conflicts = [uuid4(), uuid4()]

        prov = Provenance(
            source=Source.MEASUREMENT,
            evidence=evidence,
            confidence=0.85,
            asserted_by=asserted_by,
            last_validated=validated_at,
            validation_method="automated_test",
            scope=scope,
            conflicts=conflicts,
        )

        assert len(prov.evidence) == 1
        assert prov.last_validated == validated_at
        assert prov.validation_method == "automated_test"
        assert prov.scope == scope
        assert len(prov.conflicts) == 2

    def test_provenance_immutable(self) -> None:
        """Test that provenance is immutable (frozen)."""
        prov = Provenance(
            source=Source.USER_INPUT,
            confidence=0.75,
            asserted_by=uuid4(),
        )

        with pytest.raises(ValidationError):
            prov.confidence = 0.9  # type: ignore

    def test_asserted_at_auto_generated(self) -> None:
        """Test that asserted_at timestamp is automatically generated."""
        before = datetime.utcnow()
        prov = Provenance(
            source=Source.USER_INPUT,
            confidence=0.75,
            asserted_by=uuid4(),
        )
        after = datetime.utcnow()

        assert before <= prov.asserted_at <= after

    def test_confidence_bounds(self) -> None:
        """Test confidence is bounded [0.0, 1.0]."""
        # Valid bounds
        Provenance(
            source=Source.USER_INPUT, confidence=0.0, asserted_by=uuid4()
        )
        Provenance(
            source=Source.USER_INPUT, confidence=1.0, asserted_by=uuid4()
        )

        # Out of bounds
        with pytest.raises(ValidationError):
            Provenance(
                source=Source.USER_INPUT, confidence=1.5, asserted_by=uuid4()
            )

        with pytest.raises(ValidationError):
            Provenance(
                source=Source.USER_INPUT, confidence=-0.1, asserted_by=uuid4()
            )


class TestProvenanceConfidenceLevels:
    """Test provenance confidence level methods."""

    def test_is_high_confidence(self) -> None:
        """Test is_high_confidence() method (≥0.8)."""
        high = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.85,
            asserted_by=uuid4(),
        )
        not_high = Provenance(
            source=Source.USER_INPUT,
            confidence=0.75,
            asserted_by=uuid4(),
        )

        assert high.is_high_confidence()
        assert not not_high.is_high_confidence()

    def test_is_medium_confidence(self) -> None:
        """Test is_medium_confidence() method (0.6-0.8)."""
        medium = Provenance(
            source=Source.DOC_IMPORT,
            confidence=0.7,
            asserted_by=uuid4(),
        )
        high = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.85,
            asserted_by=uuid4(),
        )
        low = Provenance(
            source=Source.INFERRED,
            confidence=0.5,
            asserted_by=uuid4(),
        )

        assert medium.is_medium_confidence()
        assert not high.is_medium_confidence()
        assert not low.is_medium_confidence()

    def test_is_low_confidence(self) -> None:
        """Test is_low_confidence() method (<0.6)."""
        low = Provenance(
            source=Source.INFERRED,
            confidence=0.4,
            asserted_by=uuid4(),
        )
        medium = Provenance(
            source=Source.DOC_IMPORT,
            confidence=0.7,
            asserted_by=uuid4(),
        )

        assert low.is_low_confidence()
        assert not medium.is_low_confidence()

    def test_confidence_boundary_at_08(self) -> None:
        """Test high confidence boundary at exactly 0.8."""
        at_boundary = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.8,
            asserted_by=uuid4(),
        )
        below_boundary = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.7999,
            asserted_by=uuid4(),
        )

        assert at_boundary.is_high_confidence()
        assert not below_boundary.is_high_confidence()

    def test_confidence_boundary_at_06(self) -> None:
        """Test medium/low confidence boundary at exactly 0.6."""
        at_boundary = Provenance(
            source=Source.DOC_IMPORT,
            confidence=0.6,
            asserted_by=uuid4(),
        )
        below_boundary = Provenance(
            source=Source.INFERRED,
            confidence=0.5999,
            asserted_by=uuid4(),
        )

        assert at_boundary.is_medium_confidence()
        assert not at_boundary.is_low_confidence()
        assert below_boundary.is_low_confidence()
        assert not below_boundary.is_medium_confidence()


class TestProvenanceHelpers:
    """Test provenance helper methods."""

    def test_is_validated(self) -> None:
        """Test is_validated() method."""
        validated = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.9,
            asserted_by=uuid4(),
            last_validated=datetime.utcnow(),
        )
        not_validated = Provenance(
            source=Source.USER_INPUT,
            confidence=0.7,
            asserted_by=uuid4(),
        )

        assert validated.is_validated()
        assert not not_validated.is_validated()

    def test_total_evidence_contribution(self) -> None:
        """Test total_evidence_contribution() method."""
        evidence = [
            Evidence(type="measurement", reference="ref1", confidence_contribution=0.2),
            Evidence(type="document", reference="ref2", confidence_contribution=0.15),
            Evidence(type="historical", reference="ref3", confidence_contribution=0.25),
        ]

        prov = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.85,
            asserted_by=uuid4(),
            evidence=evidence,
        )

        total = prov.total_evidence_contribution()
        assert total == pytest.approx(0.6, abs=0.001)  # 0.2 + 0.15 + 0.25

    def test_total_evidence_contribution_empty(self) -> None:
        """Test total_evidence_contribution() with no evidence."""
        prov = Provenance(
            source=Source.USER_INPUT,
            confidence=0.75,
            asserted_by=uuid4(),
            evidence=[],
        )

        assert prov.total_evidence_contribution() == 0.0

    def test_has_conflicts(self) -> None:
        """Test has_conflicts() method."""
        with_conflicts = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.8,
            asserted_by=uuid4(),
            conflicts=[uuid4(), uuid4()],
        )
        no_conflicts = Provenance(
            source=Source.USER_INPUT,
            confidence=0.7,
            asserted_by=uuid4(),
        )

        assert with_conflicts.has_conflicts()
        assert not no_conflicts.has_conflicts()


class TestProvenanceStringRepresentations:
    """Test provenance string representations."""

    def test_str_representation(self) -> None:
        """Test __str__ representation."""
        evidence = [
            Evidence(type="test", reference="ref1"),
            Evidence(type="test", reference="ref2"),
        ]
        prov = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.85,
            asserted_by=uuid4(),
            evidence=evidence,
        )

        result = str(prov)
        assert "measurement" in result
        assert "0.85" in result
        assert "evidence: 2" in result

    def test_repr_representation(self) -> None:
        """Test __repr__ representation."""
        evidence = [Evidence(type="test", reference="ref1")]
        prov = Provenance(
            source=Source.COMMUNITY,
            confidence=0.7,
            asserted_by=uuid4(),
            evidence=evidence,
        )

        repr_str = repr(prov)
        assert "Provenance" in repr_str
        assert ("community" in repr_str or "COMMUNITY" in repr_str)  # Accept either format
        assert "0.7" in repr_str
        assert "evidence_count=1" in repr_str


class TestSourceEnum:
    """Test Source enum."""

    def test_source_types(self) -> None:
        """Test all source types are defined."""
        assert Source.USER_INPUT == "user_input"
        assert Source.DOC_IMPORT == "doc_import"
        assert Source.MEASUREMENT == "measurement"
        assert Source.TEMPLATE == "template"
        assert Source.COMMUNITY == "community"
        assert Source.INFERRED == "inferred"
        assert Source.EXTERNAL_API == "external_api"

    def test_source_usage(self) -> None:
        """Test using Source enum in provenance creation."""
        prov = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.9,
            asserted_by=uuid4(),
        )

        assert prov.source == Source.MEASUREMENT


class TestProvenanceEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_many_evidence_items(self) -> None:
        """Test provenance with many evidence items."""
        evidence = [
            Evidence(
                type=f"type_{i}",
                reference=f"ref_{i}",
                confidence_contribution=0.05,
            )
            for i in range(20)
        ]

        prov = Provenance(
            source=Source.COMMUNITY,
            confidence=0.9,
            asserted_by=uuid4(),
            evidence=evidence,
        )

        assert len(prov.evidence) == 20
        # Total contribution: 20 * 0.05 = 1.0
        assert prov.total_evidence_contribution() == pytest.approx(1.0)

    def test_many_conflicts(self) -> None:
        """Test provenance with many conflicts."""
        conflicts = [uuid4() for _ in range(10)]

        prov = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.8,
            asserted_by=uuid4(),
            conflicts=conflicts,
        )

        assert len(prov.conflicts) == 10
        assert prov.has_conflicts()

    def test_complex_scope(self) -> None:
        """Test provenance with complex scope."""
        scope = {
            "environment": ["production", "staging"],
            "region": ["us-west", "us-east", "eu-central"],
            "time": ["business_hours"],
            "weather": ["sunny"],  # Flattened from nested structure
            "load": ["high"],
        }

        prov = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.85,
            asserted_by=uuid4(),
            scope=scope,
        )

        assert prov.scope == scope
        assert prov.scope["weather"] == ["sunny"]

    def test_evidence_with_zero_contribution(self) -> None:
        """Test evidence with zero confidence contribution."""
        evidence = [
            Evidence(
                type="weak_signal",
                reference="ref",
                confidence_contribution=0.0,
            )
        ]

        prov = Provenance(
            source=Source.INFERRED,
            confidence=0.5,
            asserted_by=uuid4(),
            evidence=evidence,
        )

        assert prov.total_evidence_contribution() == 0.0

    def test_confidence_at_exact_boundaries(self) -> None:
        """Test confidence at exact category boundaries."""
        # Exactly 0.8 (high)
        high_boundary = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.8,
            asserted_by=uuid4(),
        )
        assert high_boundary.is_high_confidence()
        assert not high_boundary.is_medium_confidence()

        # Exactly 0.6 (medium)
        medium_boundary = Provenance(
            source=Source.DOC_IMPORT,
            confidence=0.6,
            asserted_by=uuid4(),
        )
        assert medium_boundary.is_medium_confidence()
        assert not medium_boundary.is_low_confidence()
        assert not medium_boundary.is_high_confidence()

    def test_validation_method_without_timestamp(self) -> None:
        """Test setting validation method without timestamp (unusual)."""
        prov = Provenance(
            source=Source.MEASUREMENT,
            confidence=0.9,
            asserted_by=uuid4(),
            validation_method="manual_review",
            # last_validated is None
        )

        assert prov.validation_method == "manual_review"
        assert not prov.is_validated()  # Not validated without timestamp
