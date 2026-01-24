"""Unit tests for Dependency Impact Analyzer.

Tests the S02 steal from Eye-of-Sauron: blast radius calculation, critical path
identification, and comprehensive impact metrics.
"""

from uuid import uuid4

import pytest

from tessryx.core.entity import Entity
from tessryx.core.relation import Relation
from tessryx.kernel.graph_ops import DependencyGraph
from tessryx.kernel.impact_analyzer import (
    DependencyImpactAnalyzer,
    ImpactSeverity,
)


class TestImpactMetrics:
    """Tests for impact metrics calculation."""

    def test_calculate_metrics_isolated_node(self) -> None:
        """Test metrics for isolated node (no dependencies or dependents)."""
        graph = DependencyGraph()
        entity = Entity(id=uuid4(), type="package", name="isolated")
        graph = graph.add_entity(entity)

        analyzer = DependencyImpactAnalyzer(graph)
        metrics = analyzer.calculate_impact_metrics(entity.id)

        assert metrics.direct_dependents == 0
        assert metrics.total_dependents == 0
        assert metrics.direct_dependencies == 0
        assert metrics.total_dependencies == 0
        assert metrics.severity == ImpactSeverity.MINIMAL
        assert metrics.is_leaf()

    def test_calculate_metrics_simple_chain(self) -> None:
        """Test metrics for simple dependency chain."""
        graph = DependencyGraph()

        # A -> B -> C
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=c.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)

        # Metrics for C (leaf)
        c_metrics = analyzer.calculate_impact_metrics(c.id)
        assert c_metrics.direct_dependents == 1  # B
        assert c_metrics.total_dependents == 2  # A and B
        assert c_metrics.is_leaf() is False

        # Metrics for B (middle)
        b_metrics = analyzer.calculate_impact_metrics(b.id)
        assert b_metrics.direct_dependents == 1  # A
        assert b_metrics.total_dependents == 1  # A
        assert b_metrics.direct_dependencies == 1  # C
        assert b_metrics.total_dependencies == 1  # C

        # Metrics for A (root)
        a_metrics = analyzer.calculate_impact_metrics(a.id)
        assert a_metrics.direct_dependents == 0
        assert a_metrics.total_dependents == 0
        assert a_metrics.direct_dependencies == 1  # B
        assert a_metrics.total_dependencies == 2  # B and C
        assert a_metrics.is_leaf()

    def test_blast_radius_calculation(self) -> None:
        """Test blast radius (total dependents) calculation."""
        graph = DependencyGraph()

        # Star topology: A, B, C all depend on D
        #   A   B   C
        #    \ | /
        #      D
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")
        d = Entity(id=uuid4(), type="package", name="d")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_entity(d)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=d.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=d.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=c.id, to_entity=d.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)
        metrics = analyzer.calculate_impact_metrics(d.id)

        # D has blast radius of 3 (A, B, C)
        assert metrics.blast_radius() == 3
        assert metrics.direct_dependents == 3

    def test_severity_classification(self) -> None:
        """Test severity classification based on blast radius."""
        graph = DependencyGraph()
        analyzer = DependencyImpactAnalyzer(graph)

        # Create hub with controlled number of dependents
        def create_graph_with_dependents(n: int) -> DependencyGraph:
            """Helper to create graph with N dependents of a hub."""
            g = DependencyGraph()
            hub = Entity(id=uuid4(), type="package", name="hub")
            g = g.add_entity(hub)

            for i in range(n):
                dependent = Entity(id=uuid4(), type="package", name=f"dep_{i}")
                g = g.add_entity(dependent).add_relation(
                    Relation(
                        id=uuid4(),
                        type="depends_on",
                        from_entity=dependent.id,
                        to_entity=hub.id,
                    )
                )

            return g, hub.id

        # MINIMAL: < 5
        g, hub_id = create_graph_with_dependents(3)
        analyzer.graph = g
        assert analyzer.calculate_impact_metrics(hub_id).severity == ImpactSeverity.MINIMAL

        # LOW: 5-20
        g, hub_id = create_graph_with_dependents(10)
        analyzer.graph = g
        assert analyzer.calculate_impact_metrics(hub_id).severity == ImpactSeverity.LOW

        # MEDIUM: 21-100
        g, hub_id = create_graph_with_dependents(50)
        analyzer.graph = g
        assert analyzer.calculate_impact_metrics(hub_id).severity == ImpactSeverity.MEDIUM

        # HIGH: 101-500
        g, hub_id = create_graph_with_dependents(200)
        analyzer.graph = g
        assert analyzer.calculate_impact_metrics(hub_id).severity == ImpactSeverity.HIGH

        # CRITICAL: > 500
        g, hub_id = create_graph_with_dependents(600)
        analyzer.graph = g
        assert analyzer.calculate_impact_metrics(hub_id).severity == ImpactSeverity.CRITICAL

    def test_hub_detection(self) -> None:
        """Test hub detection (>10 direct dependents)."""
        graph = DependencyGraph()

        hub = Entity(id=uuid4(), type="package", name="hub")
        graph = graph.add_entity(hub)

        # Add 15 dependents
        for i in range(15):
            dep = Entity(id=uuid4(), type="package", name=f"dep_{i}")
            graph = graph.add_entity(dep).add_relation(
                Relation(
                    id=uuid4(), type="depends_on", from_entity=dep.id, to_entity=hub.id
                )
            )

        analyzer = DependencyImpactAnalyzer(graph)
        metrics = analyzer.calculate_impact_metrics(hub.id)

        assert metrics.is_hub()
        assert not metrics.is_leaf()

    def test_circular_dependency_detection(self) -> None:
        """Test detection of circular dependencies."""
        graph = DependencyGraph()

        # Cycle: A -> B -> C -> A
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=c.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=c.id, to_entity=a.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)
        metrics = analyzer.calculate_impact_metrics(a.id)

        # A is in one circular dependency
        assert metrics.circular_dependencies == 1


