"""Unit tests for Constraint primitive."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tessryx.core.constraint import Constraint, ConstraintType, Priority


class TestConstraintCreation:
    """Test constraint creation and validation."""

    def test_create_minimal_constraint(self) -> None:
        """Test creating constraint with minimal required fields."""
        con_id = uuid4()
        entity_a = uuid4()
        entity_b = uuid4()

        con = Constraint(
            id=con_id,
            type="precedence",
            entities=[entity_a, entity_b],
            parameters={"before": "entity_a", "after": "entity_b"},
        )

        assert con.id == con_id
        assert con.type == "precedence"
        assert con.entities == [entity_a, entity_b]
        assert con.parameters == {"before": "entity_a", "after": "entity_b"}
        assert con.priority == Priority.HARD  # Default
        assert con.provenance is None
        assert con.scope is None

    def test_create_full_constraint(self) -> None:
        """Test creating constraint with all fields."""
        con_id = uuid4()
        entities = [uuid4(), uuid4(), uuid4()]
        parameters = {"min_gap": 5, "unit": "days"}
        provenance = {"confidence": 0.9, "source": "measurement"}
        scope = {"context": ["production"]}

        con = Constraint(
            id=con_id,
            type="delay",
            entities=entities,
            parameters=parameters,
            priority=Priority.SOFT,
            provenance=provenance,
            scope=scope,
        )

        assert con.priority == Priority.SOFT
        assert con.provenance == provenance
        assert con.scope == scope

    def test_constraint_immutable(self) -> None:
        """Test that constraints are immutable (frozen)."""
        con = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},
        )

        with pytest.raises(ValidationError):
            con.priority = Priority.SOFT  # type: ignore

    def test_timestamps_auto_generated(self) -> None:
        """Test that timestamps are automatically generated."""
        before = datetime.utcnow()
        con = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},
        )
        after = datetime.utcnow()

        assert before <= con.created_at <= after


class TestConstraintValidation:
    """Test constraint validation rules."""

    def test_empty_entities_rejected(self) -> None:
        """Test that constraints without entities are rejected."""
        with pytest.raises(ValidationError):
            Constraint(
                id=uuid4(),
                type="mutex",
                entities=[],  # Empty list
                parameters={},
            )

    def test_empty_type_rejected(self) -> None:
        """Test that empty type strings are rejected."""
        with pytest.raises(ValidationError):
            Constraint(
                id=uuid4(),
                type="",  # Empty type
                entities=[uuid4()],
                parameters={},
            )

    def test_type_too_long_rejected(self) -> None:
        """Test that types longer than 50 chars are rejected."""
        with pytest.raises(ValidationError):
            Constraint(
                id=uuid4(),
                type="a" * 51,  # 51 chars
                entities=[uuid4()],
                parameters={},
            )


class TestConstraintPriorities:
    """Test constraint priority methods."""

    def test_is_hard(self) -> None:
        """Test is_hard() method."""
        hard = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},
            priority=Priority.HARD,
        )
        soft = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},
            priority=Priority.SOFT,
        )

        assert hard.is_hard()
        assert not soft.is_hard()

    def test_is_soft(self) -> None:
        """Test is_soft() method."""
        soft = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},
            priority=Priority.SOFT,
        )
        hard = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},
            priority=Priority.HARD,
        )

        assert soft.is_soft()
        assert not hard.is_soft()

    def test_is_preference(self) -> None:
        """Test is_preference() method."""
        pref = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},
            priority=Priority.PREFERENCE,
        )
        hard = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},
            priority=Priority.HARD,
        )

        assert pref.is_preference()
        assert not hard.is_preference()


class TestConstraintCategories:
    """Test constraint category methods."""

    def test_is_temporal(self) -> None:
        """Test is_temporal() method."""
        temporal_types = [
            "precedence",
            "time_window",
            "duration",
            "deadline",
            "delay",
            "synchronization",
            "recurrence",
            "expiration",
        ]

        for ctype in temporal_types:
            con = Constraint(
                id=uuid4(),
                type=ctype,
                entities=[uuid4()],
                parameters={},
            )
            assert con.is_temporal(), f"{ctype} should be temporal"

        # Non-temporal
        non_temporal = Constraint(
            id=uuid4(),
            type="mutex",  # Logical, not temporal
            entities=[uuid4()],
            parameters={},
        )
        assert not non_temporal.is_temporal()

    def test_is_resource(self) -> None:
        """Test is_resource() method."""
        resource_types = [
            "resource_capacity",
            "resource_allocation",
            "resource_sharing",
            "budget",
            "throughput",
            "reservation",
            "utilization",
            "dependency_quota",
        ]

        for ctype in resource_types:
            con = Constraint(
                id=uuid4(),
                type=ctype,
                entities=[uuid4()],
                parameters={},
            )
            assert con.is_resource(), f"{ctype} should be resource"

        # Non-resource
        non_resource = Constraint(
            id=uuid4(),
            type="mutex",  # Logical, not resource
            entities=[uuid4()],
            parameters={},
        )
        assert not non_resource.is_resource()

    def test_is_logical(self) -> None:
        """Test is_logical() method."""
        logical_types = [
            "mutex",
            "choice",
            "conditional",
            "implication",
            "equivalence",
            "disjunction",
            "negation",
        ]

        for ctype in logical_types:
            con = Constraint(
                id=uuid4(),
                type=ctype,
                entities=[uuid4()],
                parameters={},
            )
            assert con.is_logical(), f"{ctype} should be logical"

        # Non-logical
        non_logical = Constraint(
            id=uuid4(),
            type="precedence",  # Temporal, not logical
            entities=[uuid4()],
            parameters={},
        )
        assert not non_logical.is_logical()

    def test_is_structural(self) -> None:
        """Test is_structural() method."""
        structural_types = [
            "hierarchy",
            "composition",
            "encapsulation",
            "interface_compatibility",
            "cardinality",
        ]

        for ctype in structural_types:
            con = Constraint(
                id=uuid4(),
                type=ctype,
                entities=[uuid4()],
                parameters={},
            )
            assert con.is_structural(), f"{ctype} should be structural"

        # Non-structural
        non_structural = Constraint(
            id=uuid4(),
            type="mutex",  # Logical, not structural
            entities=[uuid4()],
            parameters={},
        )
        assert not non_structural.is_structural()


class TestConstraintStringRepresentations:
    """Test constraint string representations."""

    def test_str_representation(self) -> None:
        """Test __str__ representation."""
        con = Constraint(
            id=uuid4(),
            type="precedence",
            entities=[uuid4(), uuid4(), uuid4()],
            parameters={"min_gap": 5},
            priority=Priority.SOFT,
        )

        result = str(con)
        assert "precedence" in result
        assert "3 entities" in result
        assert ("soft" in result or "SOFT" in result)  # Accept either format

    def test_repr_representation(self) -> None:
        """Test __repr__ representation."""
        con_id = uuid4()
        con = Constraint(
            id=con_id,
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},
            priority=Priority.HARD,
        )

        repr_str = repr(con)
        assert "Constraint" in repr_str
        assert str(con_id) in repr_str
        assert "mutex" in repr_str
        assert "2" in repr_str  # Entity count
        assert ("hard" in repr_str or "HARD" in repr_str)  # Accept either format


class TestConstraintTypeEnum:
    """Test ConstraintType enum."""

    def test_temporal_types(self) -> None:
        """Test temporal constraint types are defined."""
        assert ConstraintType.PRECEDENCE == "precedence"
        assert ConstraintType.TIME_WINDOW == "time_window"
        assert ConstraintType.DURATION == "duration"
        assert ConstraintType.DEADLINE == "deadline"
        assert ConstraintType.DELAY == "delay"
        assert ConstraintType.SYNCHRONIZATION == "synchronization"
        assert ConstraintType.RECURRENCE == "recurrence"
        assert ConstraintType.EXPIRATION == "expiration"

    def test_resource_types(self) -> None:
        """Test resource constraint types are defined."""
        assert ConstraintType.RESOURCE_CAPACITY == "resource_capacity"
        assert ConstraintType.RESOURCE_ALLOCATION == "resource_allocation"
        assert ConstraintType.RESOURCE_SHARING == "resource_sharing"
        assert ConstraintType.BUDGET == "budget"
        assert ConstraintType.THROUGHPUT == "throughput"
        assert ConstraintType.RESERVATION == "reservation"
        assert ConstraintType.UTILIZATION == "utilization"
        assert ConstraintType.DEPENDENCY_QUOTA == "dependency_quota"

    def test_logical_types(self) -> None:
        """Test logical constraint types are defined."""
        assert ConstraintType.MUTEX == "mutex"
        assert ConstraintType.CHOICE == "choice"
        assert ConstraintType.CONDITIONAL == "conditional"
        assert ConstraintType.IMPLICATION == "implication"
        assert ConstraintType.EQUIVALENCE == "equivalence"
        assert ConstraintType.DISJUNCTION == "disjunction"
        assert ConstraintType.NEGATION == "negation"

    def test_structural_types(self) -> None:
        """Test structural constraint types are defined."""
        assert ConstraintType.HIERARCHY == "hierarchy"
        assert ConstraintType.COMPOSITION == "composition"
        assert ConstraintType.ENCAPSULATION == "encapsulation"
        assert ConstraintType.INTERFACE_COMPATIBILITY == "interface_compatibility"
        assert ConstraintType.CARDINALITY == "cardinality"


class TestPriorityEnum:
    """Test Priority enum."""

    def test_priority_values(self) -> None:
        """Test that priority values are defined."""
        assert Priority.HARD == "hard"
        assert Priority.SOFT == "soft"
        assert Priority.PREFERENCE == "pref"

    def test_priority_usage(self) -> None:
        """Test using Priority enum in constraint creation."""
        con = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4()],
            parameters={},
            priority=Priority.SOFT,
        )

        assert con.priority == Priority.SOFT


class TestConstraintEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_entity_constraint(self) -> None:
        """Test constraint with single entity (valid for some types)."""
        con = Constraint(
            id=uuid4(),
            type="negation",  # Makes sense with one entity
            entities=[uuid4()],
            parameters={},
        )

        assert len(con.entities) == 1

    def test_many_entities_constraint(self) -> None:
        """Test constraint with many entities."""
        entities = [uuid4() for _ in range(10)]
        con = Constraint(
            id=uuid4(),
            type="choice",  # Choose N of M
            entities=entities,
            parameters={"choose": 3},
        )

        assert len(con.entities) == 10

    def test_empty_parameters(self) -> None:
        """Test constraint with empty parameters dictionary."""
        con = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4(), uuid4()],
            parameters={},  # Empty but valid
        )

        assert con.parameters == {}

    def test_complex_parameters(self) -> None:
        """Test constraint with complex nested parameters."""
        params = {
            "min_gap": 5,
            "max_gap": 10,
            "unit": "days",
            "conditions": {
                "weather": "sunny",
                "season": "summer",
            },
            "fallback": ["alternative_a", "alternative_b"],
        }

        con = Constraint(
            id=uuid4(),
            type="delay",
            entities=[uuid4(), uuid4()],
            parameters=params,
        )

        assert con.parameters == params
        assert con.parameters["conditions"]["weather"] == "sunny"

    def test_none_vs_empty_provenance(self) -> None:
        """Test difference between None and empty provenance."""
        con_none = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4()],
            parameters={},
            provenance=None,
        )
        con_empty = Constraint(
            id=uuid4(),
            type="mutex",
            entities=[uuid4()],
            parameters={},
            provenance={},
        )

        assert con_none.provenance is None
        assert con_empty.provenance == {}

    def test_scope_contextual_constraint(self) -> None:
        """Test constraint with scope for conditional application."""
        scope = {
            "environment": ["production"],
            "time_of_day": ["business_hours"],
        }

        con = Constraint(
            id=uuid4(),
            type="resource_capacity",
            entities=[uuid4()],
            parameters={"max_concurrent": 100},
            scope=scope,
        )

        assert con.scope == scope
