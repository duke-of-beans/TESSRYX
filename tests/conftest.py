"""Test configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_entity_id():
    """Provide a sample UUID for testing."""
    from uuid import UUID

    return UUID("550e8400-e29b-41d4-a716-446655440000")


@pytest.fixture
def sample_relation_id():
    """Provide a sample relation UUID for testing."""
    from uuid import UUID

    return UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


@pytest.fixture
def sample_constraint_id():
    """Provide a sample constraint UUID for testing."""
    from uuid import UUID

    return UUID("c1c2c3c4-d5d6-7890-abcd-ef1234567890")