class TestCriticalPath:
    """Tests for critical path analysis."""

    def test_critical_path_linear(self) -> None:
        """Test critical path on linear chain."""
        graph = DependencyGraph()

        # A -> B -> C -> D
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")
        d = Entity(id=uuid4(), type="package", name="d")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_entity(d)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=c.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=c.id, to_entity=d.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)
        critical = analyzer.find_critical_path()

        assert critical is not None
        assert critical.length == 4
        assert critical.path == (a.id, b.id, c.id, d.id)
        assert critical.get_bottleneck() == a.id

    def test_critical_path_diamond(self) -> None:
        """Test critical path with diamond graph."""
        graph = DependencyGraph()

        # A -> B -> D
        # A -> C -> D (C -> D is longer)
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")
        d = Entity(id=uuid4(), type="package", name="d")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_entity(d)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=c.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=d.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=c.id, to_entity=d.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)
        critical = analyzer.find_critical_path()

        assert critical is not None
        # Both paths have same length
        assert critical.length == 3

    def test_critical_path_with_cycle(self) -> None:
        """Test critical path returns None for cyclic graph."""
        graph = DependencyGraph()

        # Cycle: A -> B -> A
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=a.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)
        critical = analyzer.find_critical_path()

        # Cannot compute critical path with cycles
        assert critical is None

    def test_critical_path_marking_in_metrics(self) -> None:
        """Test that metrics correctly identify entities on critical path."""
        graph = DependencyGraph()

        # A -> B -> C
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=c.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)

        # All should be on critical path
        assert analyzer.calculate_impact_metrics(a.id).is_critical_path
        assert analyzer.calculate_impact_metrics(b.id).is_critical_path
        assert analyzer.calculate_impact_metrics(c.id).is_critical_path


class TestChangeImpactAnalysis:
    """Tests for comprehensive change impact analysis."""

    def test_analyze_low_impact_change(self) -> None:
        """Test analysis of low-impact change."""
        graph = DependencyGraph()

        # Simple: A -> B
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = graph.add_entity(a).add_entity(b).add_relation(
            Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
        )

        analyzer = DependencyImpactAnalyzer(graph)
        impact = analyzer.analyze_change_impact(b.id)

        # B only affects A
        assert len(impact.affected_entities) == 1
        assert a.id in impact.affected_entities
        assert impact.metrics.severity == ImpactSeverity.MINIMAL
        assert impact.is_safe_to_change()
        assert not impact.requires_coordination()

    def test_analyze_high_impact_change(self) -> None:
        """Test analysis of high-impact change."""
        graph = DependencyGraph()

        # Hub with 150 dependents
        hub = Entity(id=uuid4(), type="package", name="hub")
        graph = graph.add_entity(hub)

        for i in range(150):
            dep = Entity(id=uuid4(), type="package", name=f"dep_{i}")
            graph = graph.add_entity(dep).add_relation(
                Relation(
                    id=uuid4(), type="depends_on", from_entity=dep.id, to_entity=hub.id
                )
            )

        analyzer = DependencyImpactAnalyzer(graph)
        impact = analyzer.analyze_change_impact(hub.id)

        # Hub affects 150 entities
        assert len(impact.affected_entities) == 150
        assert impact.metrics.severity == ImpactSeverity.HIGH
        assert impact.metrics.is_high_risk()
        assert not impact.is_safe_to_change()
        assert impact.requires_coordination()
        assert impact.risk_score > 0.3

    def test_recommendations_for_hub(self) -> None:
        """Test recommendations for hub entity."""
        graph = DependencyGraph()

        # Hub with 15 dependents
        hub = Entity(id=uuid4(), type="package", name="hub")
        graph = graph.add_entity(hub)

        for i in range(15):
            dep = Entity(id=uuid4(), type="package", name=f"dep_{i}")
            graph = graph.add_entity(dep).add_relation(
                Relation(
                    id=uuid4(), type="depends_on", from_entity=dep.id, to_entity=hub.id
                )
            )

        analyzer = DependencyImpactAnalyzer(graph)
        impact = analyzer.analyze_change_impact(hub.id)

        # Should have recommendation about gradual rollout
        recs = " ".join(impact.recommendations)
        assert "gradual rollout" in recs or "feature flags" in recs

    def test_recommendations_for_circular_dependency(self) -> None:
        """Test recommendations when circular dependencies exist."""
        graph = DependencyGraph()

        # Cycle: A -> B -> C -> A
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=c.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=c.id, to_entity=a.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)
        impact = analyzer.analyze_change_impact(a.id)

        # Should warn about circular dependency
        recs = " ".join(impact.recommendations)
        assert "circular" in recs.lower()
        assert len(impact.circular_dependency_chains) == 1

    def test_recommendations_for_critical_path(self) -> None:
        """Test recommendations for entity on critical path."""
        graph = DependencyGraph()

        # Linear chain (all on critical path)
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=c.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)
        impact = analyzer.analyze_change_impact(b.id)

        # Should warn about critical path
        recs = " ".join(impact.recommendations)
        assert "critical path" in recs.lower() or "bottleneck" in recs.lower()

    def test_risk_score_calculation(self) -> None:
        """Test risk score calculation."""
        graph = DependencyGraph()
        analyzer = DependencyImpactAnalyzer(graph)

        # Low risk: isolated node
        isolated = Entity(id=uuid4(), type="package", name="isolated")
        graph = graph.add_entity(isolated)
        analyzer.graph = graph
        impact = analyzer.analyze_change_impact(isolated.id)
        assert impact.risk_score < 0.2

        # Medium risk: small hub
        hub = Entity(id=uuid4(), type="package", name="hub")
        g = DependencyGraph().add_entity(hub)
        for i in range(20):
            dep = Entity(id=uuid4(), type="package", name=f"dep_{i}")
            g = g.add_entity(dep).add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=dep.id, to_entity=hub.id)
            )
        analyzer.graph = g
        impact = analyzer.analyze_change_impact(hub.id)
        assert 0.2 <= impact.risk_score <= 0.6

        # High risk: large hub
        big_hub = Entity(id=uuid4(), type="package", name="big_hub")
        g = DependencyGraph().add_entity(big_hub)
        for i in range(500):
            dep = Entity(id=uuid4(), type="package", name=f"dep_{i}")
            g = g.add_entity(dep).add_relation(
                Relation(
                    id=uuid4(), type="depends_on", from_entity=dep.id, to_entity=big_hub.id
                )
            )
        analyzer.graph = g
        impact = analyzer.analyze_change_impact(big_hub.id)
        assert impact.risk_score > 0.5


