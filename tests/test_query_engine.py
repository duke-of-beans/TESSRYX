"""Unit tests for Query Engine.

Tests the high-level query interface for dependency questions.
"""

from uuid import uuid4

import pytest

from tessryx.core.entity import Entity
from tessryx.core.relation import Relation
from tessryx.kernel.graph_ops import DependencyGraph
from tessryx.kernel.impact_analyzer import DependencyImpactAnalyzer
from tessryx.kernel.query_engine import QueryEngine, QueryType


class TestWhatQueries:
    """Tests for 'what' queries."""

    def test_what_depends_on_leaf(self) -> None:
        """Test what depends on a leaf package (nothing)."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        graph = graph.add_entity(a)

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.what_depends_on(a.id)

        assert result.query_type == QueryType.WHAT_DEPENDS_ON
        assert "Nothing depends on" in result.answer or "leaf" in result.answer
        assert len(result.entities) == 0
        assert result.evidence["is_leaf"]

    def test_what_depends_on_hub(self) -> None:
        """Test what depends on a hub package."""
        graph = DependencyGraph()

        hub = Entity(id=uuid4(), type="package", name="hub")
        deps = [Entity(id=uuid4(), type="package", name=f"dep_{i}") for i in range(5)]

        graph = graph.add_entity(hub)
        for dep in deps:
            graph = graph.add_entity(dep).add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity_id=dep.id, to_entity_id=hub.id)
            )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.what_depends_on(hub.id)

        assert result.query_type == QueryType.WHAT_DEPENDS_ON
        assert "5 package(s) depend on" in result.answer
        assert len(result.entities) == 5
        assert result.evidence["direct_count"] == 5
        assert result.evidence["transitive_count"] == 5

    def test_what_dependencies_root(self) -> None:
        """Test what dependencies for root package (none)."""
        graph = DependencyGraph()
        root = Entity(id=uuid4(), type="package", name="root")
        graph = graph.add_entity(root)

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.what_dependencies(root.id)

        assert result.query_type == QueryType.WHAT_DEPENDENCIES
        assert "no dependencies" in result.answer or "root" in result.answer
        assert len(result.entities) == 0
        assert result.evidence["is_root"]

    def test_what_dependencies_chain(self) -> None:
        """Test what dependencies for package in chain."""
        graph = DependencyGraph()

        # A -> B -> C
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=b.id, to_entity_id=c.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.what_dependencies(a.id)

        assert result.query_type == QueryType.WHAT_DEPENDENCIES
        assert "2 package(s)" in result.answer  # B and C
        assert len(result.entities) == 2
        assert result.evidence["direct_count"] == 1  # Just B
        assert result.evidence["transitive_count"] == 2  # B and C


class TestWhyQueries:
    """Tests for 'why' queries."""

    def test_why_dependency_direct(self) -> None:
        """Test why direct dependency exists."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.why_dependency(a.id, b.id)

        assert result.query_type == QueryType.WHY_DEPENDENCY
        assert "directly depends" in result.answer
        assert len(result.entities) == 2
        assert result.evidence["is_direct"]
        assert result.evidence["hops"] == 1

    def test_why_dependency_transitive(self) -> None:
        """Test why transitive dependency exists."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=b.id, to_entity_id=c.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.why_dependency(a.id, c.id)

        assert result.query_type == QueryType.WHY_DEPENDENCY
        assert "transitively" in result.answer
        assert len(result.entities) == 3
        assert not result.evidence["is_direct"]
        assert result.evidence["hops"] == 2

    def test_why_dependency_no_path(self) -> None:
        """Test why dependency when no path exists."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = graph.add_entity(a).add_entity(b)

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.why_dependency(a.id, b.id)

        assert result.query_type == QueryType.WHY_DEPENDENCY
        assert "does not depend" in result.answer
        assert len(result.entities) == 0

    def test_why_cant_upgrade_circular(self) -> None:
        """Test why can't upgrade when circular dependency exists."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=b.id, to_entity_id=a.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.why_cant_upgrade(a.id)

        assert result.query_type == QueryType.WHY_CANT_UPGRADE
        assert "circular dependency" in result.answer
        assert result.evidence["in_circular"]


class TestImpactQueries:
    """Tests for impact analysis queries."""

    def test_impact_of_change_low(self) -> None:
        """Test impact of change for low-impact package."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.impact_of_change(b.id)

        assert result.query_type == QueryType.IMPACT_ANALYSIS
        assert "Blast radius: 1" in result.answer
        assert result.evidence["is_safe"]

    def test_impact_of_change_high(self) -> None:
        """Test impact of change for high-impact hub."""
        graph = DependencyGraph()
        hub = Entity(id=uuid4(), type="package", name="hub")
        deps = [Entity(id=uuid4(), type="package", name=f"dep_{i}") for i in range(30)]

        graph = graph.add_entity(hub)
        for dep in deps:
            graph = graph.add_entity(dep).add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity_id=dep.id, to_entity_id=hub.id)
            )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.impact_of_change(hub.id)

        assert result.query_type == QueryType.IMPACT_ANALYSIS
        assert "30 package" in result.answer
        assert not result.evidence["is_safe"]

    def test_risk_assessment_low(self) -> None:
        """Test risk assessment for low-risk package."""
        graph = DependencyGraph()
        leaf = Entity(id=uuid4(), type="package", name="leaf")
        graph = graph.add_entity(leaf)

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.risk_assessment(leaf.id)

        assert result.query_type == QueryType.RISK_ASSESSMENT
        assert "LOW" in result.answer
        assert result.evidence["risk_score"] < 0.3


