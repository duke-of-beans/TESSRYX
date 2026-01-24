"""Unit tests for graph operations module."""

from uuid import UUID, uuid4

import pytest

from tessryx.core.relation import Relation
from tessryx.kernel.graph_ops import GraphDict, GraphOps


class TestBuildGraph:
    """Tests for building graph from relations."""

    def test_empty_relations(self) -> None:
        """Test building graph from empty relations list."""
        graph = GraphOps.build_graph([])
        assert graph == {}

    def test_single_relation(self) -> None:
        """Test building graph from single relation."""
        from_id = uuid4()
        to_id = uuid4()
        rel = Relation(
            id=uuid4(),
            type="requires",
            from_entity=from_id,
            to_entity=to_id,
            strength=0.9,
        )
        graph = GraphOps.build_graph([rel])
        assert from_id in graph
        assert to_id in graph[from_id]
        assert len(graph[from_id]) == 1

    def test_multiple_relations(self) -> None:
        """Test building graph from multiple relations."""
        a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
        relations = [
            Relation(id=uuid4(), type="requires", from_entity=a, to_entity=b, strength=0.9),
            Relation(id=uuid4(), type="requires", from_entity=b, to_entity=c, strength=0.8),
            Relation(id=uuid4(), type="requires", from_entity=a, to_entity=d, strength=0.7),
        ]
        graph = GraphOps.build_graph(relations)
        assert a in graph
        assert set(graph[a]) == {b, d}
        assert b in graph
        assert graph[b] == [c]


class TestTarjanSCC:
    """Tests for Tarjan's SCC algorithm."""

    def test_empty_graph(self) -> None:
        """Test SCC on empty graph."""
        sccs = GraphOps.tarjan_scc({})
        assert sccs == []

    def test_single_node(self) -> None:
        """Test SCC on graph with single isolated node."""
        node = uuid4()
        graph: GraphDict = {node: []}
        sccs = GraphOps.tarjan_scc(graph)
        assert len(sccs) == 1
        assert sccs[0] == [node]

    def test_linear_chain(self) -> None:
        """Test SCC on linear dependency chain (no cycles)."""
        a, b, c = uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: []}
        sccs = GraphOps.tarjan_scc(graph)
        # Should have 3 SCCs (one per node, no cycles)
        assert len(sccs) == 3

    def test_simple_cycle(self) -> None:
        """Test SCC with simple two-node cycle."""
        a, b = uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [a]}
        sccs = GraphOps.tarjan_scc(graph)
        # Should find one SCC with both nodes
        assert len(sccs) == 1
        assert set(sccs[0]) == {a, b}

    def test_complex_graph(self) -> None:
        """Test SCC on complex graph with multiple components."""
        a, b, c, d, e = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
        graph: GraphDict = {
            a: [b],
            b: [c],
            c: [a],  # Cycle: a -> b -> c -> a
            d: [e],
            e: [],
        }
        sccs = GraphOps.tarjan_scc(graph)
        # Should have 3 SCCs: {a, b, c}, {d}, {e}
        assert len(sccs) == 3
        # Find the cycle SCC
        cycle_scc = next(scc for scc in sccs if len(scc) == 3)
        assert set(cycle_scc) == {a, b, c}


class TestDetectCycles:
    """Tests for cycle detection."""

    def test_no_cycles(self) -> None:
        """Test graph with no cycles."""
        a, b, c = uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: []}
        cycles = GraphOps.detect_cycles(graph)
        assert cycles == []

    def test_self_loop(self) -> None:
        """Test detection of self-loop."""
        a = uuid4()
        graph: GraphDict = {a: [a]}
        cycles = GraphOps.detect_cycles(graph)
        assert len(cycles) == 1
        assert cycles[0] == [a]

    def test_simple_cycle(self) -> None:
        """Test detection of simple cycle."""
        a, b = uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [a]}
        cycles = GraphOps.detect_cycles(graph)
        assert len(cycles) == 1
        assert set(cycles[0]) == {a, b}

    def test_multiple_cycles(self) -> None:
        """Test detection of multiple independent cycles."""
        a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
        graph: GraphDict = {
            a: [b],
            b: [a],  # Cycle 1
            c: [d],
            d: [c],  # Cycle 2
        }
        cycles = GraphOps.detect_cycles(graph)
        assert len(cycles) == 2


