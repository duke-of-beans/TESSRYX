"""Unit tests for Relation primitive."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tessryx.core.relation import Relation, RelationType


class TestRelationCreation:
    """Test relation creation and validation."""

    def test_create_minimal_relation(self) -> None:
        """Test creating relation with minimal required fields."""
        rel_id = uuid4()
        from_id = uuid4()
        to_id = uuid4()

        rel = Relation(
            id=rel_id,
            type="requires",
            from_entity=from_id,
            to_entity=to_id,
        )

        assert rel.id == rel_id
        assert rel.type == "requires"
        assert rel.from_entity == from_id
        assert rel.to_entity == to_id
        assert rel.strength == 1.0  # Default
        assert rel.contract is None
        assert rel.provenance is None

    def test_create_full_relation(self) -> None:
        """Test creating relation with all fields."""
        rel_id = uuid4()
        from_id = uuid4()
        to_id = uuid4()

        contract = {
            "preconditions": ["entity_a_exists"],
            "postconditions": ["entity_b_functional"],
            "invariants": ["version_compatible"],
        }
        provenance = {"confidence": 0.95}  # Schema is dict[str, float]

        rel = Relation(
            id=rel_id,
            type="requires",
            from_entity=from_id,
            to_entity=to_id,
            strength=0.85,
            contract=contract,
            provenance=provenance,
        )

        assert rel.strength == 0.85
        assert rel.contract == contract
        assert rel.provenance == provenance

    def test_relation_immutable(self) -> None:
        """Test that relations are immutable (frozen)."""
        rel = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
        )

        with pytest.raises(ValidationError):
            rel.strength = 0.5  # type: ignore

    def test_timestamps_auto_generated(self) -> None:
        """Test that timestamps are automatically generated."""
        before = datetime.utcnow()
        rel = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
        )
        after = datetime.utcnow()

        assert before <= rel.created_at <= after
        assert before <= rel.updated_at <= after


class TestRelationValidation:
    """Test relation validation rules."""

    def test_self_loop_rejected(self) -> None:
        """Test that self-loops (entity -> same entity) are rejected."""
        entity_id = uuid4()

        with pytest.raises(ValueError, match="self-loop"):
            Relation(
                id=uuid4(),
                type="requires",
                from_entity=entity_id,
                to_entity=entity_id,  # Same as from_entity
            )

    def test_strength_out_of_range_rejected(self) -> None:
        """Test that strength outside [0.0, 1.0] is rejected."""
        # Strength > 1.0
        with pytest.raises(ValidationError):
            Relation(
                id=uuid4(),
                type="requires",
                from_entity=uuid4(),
                to_entity=uuid4(),
                strength=1.5,
            )

        # Strength < 0.0
        with pytest.raises(ValidationError):
            Relation(
                id=uuid4(),
                type="requires",
                from_entity=uuid4(),
                to_entity=uuid4(),
                strength=-0.1,
            )

    def test_empty_type_rejected(self) -> None:
        """Test that empty type strings are rejected."""
        with pytest.raises(ValidationError):
            Relation(
                id=uuid4(),
                type="",  # Empty type
                from_entity=uuid4(),
                to_entity=uuid4(),
            )

    def test_type_too_long_rejected(self) -> None:
        """Test that types longer than 50 chars are rejected."""
        with pytest.raises(ValidationError):
            Relation(
                id=uuid4(),
                type="a" * 51,  # 51 chars
                from_entity=uuid4(),
                to_entity=uuid4(),
            )


class TestRelationHelpers:
    """Test relation helper methods."""

    def test_is_hard_dependency(self) -> None:
        """Test is_hard_dependency() method."""
        hard = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=1.0,
        )
        soft = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.8,
        )

        assert hard.is_hard_dependency()
        assert not soft.is_hard_dependency()

    def test_is_soft_dependency(self) -> None:
        """Test is_soft_dependency() method."""
        soft = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.75,
        )
        hard = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=1.0,
        )
        zero = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.0,
        )

        assert soft.is_soft_dependency()
        assert not hard.is_soft_dependency()
        assert not zero.is_soft_dependency()

    def test_is_weak_dependency(self) -> None:
        """Test is_weak_dependency() method."""
        weak = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.3,
        )
        strong = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.8,
        )

        assert weak.is_weak_dependency()
        assert not strong.is_weak_dependency()

    def test_confidence_with_provenance(self) -> None:
        """Test confidence() extracts from provenance when available."""
        rel_with_prov = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.9,
            provenance={"confidence": 0.85},
        )

        assert rel_with_prov.confidence() == 0.85  # From provenance

    def test_confidence_fallback_to_strength(self) -> None:
        """Test confidence() falls back to strength without provenance."""
        rel_no_prov = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.75,
        )

        assert rel_no_prov.confidence() == 0.75  # Fallback to strength


class TestRelationStringRepresentations:
    """Test relation string representations."""

    def test_str_representation(self) -> None:
        """Test __str__ representation."""
        from_id = uuid4()
        to_id = uuid4()
        rel = Relation(
            id=uuid4(),
            type="requires",
            from_entity=from_id,
            to_entity=to_id,
        )

        result = str(rel)
        assert str(from_id) in result
        assert str(to_id) in result
        assert "requires" in result
        assert "--[" in result
        assert "]-->" in result

    def test_repr_representation(self) -> None:
        """Test __repr__ representation."""
        rel_id = uuid4()
        from_id = uuid4()
        to_id = uuid4()
        rel = Relation(
            id=rel_id,
            type="enables",
            from_entity=from_id,
            to_entity=to_id,
            strength=0.9,
        )

        repr_str = repr(rel)
        assert "Relation" in repr_str
        assert str(rel_id) in repr_str
        assert "enables" in repr_str
        assert str(from_id) in repr_str
        assert str(to_id) in repr_str
        assert "0.9" in repr_str


class TestRelationTypeEnum:
    """Test RelationType enum."""

    def test_dependency_types(self) -> None:
        """Test dependency relation types are defined."""
        assert RelationType.REQUIRES == "requires"
        assert RelationType.ENABLES == "enables"
        assert RelationType.BLOCKS == "blocks"
        assert RelationType.CONFLICTS == "conflicts"

    def test_temporal_types(self) -> None:
        """Test temporal relation types are defined."""
        assert RelationType.PRECEDES == "precedes"
        assert RelationType.FOLLOWS == "follows"
        assert RelationType.CONCURRENT == "concurrent"

    def test_compositional_types(self) -> None:
        """Test compositional relation types are defined."""
        assert RelationType.CONTAINS == "contains"
        assert RelationType.PART_OF == "part_of"
        assert RelationType.REPLACES == "replaces"

    def test_relation_type_usage(self) -> None:
        """Test using RelationType enum in relation creation."""
        rel = Relation(
            id=uuid4(),
            type=RelationType.REQUIRES.value,
            from_entity=uuid4(),
            to_entity=uuid4(),
        )

        assert rel.type == "requires"


class TestRelationEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_strength_boundary_values(self) -> None:
        """Test strength at exact boundary values."""
        # Exactly 0.0
        rel_zero = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.0,
        )
        assert rel_zero.strength == 0.0

        # Exactly 1.0
        rel_one = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=1.0,
        )
        assert rel_one.strength == 1.0

    def test_strength_at_weak_threshold(self) -> None:
        """Test weak dependency at exact 0.5 threshold."""
        at_threshold = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.5,
        )
        below_threshold = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            strength=0.49999,
        )

        assert not at_threshold.is_weak_dependency()  # 0.5 is not weak
        assert below_threshold.is_weak_dependency()

    def test_empty_contract(self) -> None:
        """Test relation with empty contract dictionary."""
        rel = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            contract={},  # Empty but not None
        )

        assert rel.contract == {}

    def test_empty_provenance(self) -> None:
        """Test relation with empty provenance dictionary."""
        rel = Relation(
            id=uuid4(),
            type="requires",
            from_entity=uuid4(),
            to_entity=uuid4(),
            provenance={},  # Empty but not None
        )

        assert rel.provenance == {}
        # Should fall back to strength since no 'confidence' key
        assert rel.confidence() == 1.0  # Default strength