class TestPathQueries:
    """Tests for path queries."""

    def test_how_does_reach_exists(self) -> None:
        """Test path query when path exists."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=b.id, to_entity_id=c.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.how_does_reach(a.id, c.id)

        assert result.query_type == QueryType.PATH_QUERY
        assert "reaches" in result.answer
        assert "a → b → c" in result.answer
        assert len(result.entities) == 3
        assert result.evidence["has_path"]
        assert result.evidence["hops"] == 2

    def test_how_does_reach_no_path(self) -> None:
        """Test path query when no path exists."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = graph.add_entity(a).add_entity(b)

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.how_does_reach(a.id, b.id)

        assert result.query_type == QueryType.PATH_QUERY
        assert "does not reach" in result.answer
        assert len(result.entities) == 0
        assert not result.evidence["has_path"]


class TestCircularQueries:
    """Tests for circular dependency queries."""

    def test_is_circular_yes(self) -> None:
        """Test circular check when entity is in cycle."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=b.id, to_entity_id=a.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.is_circular(a.id)

        assert result.query_type == QueryType.CIRCULAR_CHECK
        assert "circular dependency" in result.answer
        assert result.evidence["is_circular"]
        assert result.evidence["cycle_count"] == 1

    def test_is_circular_no(self) -> None:
        """Test circular check when entity not in cycle."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.is_circular(a.id)

        assert result.query_type == QueryType.CIRCULAR_CHECK
        assert "not in any circular" in result.answer
        assert not result.evidence["is_circular"]

    def test_list_all_cycles_none(self) -> None:
        """Test listing cycles when graph is acyclic."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.list_all_cycles()

        assert result.query_type == QueryType.LIST_CYCLES
        assert "No circular dependencies" in result.answer
        assert result.evidence["cycle_count"] == 0

    def test_list_all_cycles_multiple(self) -> None:
        """Test listing multiple cycles."""
        graph = DependencyGraph()

        # Cycle 1: a ↔ b
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        # Cycle 2: c ↔ d
        c = Entity(id=uuid4(), type="package", name="c")
        d = Entity(id=uuid4(), type="package", name="d")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_entity(d)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=b.id, to_entity_id=a.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=c.id, to_entity_id=d.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=d.id, to_entity_id=c.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        engine = QueryEngine(graph, analyzer)

        result = engine.list_all_cycles()

        assert result.query_type == QueryType.LIST_CYCLES
        assert "2 circular dependency" in result.answer
        assert result.evidence["cycle_count"] == 2