class TestBottleneckDetection:
    """Tests for bottleneck identification."""

    def test_find_bottlenecks(self) -> None:
        """Test finding bottleneck entities."""
        graph = DependencyGraph()

        # Create various entities with different dependent counts
        entities = []
        for i, dep_count in enumerate([5, 15, 25, 8, 12]):
            hub = Entity(id=uuid4(), type="package", name=f"hub_{i}")
            graph = graph.add_entity(hub)
            entities.append((hub, dep_count))

            for j in range(dep_count):
                dep = Entity(id=uuid4(), type="package", name=f"dep_{i}_{j}")
                graph = graph.add_entity(dep).add_relation(
                    Relation(
                        id=uuid4(), type="depends_on", from_entity=dep.id, to_entity=hub.id
                    )
                )

        analyzer = DependencyImpactAnalyzer(graph)
        bottlenecks = analyzer.find_bottlenecks(min_dependents=10)

        # Should find 3 bottlenecks (15, 25, 12 dependents)
        assert len(bottlenecks) == 3

        # Should be sorted by dependent count (descending)
        assert bottlenecks[0][1] == 25  # Highest
        assert bottlenecks[1][1] == 15
        assert bottlenecks[2][1] == 12

    def test_find_blast_radius(self) -> None:
        """Test blast radius calculation."""
        graph = DependencyGraph()

        # A -> B -> C -> D
        # E -> C
        # Changing C affects A, B, E
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")
        d = Entity(id=uuid4(), type="package", name="d")
        e = Entity(id=uuid4(), type="package", name="e")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_entity(d)
            .add_entity(e)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=c.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=c.id, to_entity=d.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=e.id, to_entity=c.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)
        blast = analyzer.find_blast_radius(c.id)

        assert len(blast) == 3
        assert {a.id, b.id, e.id} == blast


class TestDepthCalculation:
    """Tests for depth calculation in metrics."""

    def test_deployment_depth(self) -> None:
        """Test deployment depth calculation."""
        graph = DependencyGraph()

        # A -> B -> C -> D
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")
        d = Entity(id=uuid4(), type="package", name="d")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_entity(d)
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=c.id)
            )
            .add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity=c.id, to_entity=d.id)
            )
        )

        analyzer = DependencyImpactAnalyzer(graph)

        # D is at deployment depth 3 (A -> B -> C all depend on it)
        d_metrics = analyzer.calculate_impact_metrics(d.id)
        assert d_metrics.deployment_depth() == 3

        # A is at deployment depth 0 (nothing depends on it)
        a_metrics = analyzer.calculate_impact_metrics(a.id)
        assert a_metrics.deployment_depth() == 0
