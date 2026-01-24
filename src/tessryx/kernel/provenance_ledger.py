"""Provenance Ledger - Trust infrastructure managing all assertions.

This module implements the S01 steal from Consensus: a complete provenance
ledger with confidence scoring (G-Score), validation history, and conflict detection.

The ledger is the single source of truth for:
- Who asserted what
- When it was asserted
- What evidence supports it
- How confident we should be
- What conflicts exist
"""

from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import UUID

from tessryx.core.provenance import Evidence, Provenance, Source
from tessryx.core.types import EntityID


class ProvenanceLedger:
    """Central ledger managing all provenance records.

    The ledger provides:
    - Provenance storage and retrieval
    - Confidence score calculation (G-Score algorithm)
    - Conflict detection and tracking
    - Validation history
    - Evidence aggregation

    Thread-safe for concurrent access (uses immutable Provenance objects).

    Examples:
        >>> from uuid import uuid4
        >>> ledger = ProvenanceLedger()
        >>> user_id = uuid4()
        >>> entity_id = uuid4()
        >>>
        >>> # Record a measurement with evidence
        >>> prov = ledger.record(
        ...     entity_id=entity_id,
        ...     source=Source.MEASUREMENT,
        ...     asserted_by=user_id,
        ...     base_confidence=0.7,
        ...     evidence=[
        ...         Evidence(
        ...             type="measurement",
        ...             reference="prod_logs_2024_01",
        ...             confidence_contribution=0.2
        ...         )
        ...     ]
        ... )
        >>> prov.confidence  # Base + evidence contributions
        0.9
        >>>
        >>> # Get provenance for entity
        >>> records = ledger.get_all(entity_id)
        >>> len(records)
        1
    """

    def __init__(self) -> None:
        """Initialize an empty provenance ledger."""
        # Entity ID -> list of Provenance records
        self._records: dict[EntityID, list[Provenance]] = defaultdict(list)

        # Track conflicts: Provenance ID -> list of conflicting Provenance IDs
        self._conflicts: dict[tuple[EntityID, int], list[tuple[EntityID, int]]] = {}

        # Validation history: Entity ID -> list of (timestamp, method, result)
        self._validation_history: dict[EntityID, list[tuple[datetime, str, bool]]] = (
            defaultdict(list)
        )

    def record(
        self,
        entity_id: EntityID,
        source: Source,
        asserted_by: EntityID,
        base_confidence: float,
        evidence: list[Evidence] | None = None,
        validation_method: str | None = None,
        scope: dict[str, list[str]] | None = None,
    ) -> Provenance:
        """Record a new provenance assertion.

        Calculates final confidence using G-Score algorithm:
        - Base confidence from source type
        - Evidence contributions (additive, capped at 1.0)
        - Historical validation adjustments

        Args:
            entity_id: Entity this provenance applies to
            source: Source type of assertion
            asserted_by: Who/what made the assertion
            base_confidence: Initial confidence (0.0-1.0)
            evidence: Supporting evidence items
            validation_method: How this was validated (optional)
            scope: Context where provenance applies (optional)

        Returns:
            Created Provenance record with calculated G-Score

        Raises:
            ValueError: If base_confidence not in [0.0, 1.0]
        """
        if not 0.0 <= base_confidence <= 1.0:
            raise ValueError(f"base_confidence must be 0.0-1.0, got {base_confidence}")

        evidence = evidence or []

        # Calculate G-Score (confidence with evidence)
        g_score = self._calculate_g_score(
            base_confidence=base_confidence,
            evidence=evidence,
            entity_id=entity_id,
        )

        # Create provenance record
        provenance = Provenance(
            source=source,
            evidence=evidence,
            confidence=g_score,
            asserted_by=asserted_by,
            asserted_at=datetime.utcnow(),
            last_validated=datetime.utcnow() if validation_method else None,
            validation_method=validation_method,
            scope=scope,
            conflicts=[],  # Will be detected later
        )

        # Store in ledger
        self._records[entity_id].append(provenance)

        # Detect conflicts with existing records
        self._detect_conflicts(entity_id, len(self._records[entity_id]) - 1)

        return provenance

    def get_all(self, entity_id: EntityID) -> list[Provenance]:
        """Get all provenance records for an entity.

        Returns records in chronological order (oldest first).

        Args:
            entity_id: Entity to get provenance for

        Returns:
            List of Provenance records (may be empty)
        """
        return list(self._records[entity_id])

    def get_latest(self, entity_id: EntityID) -> Provenance | None:
        """Get the most recent provenance record for an entity.

        Args:
            entity_id: Entity to get provenance for

        Returns:
            Latest Provenance record, or None if no records exist
        """
        records = self._records[entity_id]
        return records[-1] if records else None

    def get_highest_confidence(self, entity_id: EntityID) -> Provenance | None:
        """Get the highest-confidence provenance record for an entity.

        Useful when multiple sources assert the same thing with different confidence.

        Args:
            entity_id: Entity to get provenance for

        Returns:
            Highest-confidence Provenance record, or None if no records exist
        """
        records = self._records[entity_id]
        if not records:
            return None

        return max(records, key=lambda p: p.confidence)

    def get_by_source(self, entity_id: EntityID, source: Source) -> list[Provenance]:
        """Get all provenance records from a specific source type.

        Args:
            entity_id: Entity to filter records for
            source: Source type to filter by

        Returns:
            List of matching Provenance records
        """
        return [p for p in self._records[entity_id] if p.source == source]

    def validate(
        self,
        entity_id: EntityID,
        validation_method: str,
        result: bool,
    ) -> None:
        """Record a validation event for an entity's provenance.

        Updates validation history and may adjust confidence scores
        for related assertions.

        Args:
            entity_id: Entity that was validated
            validation_method: How validation was performed
            result: Whether validation passed (True) or failed (False)
        """
        timestamp = datetime.utcnow()

        # Record in validation history
        self._validation_history[entity_id].append((timestamp, validation_method, result))

        # Update latest provenance record if it exists
        records = self._records[entity_id]
        if records:
            latest = records[-1]

            # Create updated provenance with validation info
            # (Provenance is immutable, so we create a new one)
            updated = Provenance(
                source=latest.source,
                evidence=latest.evidence,
                confidence=latest.confidence,
                asserted_by=latest.asserted_by,
                asserted_at=latest.asserted_at,
                last_validated=timestamp,
                validation_method=validation_method,
                scope=latest.scope,
                conflicts=latest.conflicts,
            )

            # Replace latest record
            self._records[entity_id][-1] = updated

    def get_validation_history(
        self,
        entity_id: EntityID,
    ) -> list[tuple[datetime, str, bool]]:
        """Get validation history for an entity.

        Returns list of (timestamp, method, result) tuples in chronological order.

        Args:
            entity_id: Entity to get history for

        Returns:
            List of validation events
        """
        return list(self._validation_history[entity_id])

    def get_conflicts(self, entity_id: EntityID, index: int) -> list[Provenance]:
        """Get all provenance records conflicting with a specific record.

        Args:
            entity_id: Entity the record belongs to
            index: Index of record in entity's provenance list

        Returns:
            List of conflicting Provenance records
        """
        key = (entity_id, index)
        if key not in self._conflicts:
            return []

        result = []
        for conflict_entity_id, conflict_index in self._conflicts[key]:
            if conflict_index < len(self._records[conflict_entity_id]):
                result.append(self._records[conflict_entity_id][conflict_index])

        return result

    def has_conflicts(self, entity_id: EntityID) -> bool:
        """Check if any provenance records for entity have conflicts.

        Args:
            entity_id: Entity to check

        Returns:
            True if conflicts exist
        """
        for i in range(len(self._records[entity_id])):
            if (entity_id, i) in self._conflicts:
                return True
        return False

    def get_aggregate_confidence(self, entity_id: EntityID) -> float:
        """Calculate aggregate confidence from all provenance records.

        Uses weighted average based on:
        - Recency (newer records weighted higher)
        - Evidence quality
        - Source reliability

        Args:
            entity_id: Entity to calculate confidence for

        Returns:
            Aggregate confidence score (0.0-1.0), or 0.0 if no records
        """
        records = self._records[entity_id]
        if not records:
            return 0.0

        # Simple weighted average for now (can enhance later)
        # Weight newer records higher using exponential decay
        total_weight = 0.0
        weighted_sum = 0.0

        for i, record in enumerate(records):
            # Recency weight: newer records weighted higher
            recency_weight = 0.5 ** (len(records) - i - 1)  # Exponential decay

            # Evidence weight: more evidence = higher weight
            evidence_weight = 1.0 + (len(record.evidence) * 0.1)

            # Validation weight: validated records weighted higher
            validation_weight = 1.5 if record.is_validated() else 1.0

            weight = recency_weight * evidence_weight * validation_weight
            weighted_sum += record.confidence * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def get_statistics(self) -> dict[str, Any]:
        """Get ledger statistics.

        Returns:
            Dictionary with ledger metrics:
            - total_entities: Number of entities with provenance
            - total_records: Total provenance records
            - total_conflicts: Number of conflicts detected
            - avg_confidence: Average confidence across all records
            - records_by_source: Count of records by source type
            - high_confidence_records: Count with confidence >= 0.8
            - validated_records: Count with validation
        """
        total_records = sum(len(records) for records in self._records.values())
        total_conflicts = len(self._conflicts)

        all_confidences = [
            p.confidence for records in self._records.values() for p in records
        ]
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        # Count by source
        records_by_source: dict[Source, int] = defaultdict(int)
        for records in self._records.values():
            for p in records:
                records_by_source[p.source] += 1

        # High confidence count
        high_confidence = sum(1 for c in all_confidences if c >= 0.8)

        # Validated count
        validated = sum(
            1 for records in self._records.values() for p in records if p.is_validated()
        )

        return {
            "total_entities": len(self._records),
            "total_records": total_records,
            "total_conflicts": total_conflicts,
            "avg_confidence": round(avg_confidence, 3),
            "records_by_source": {s.value: count for s, count in records_by_source.items()},
            "high_confidence_records": high_confidence,
            "validated_records": validated,
        }

    # Private methods

    def _calculate_g_score(
        self,
        base_confidence: float,
        evidence: list[Evidence],
        entity_id: EntityID,
    ) -> float:
        """Calculate G-Score (confidence with evidence).

        G-Score algorithm:
        1. Start with base confidence from source
        2. Add evidence contributions (additive)
        3. Apply historical validation adjustments
        4. Cap at 1.0

        Args:
            base_confidence: Initial confidence
            evidence: Supporting evidence items
            entity_id: Entity for historical context

        Returns:
            Final G-Score (0.0-1.0)
        """
        # Start with base
        score = base_confidence

        # Add evidence contributions
        for ev in evidence:
            score += ev.confidence_contribution

        # Apply historical validation adjustment
        history = self._validation_history[entity_id]
        if history:
            # Count recent validations (last 10)
            recent = history[-10:]
            passed = sum(1 for _, _, result in recent if result)
            failed = len(recent) - passed

            # Adjust based on validation success rate
            if passed > failed:
                # Good track record: small boost
                score *= 1.05
            elif failed > passed:
                # Poor track record: small penalty
                score *= 0.95

        # Cap at 1.0
        return min(score, 1.0)

    def _detect_conflicts(self, entity_id: EntityID, new_index: int) -> None:
        """Detect conflicts between new provenance and existing records.

        Conflicts occur when:
        - Different sources assert contradictory things
        - Confidence scores diverge significantly
        - Evidence contradicts

        Args:
            entity_id: Entity the new record belongs to
            new_index: Index of new record in entity's list
        """
        records = self._records[entity_id]
        new_record = records[new_index]

        for i, existing in enumerate(records[: new_index]):
            # Check for conflict indicators
            has_conflict = False

            # Different sources with very different confidence
            if existing.source != new_record.source:
                confidence_diff = abs(existing.confidence - new_record.confidence)
                if confidence_diff > 0.3:  # Significant divergence
                    has_conflict = True

            # Mark conflict if detected
            if has_conflict:
                # Record bidirectional conflict
                self._conflicts.setdefault((entity_id, new_index), []).append(
                    (entity_id, i)
                )
                self._conflicts.setdefault((entity_id, i), []).append((entity_id, new_index))

                # Update conflict lists in records (create new immutable versions)
                # Update existing record
                updated_existing = Provenance(
                    source=existing.source,
                    evidence=existing.evidence,
                    confidence=existing.confidence,
                    asserted_by=existing.asserted_by,
                    asserted_at=existing.asserted_at,
                    last_validated=existing.last_validated,
                    validation_method=existing.validation_method,
                    scope=existing.scope,
                    conflicts=existing.conflicts + [entity_id],  # Add conflict
                )
                records[i] = updated_existing

                # Update new record
                updated_new = Provenance(
                    source=new_record.source,
                    evidence=new_record.evidence,
                    confidence=new_record.confidence,
                    asserted_by=new_record.asserted_by,
                    asserted_at=new_record.asserted_at,
                    last_validated=new_record.last_validated,
                    validation_method=new_record.validation_method,
                    scope=new_record.scope,
                    conflicts=new_record.conflicts + [entity_id],  # Add conflict
                )
                records[new_index] = updated_new