class TestTopologicalSort:
    """Tests for topological sorting."""

    def test_empty_graph(self) -> None:
        """Test topological sort on empty graph."""
        result = GraphOps.topological_sort({})
        assert result == []

    def test_linear_chain(self) -> None:
        """Test topological sort on linear dependency chain."""
        a, b, c = uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: []}
        result = GraphOps.topological_sort(graph)
        assert result is not None
        # a must come before b, b before c
        assert result.index(a) < result.index(b)
        assert result.index(b) < result.index(c)

    def test_dag_multiple_paths(self) -> None:
        """Test topological sort on DAG with multiple valid orderings."""
        a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b, c], b: [d], c: [d], d: []}
        result = GraphOps.topological_sort(graph)
        assert result is not None
        # Verify all dependencies are satisfied
        assert result.index(a) < result.index(b)
        assert result.index(a) < result.index(c)
        assert result.index(b) < result.index(d)
        assert result.index(c) < result.index(d)

    def test_cycle_detection(self) -> None:
        """Test that topological sort returns None for cyclic graph."""
        a, b, c = uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: [a]}
        result = GraphOps.topological_sort(graph)
        assert result is None


class TestBlastRadius:
    """Tests for blast radius calculation."""

    def test_isolated_node(self) -> None:
        """Test blast radius for isolated node."""
        a = uuid4()
        graph: GraphDict = {a: []}
        radius = GraphOps.blast_radius(graph, a)
        assert radius == set()

    def test_linear_chain(self) -> None:
        """Test blast radius on linear chain."""
        a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: [d], d: []}
        radius = GraphOps.blast_radius(graph, a)
        assert radius == {b, c, d}

    def test_tree_structure(self) -> None:
        """Test blast radius on tree structure."""
        a, b, c, d, e = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b, c], b: [d], c: [e], d: [], e: []}
        radius = GraphOps.blast_radius(graph, a)
        assert radius == {b, c, d, e}

    def test_max_depth_limit(self) -> None:
        """Test blast radius with depth limit."""
        a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: [d], d: []}
        radius = GraphOps.blast_radius(graph, a, max_depth=2)
        # Should only get b and c (depth 1 and 2)
        assert radius == {b, c}

    def test_nonexistent_entity(self) -> None:
        """Test blast radius for entity not in graph."""
        a = uuid4()
        nonexistent = uuid4()
        graph: GraphDict = {a: []}
        radius = GraphOps.blast_radius(graph, nonexistent)
        assert radius == set()


class TestReverseGraph:
    """Tests for graph reversal."""

    def test_empty_graph(self) -> None:
        """Test reversing empty graph."""
        reversed_graph = GraphOps.reverse_graph({})
        assert reversed_graph == {}

    def test_simple_reversal(self) -> None:
        """Test reversing simple graph."""
        a, b = uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: []}
        reversed_graph = GraphOps.reverse_graph(graph)
        assert a in reversed_graph
        assert b in reversed_graph
        assert reversed_graph[a] == []
        assert reversed_graph[b] == [a]

    def test_complex_reversal(self) -> None:
        """Test reversing complex graph."""
        a, b, c = uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b, c], b: [c], c: []}
        reversed_graph = GraphOps.reverse_graph(graph)
        assert set(reversed_graph[c]) == {a, b}
        assert reversed_graph[b] == [a]
        assert reversed_graph[a] == []


class TestUpstreamDependencies:
    """Tests for upstream dependency calculation."""

    def test_root_node(self) -> None:
        """Test upstream dependencies for root node (no dependencies)."""
        a, b, c = uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: []}
        upstream = GraphOps.upstream_dependencies(graph, a)
        assert upstream == set()

    def test_leaf_node(self) -> None:
        """Test upstream dependencies for leaf node."""
        a, b, c = uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: []}
        upstream = GraphOps.upstream_dependencies(graph, c)
        assert upstream == {a, b}

    def test_middle_node(self) -> None:
        """Test upstream dependencies for middle node."""
        a, b, c = uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: []}
        upstream = GraphOps.upstream_dependencies(graph, b)
        assert upstream == {a}

    def test_max_depth_limit(self) -> None:
        """Test upstream dependencies with depth limit."""
        a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
        graph: GraphDict = {a: [b], b: [c], c: [d], d: []}
        upstream = GraphOps.upstream_dependencies(graph, d, max_depth=2)
        # Should only get c and b (depth 1 and 2)
        assert upstream == {b, c}
