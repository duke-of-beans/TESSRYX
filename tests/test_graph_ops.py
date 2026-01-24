"""Unit tests for Graph Operations.

Tests core graph algorithms: SCC detection, topological sort, reachability,
and transitive dependency queries.
"""

from uuid import uuid4

import pytest

from tessryx.core.entity import Entity
from tessryx.core.relation import Relation
from tessryx.kernel.graph_ops import (
    CycleDetectedError,
    DependencyGraph,
    find_all_paths,
    find_circular_dependencies,
    find_path,
    find_strongly_connected_components,
    get_transitive_dependencies,
    get_transitive_dependents,
    is_reachable,
    topological_sort,
)


class TestDependencyGraph:
    """Tests for DependencyGraph class."""

    def test_init_empty_graph(self) -> None:
        """Test creating empty graph."""
        graph = DependencyGraph()
        assert graph.node_count() == 0
        assert graph.edge_count() == 0

    def test_add_entity(self) -> None:
        """Test adding entity to graph."""
        graph = DependencyGraph()
        entity = Entity(id=uuid4(), type="package", name="react")

        graph = graph.add_entity(entity)

        assert graph.node_count() == 1
        assert graph.get_entity(entity.id) == entity

    def test_add_duplicate_entity(self) -> None:
        """Test that adding duplicate entity raises error."""
        graph = DependencyGraph()
        entity = Entity(id=uuid4(), type="package", name="react")

        graph = graph.add_entity(entity)

        with pytest.raises(ValueError, match="already exists"):
            graph.add_entity(entity)

    def test_add_relation(self) -> None:
        """Test adding relation between entities."""
        graph = DependencyGraph()

        e1 = Entity(id=uuid4(), type="package", name="a")
        e2 = Entity(id=uuid4(), type="package", name="b")

        graph = graph.add_entity(e1).add_entity(e2)

        relation = Relation(
            id=uuid4(),
            type="depends_on",
            from_entity=e1.id,
            to_entity=e2.id,
        )

        graph = graph.add_relation(relation)

        assert graph.edge_count() == 1
        assert graph.get_relation(e1.id, e2.id) == relation

    def test_add_relation_missing_source(self) -> None:
        """Test that adding relation with missing source raises error."""
        graph = DependencyGraph()

        e1 = Entity(id=uuid4(), type="package", name="a")
        missing_id = uuid4()

        graph = graph.add_entity(e1)

        relation = Relation(
            id=uuid4(),
            type="depends_on",
            from_entity=missing_id,
            to_entity=e1.id,
        )

        with pytest.raises(ValueError, match="not in graph"):
            graph.add_relation(relation)

    def test_get_dependencies(self) -> None:
        """Test getting direct dependencies."""
        graph = DependencyGraph()

        # A depends on B and C
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = graph.add_entity(a).add_entity(b).add_entity(c)

        r1 = Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
        r2 = Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=c.id)

        graph = graph.add_relation(r1).add_relation(r2)

        deps = graph.get_dependencies(a.id)
        assert len(deps) == 2
        assert b in deps
        assert c in deps

    def test_get_dependents(self) -> None:
        """Test getting direct dependents."""
        graph = DependencyGraph()

        # A and B depend on C
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = graph.add_entity(a).add_entity(b).add_entity(c)

        r1 = Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=c.id)
        r2 = Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=c.id)

        graph = graph.add_relation(r1).add_relation(r2)

        dependents = graph.get_dependents(c.id)
        assert len(dependents) == 2
        assert a in dependents
        assert b in dependents

    def test_immutability(self) -> None:
        """Test that graph operations are immutable."""
        graph1 = DependencyGraph()
        entity = Entity(id=uuid4(), type="package", name="react")

        graph2 = graph1.add_entity(entity)

        # graph1 should be unchanged
        assert graph1.node_count() == 0
        # graph2 should have the entity
        assert graph2.node_count() == 1


