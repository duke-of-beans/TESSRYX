"""Unit tests for Entity primitive."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from tessryx.core.entity import Entity, EntityType


class TestEntityCreation:
    """Test entity creation and validation."""

    def test_create_minimal_entity(self) -> None:
        """Test creating entity with minimal required fields."""
        entity_id = uuid4()
        entity = Entity(
            id=entity_id,
            type="component",
            name="test-entity",
        )

        assert entity.id == entity_id
        assert entity.type == "component"
        assert entity.name == "test-entity"
        assert entity.version is None
        assert entity.parent is None
        assert entity.children == []
        assert entity.metadata == {}

    def test_create_full_entity(self) -> None:
        """Test creating entity with all fields."""
        entity_id = uuid4()
        parent_id = uuid4()
        child_id = uuid4()

        entity = Entity(
            id=entity_id,
            type="package",
            name="react",
            version="18.2.0",
            parent=parent_id,
            children=[child_id],
            metadata={"language": "javascript", "license": "MIT"},
        )

        assert entity.id == entity_id
        assert entity.type == "package"
        assert entity.name == "react"
        assert entity.version == "18.2.0"
        assert entity.parent == parent_id
        assert entity.children == [child_id]
        assert entity.metadata["language"] == "javascript"

    def test_entity_immutable(self) -> None:
        """Test that entities are immutable (frozen)."""
        entity = Entity(
            id=uuid4(),
            type="component",
            name="test",
        )

        with pytest.raises(ValidationError):
            entity.name = "new-name"  # type: ignore

    def test_timestamps_auto_generated(self) -> None:
        """Test that timestamps are automatically generated."""
        before = datetime.utcnow()
        entity = Entity(
            id=uuid4(),
            type="component",
            name="test",
        )
        after = datetime.utcnow()

        assert before <= entity.created_at <= after
        assert before <= entity.updated_at <= after


class TestEntityValidation:
    """Test entity validation rules."""

    def test_empty_name_rejected(self) -> None:
        """Test that empty names are rejected."""
        with pytest.raises(ValidationError):
            Entity(
                id=uuid4(),
                type="component",
                name="",  # Empty name should fail
            )

    def test_type_too_long_rejected(self) -> None:
        """Test that types longer than 50 chars are rejected."""
        with pytest.raises(ValidationError):
            Entity(
                id=uuid4(),
                type="a" * 51,  # 51 chars, should fail
                name="test",
            )


class TestEntityHelpers:
    """Test entity helper methods."""

    def test_has_parent(self) -> None:
        """Test has_parent() method."""
        entity_with_parent = Entity(
            id=uuid4(),
            type="component",
            name="test",
            parent=uuid4(),
        )
        entity_without_parent = Entity(
            id=uuid4(),
            type="component",
            name="test",
        )

        assert entity_with_parent.has_parent()
        assert not entity_without_parent.has_parent()

    def test_has_children(self) -> None:
        """Test has_children() method."""
        entity_with_children = Entity(
            id=uuid4(),
            type="component",
            name="test",
            children=[uuid4()],
        )
        entity_without_children = Entity(
            id=uuid4(),
            type="component",
            name="test",
        )

        assert entity_with_children.has_children()
        assert not entity_without_children.has_children()

    def test_is_leaf(self) -> None:
        """Test is_leaf() method."""
        leaf = Entity(
            id=uuid4(),
            type="component",
            name="test",
        )
        parent = Entity(
            id=uuid4(),
            type="component",
            name="test",
            children=[uuid4()],
        )

        assert leaf.is_leaf()
        assert not parent.is_leaf()


class TestEntityStringRepresentations:
    """Test entity string representations."""

    def test_str_without_version(self) -> None:
        """Test __str__ without version."""
        entity = Entity(
            id=uuid4(),
            type="package",
            name="express",
        )

        assert str(entity) == "express (package)"

    def test_str_with_version(self) -> None:
        """Test __str__ with version."""
        entity = Entity(
            id=uuid4(),
            type="package",
            name="react",
            version="18.2.0",
        )

        assert str(entity) == "react@18.2.0 (package)"

    def test_repr(self) -> None:
        """Test __repr__ representation."""
        entity_id = uuid4()
        entity = Entity(
            id=entity_id,
            type="package",
            name="react",
        )

        repr_str = repr(entity)
        assert "Entity" in repr_str
        assert str(entity_id) in repr_str
        assert "package" in repr_str
        assert "react" in repr_str


class TestEntityTypeEnum:
    """Test EntityType enum."""

    def test_base_entity_types(self) -> None:
        """Test that base entity types are defined."""
        assert EntityType.COMPONENT == "component"
        assert EntityType.RESOURCE == "resource"
        assert EntityType.TASK == "task"
        assert EntityType.GATE == "gate"

    def test_entity_type_usage(self) -> None:
        """Test using EntityType enum in entity creation."""
        entity = Entity(
            id=uuid4(),
            type=EntityType.COMPONENT.value,
            name="test",
        )

        assert entity.type == "component"
