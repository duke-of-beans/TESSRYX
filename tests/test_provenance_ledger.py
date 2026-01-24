"""Unit tests for Provenance Ledger.

Tests the S01 steal from Consensus: confidence scoring, conflict detection,
validation history, and evidence aggregation.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from tessryx.core.provenance import Evidence, Provenance, Source
from tessryx.kernel.provenance_ledger import ProvenanceLedger


class TestProvenanceLedger:
    """Tests for ProvenanceLedger class."""

    def test_init_empty_ledger(self) -> None:
        """Test creating an empty ledger."""
        ledger = ProvenanceLedger()
        stats = ledger.get_statistics()

        assert stats["total_entities"] == 0
        assert stats["total_records"] == 0
        assert stats["total_conflicts"] == 0

    def test_record_simple_provenance(self) -> None:
        """Test recording a simple provenance assertion."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        prov = ledger.record(
            entity_id=entity_id,
            source=Source.USER_INPUT,
            asserted_by=user_id,
            base_confidence=0.8,
        )

        assert prov.source == Source.USER_INPUT
        assert prov.confidence == 0.8
        assert prov.asserted_by == user_id
        assert isinstance(prov.asserted_at, datetime)

    def test_record_with_evidence(self) -> None:
        """Test recording provenance with supporting evidence."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        evidence = [
            Evidence(
                type="measurement",
                reference="prod_logs_2024_01",
                confidence_contribution=0.15,
            ),
            Evidence(
                type="historical",
                reference="6_month_trend",
                confidence_contribution=0.05,
            ),
        ]

        prov = ledger.record(
            entity_id=entity_id,
            source=Source.MEASUREMENT,
            asserted_by=user_id,
            base_confidence=0.7,
            evidence=evidence,
        )

        # G-Score should be base + evidence contributions (capped at 1.0)
        expected_score = 0.7 + 0.15 + 0.05
        assert prov.confidence == expected_score
        assert len(prov.evidence) == 2

    def test_g_score_capped_at_one(self) -> None:
        """Test that G-Score is capped at 1.0."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()

        evidence = [
            Evidence(type="test", reference="ref1", confidence_contribution=0.3),
            Evidence(type="test", reference="ref2", confidence_contribution=0.3),
        ]

        prov = ledger.record(
            entity_id=entity_id,
            source=Source.COMMUNITY,
            asserted_by=uuid4(),
            base_confidence=0.9,  # 0.9 + 0.3 + 0.3 = 1.5
            evidence=evidence,
        )

        assert prov.confidence == 1.0  # Capped

    def test_invalid_base_confidence(self) -> None:
        """Test that invalid confidence values are rejected."""
        ledger = ProvenanceLedger()

        with pytest.raises(ValueError, match="base_confidence must be 0.0-1.0"):
            ledger.record(
                entity_id=uuid4(),
                source=Source.USER_INPUT,
                asserted_by=uuid4(),
                base_confidence=1.5,  # Invalid
            )

        with pytest.raises(ValueError):
            ledger.record(
                entity_id=uuid4(),
                source=Source.USER_INPUT,
                asserted_by=uuid4(),
                base_confidence=-0.1,  # Invalid
            )

    def test_get_all_records(self) -> None:
        """Test retrieving all provenance records for an entity."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        # Record multiple assertions
        ledger.record(entity_id, Source.USER_INPUT, user_id, 0.6)
        ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.8)
        ledger.record(entity_id, Source.COMMUNITY, user_id, 0.9)

        records = ledger.get_all(entity_id)
        assert len(records) == 3
        assert [r.confidence for r in records] == [0.6, 0.8, 0.9]

    def test_get_latest_record(self) -> None:
        """Test retrieving the most recent provenance record."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        ledger.record(entity_id, Source.USER_INPUT, user_id, 0.6)
        ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.8)

        latest = ledger.get_latest(entity_id)
        assert latest is not None
        assert latest.confidence == 0.8
        assert latest.source == Source.MEASUREMENT

    def test_get_latest_empty(self) -> None:
        """Test getting latest record for entity with no records."""
        ledger = ProvenanceLedger()
        latest = ledger.get_latest(uuid4())
        assert latest is None

    def test_get_highest_confidence(self) -> None:
        """Test retrieving highest-confidence record."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        ledger.record(entity_id, Source.USER_INPUT, user_id, 0.6)
        ledger.record(entity_id, Source.COMMUNITY, user_id, 0.95)  # Highest
        ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.8)

        highest = ledger.get_highest_confidence(entity_id)
        assert highest is not None
        assert highest.confidence == 0.95
        assert highest.source == Source.COMMUNITY

    def test_get_by_source(self) -> None:
        """Test filtering records by source type."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        ledger.record(entity_id, Source.USER_INPUT, user_id, 0.6)
        ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.8)
        ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.85)

        measurements = ledger.get_by_source(entity_id, Source.MEASUREMENT)
        assert len(measurements) == 2
        assert all(r.source == Source.MEASUREMENT for r in measurements)

    def test_validate_record(self) -> None:
        """Test recording validation events."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        # Record initial provenance
        prov = ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.7)
        assert prov.last_validated is None

        # Validate
        ledger.validate(entity_id, "automated_test", result=True)

        # Check updated record
        latest = ledger.get_latest(entity_id)
        assert latest is not None
        assert latest.last_validated is not None
        assert latest.validation_method == "automated_test"

    def test_validation_history(self) -> None:
        """Test tracking validation history."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()

        # Perform multiple validations
        ledger.validate(entity_id, "test1", True)
        ledger.validate(entity_id, "test2", False)
        ledger.validate(entity_id, "test3", True)

        history = ledger.get_validation_history(entity_id)
        assert len(history) == 3

        timestamps, methods, results = zip(*history)
        assert list(methods) == ["test1", "test2", "test3"]
        assert list(results) == [True, False, True]

    def test_validation_affects_g_score(self) -> None:
        """Test that validation history affects future G-Scores."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        # Record initial provenance
        prov1 = ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.7)
        initial_score = prov1.confidence

        # Add positive validation history
        for _ in range(5):
            ledger.validate(entity_id, "test", True)

        # Record new provenance - should have boosted G-Score
        prov2 = ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.7)
        assert prov2.confidence > initial_score  # Boosted by validation history

    def test_conflict_detection_different_sources(self) -> None:
        """Test conflict detection between different sources."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        # Record assertions from different sources with divergent confidence
        ledger.record(entity_id, Source.USER_INPUT, user_id, 0.3)  # Low confidence
        ledger.record(entity_id, Source.COMMUNITY, user_id, 0.95)  # High confidence

        # Should detect conflict (>0.3 difference)
        assert ledger.has_conflicts(entity_id)

    def test_get_conflicts(self) -> None:
        """Test retrieving conflicting provenance records."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        ledger.record(entity_id, Source.USER_INPUT, user_id, 0.2)
        ledger.record(entity_id, Source.COMMUNITY, user_id, 0.9)

        # Get conflicts for the second record (index 1)
        conflicts = ledger.get_conflicts(entity_id, 1)
        assert len(conflicts) > 0
        assert conflicts[0].confidence == 0.2  # The conflicting low-confidence record

    def test_no_conflicts_similar_confidence(self) -> None:
        """Test that similar confidence scores don't trigger conflicts."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        ledger.record(entity_id, Source.USER_INPUT, user_id, 0.75)
        ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.80)

        # Difference is only 0.05, below 0.3 threshold
        assert not ledger.has_conflicts(entity_id)

    def test_aggregate_confidence_single_record(self) -> None:
        """Test aggregate confidence with single record."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()

        ledger.record(entity_id, Source.MEASUREMENT, uuid4(), 0.85)

        aggregate = ledger.get_aggregate_confidence(entity_id)
        assert aggregate == 0.85

    def test_aggregate_confidence_multiple_records(self) -> None:
        """Test aggregate confidence calculation with multiple records."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()
        user_id = uuid4()

        # Record multiple assertions
        ledger.record(entity_id, Source.USER_INPUT, user_id, 0.6)
        ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.8)
        ledger.record(entity_id, Source.COMMUNITY, user_id, 0.9)

        aggregate = ledger.get_aggregate_confidence(entity_id)

        # Should be weighted average favoring newer records
        assert 0.6 < aggregate < 0.9  # Between min and max
        assert aggregate > 0.8  # Closer to newer, higher-confidence records

    def test_aggregate_confidence_empty(self) -> None:
        """Test aggregate confidence for entity with no records."""
        ledger = ProvenanceLedger()
        aggregate = ledger.get_aggregate_confidence(uuid4())
        assert aggregate == 0.0

    def test_statistics(self) -> None:
        """Test ledger statistics calculation."""
        ledger = ProvenanceLedger()
        user_id = uuid4()

        # Add records for multiple entities
        entity1 = uuid4()
        entity2 = uuid4()

        ledger.record(entity1, Source.MEASUREMENT, user_id, 0.85)
        ledger.record(entity1, Source.COMMUNITY, user_id, 0.95)
        ledger.record(entity2, Source.USER_INPUT, user_id, 0.6)

        # Validate one record
        ledger.validate(entity1, "test", True)

        stats = ledger.get_statistics()

        assert stats["total_entities"] == 2
        assert stats["total_records"] == 3
        assert stats["avg_confidence"] > 0.7  # Average of 0.85, 0.95, 0.6
        assert stats["high_confidence_records"] == 2  # Two >= 0.8
        assert stats["validated_records"] == 1

    def test_statistics_by_source(self) -> None:
        """Test statistics broken down by source type."""
        ledger = ProvenanceLedger()
        user_id = uuid4()
        entity_id = uuid4()

        ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.8)
        ledger.record(entity_id, Source.MEASUREMENT, user_id, 0.85)
        ledger.record(entity_id, Source.COMMUNITY, user_id, 0.95)

        stats = ledger.get_statistics()

        assert stats["records_by_source"]["measurement"] == 2
        assert stats["records_by_source"]["community"] == 1

    def test_immutability_of_provenance(self) -> None:
        """Test that Provenance objects are immutable."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()

        prov = ledger.record(entity_id, Source.USER_INPUT, uuid4(), 0.8)

        # Should not be able to modify frozen Provenance
        with pytest.raises(Exception):  # Pydantic ValidationError
            prov.confidence = 0.9  # type: ignore[misc]

    def test_multiple_entities(self) -> None:
        """Test ledger handling multiple entities independently."""
        ledger = ProvenanceLedger()
        user_id = uuid4()

        entity1 = uuid4()
        entity2 = uuid4()

        ledger.record(entity1, Source.MEASUREMENT, user_id, 0.8)
        ledger.record(entity2, Source.COMMUNITY, user_id, 0.9)

        assert len(ledger.get_all(entity1)) == 1
        assert len(ledger.get_all(entity2)) == 1

        assert ledger.get_latest(entity1)!= ledger.get_latest(entity2)


class TestProvenanceGScore:
    """Focused tests for G-Score algorithm."""

    def test_base_confidence_only(self) -> None:
        """Test G-Score with just base confidence."""
        ledger = ProvenanceLedger()

        prov = ledger.record(
            entity_id=uuid4(),
            source=Source.MEASUREMENT,
            asserted_by=uuid4(),
            base_confidence=0.75,
        )

        assert prov.confidence == 0.75

    def test_evidence_contribution(self) -> None:
        """Test that evidence contributions add to base confidence."""
        ledger = ProvenanceLedger()

        evidence = [
            Evidence(type="doc", reference="ref1", confidence_contribution=0.1),
            Evidence(type="test", reference="ref2", confidence_contribution=0.05),
        ]

        prov = ledger.record(
            entity_id=uuid4(),
            source=Source.MEASUREMENT,
            asserted_by=uuid4(),
            base_confidence=0.7,
            evidence=evidence,
        )

        # 0.7 + 0.1 + 0.05 = 0.85
        assert prov.confidence == 0.85

    def test_validation_boost(self) -> None:
        """Test that successful validations boost future G-Scores."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()

        # Build positive validation history
        for _ in range(10):
            ledger.validate(entity_id, "test", True)

        prov = ledger.record(
            entity_id=entity_id,
            source=Source.MEASUREMENT,
            asserted_by=uuid4(),
            base_confidence=0.7,
        )

        # Should be boosted by ~5% due to validation history
        assert prov.confidence > 0.7
        assert prov.confidence <= 0.7 * 1.05 + 0.01  # Allow small variance

    def test_validation_penalty(self) -> None:
        """Test that failed validations penalize future G-Scores."""
        ledger = ProvenanceLedger()
        entity_id = uuid4()

        # Build negative validation history
        for _ in range(10):
            ledger.validate(entity_id, "test", False)

        prov = ledger.record(
            entity_id=entity_id,
            source=Source.MEASUREMENT,
            asserted_by=uuid4(),
            base_confidence=0.7,
        )

        # Should be penalized by ~5%
        assert prov.confidence < 0.7
        assert prov.confidence >= 0.7 * 0.95 - 0.01  # Allow small variance