class TestStronglyConnectedComponents:
    """Tests for SCC detection."""

    def test_scc_no_cycles(self) -> None:
        """Test SCC detection on acyclic graph."""
        graph = DependencyGraph()

        # Linear chain: A -> B -> C
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

        sccs = find_strongly_connected_components(graph)

        # Each node is its own SCC
        assert len(sccs) == 3
        assert all(len(scc) == 1 for scc in sccs)

    def test_scc_simple_cycle(self) -> None:
        """Test SCC detection with simple cycle."""
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

        sccs = find_strongly_connected_components(graph)

        # All three nodes in one SCC
        assert len(sccs) == 1
        assert len(sccs[0]) == 3

    def test_find_circular_dependencies(self) -> None:
        """Test finding circular dependencies."""
        graph = DependencyGraph()

        # Cycle: A -> B -> A
        # Isolated node: C
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
                Relation(id=uuid4(), type="depends_on", from_entity=b.id, to_entity=a.id)
            )
        )

        cycles = find_circular_dependencies(graph)

        # Should find one cycle
        assert len(cycles) == 1
        assert len(cycles[0]) == 2
        assert set(cycles[0]) == {a.id, b.id}


class TestTopologicalSort:
    """Tests for topological sort."""

    def test_topological_sort_linear(self) -> None:
        """Test topological sort on linear chain."""
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

        order = topological_sort(graph)

        # C should come before B, B before A
        c_idx = order.index(c.id)
        b_idx = order.index(b.id)
        a_idx = order.index(a.id)

        assert c_idx < b_idx < a_idx

    def test_topological_sort_diamond(self) -> None:
        """Test topological sort on diamond graph."""
        graph = DependencyGraph()

        # A depends on B and C, both B and C depend on D
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D
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

        order = topological_sort(graph)

        # D must come before both B and C
        # Both B and C must come before A
        d_idx = order.index(d.id)
        b_idx = order.index(b.id)
        c_idx = order.index(c.id)
        a_idx = order.index(a.id)

        assert d_idx < b_idx
        assert d_idx < c_idx
        assert b_idx < a_idx
        assert c_idx < a_idx

    def test_topological_sort_with_cycle(self) -> None:
        """Test that topological sort raises error on cyclic graph."""
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

        with pytest.raises(CycleDetectedError):
            topological_sort(graph)


class TestReachability:
    """Tests for reachability queries."""

    def test_is_reachable_direct(self) -> None:
        """Test reachability with direct edge."""
        graph = DependencyGraph()

        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = graph.add_entity(a).add_entity(b).add_relation(
            Relation(id=uuid4(), type="depends_on", from_entity=a.id, to_entity=b.id)
        )

        assert is_reachable(graph, a.id, b.id)
        assert not is_reachable(graph, b.id, a.id)

    def test_is_reachable_transitive(self) -> None:
        """Test reachability through transitive path."""
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

        # A can reach C transitively
        assert is_reachable(graph, a.id, c.id)

    def test_find_path(self) -> None:
        """Test finding shortest path."""
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

        path = find_path(graph, a.id, c.id)

        assert path == [a.id, b.id, c.id]

    def test_find_path_no_path(self) -> None:
        """Test finding path when none exists."""
        graph = DependencyGraph()

        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = graph.add_entity(a).add_entity(b)

        path = find_path(graph, a.id, b.id)

        assert path is None

    def test_find_all_paths(self) -> None:
        """Test finding multiple paths."""
        graph = DependencyGraph()

        # Two paths from A to D:
        # A -> B -> D
        # A -> C -> D
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

        paths = find_all_paths(graph, a.id, d.id)

        assert len(paths) == 2
        assert [a.id, b.id, d.id] in paths
        assert [a.id, c.id, d.id] in paths


class TestTransitiveDependencies:
    """Tests for transitive dependency queries."""

    def test_transitive_dependencies_simple(self) -> None:
        """Test getting transitive dependencies."""
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

        deps = get_transitive_dependencies(graph, a.id)

        assert deps == {b.id, c.id, d.id}

    def test_transitive_dependencies_with_max_depth(self) -> None:
        """Test transitive dependencies with depth limit."""
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

        # Depth 1: only direct dependencies
        deps = get_transitive_dependencies(graph, a.id, max_depth=1)
        assert deps == {b.id}

        # Depth 2: two levels
        deps = get_transitive_dependencies(graph, a.id, max_depth=2)
        assert deps == {b.id, c.id}

    def test_transitive_dependents(self) -> None:
        """Test getting transitive dependents."""
        graph = DependencyGraph()

        # A -> B -> C -> D
        # All of A, B, C depend on D (transitively)
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

        dependents = get_transitive_dependents(graph, d.id)

        assert dependents == {a.id, b.id, c.id}
