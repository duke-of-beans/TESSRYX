"""Property-based tests for Graph Operations using Hypothesis.

Property-based testing generates hundreds of random test cases to verify
that algorithms maintain their invariants across all possible inputs.

These tests validate:
- Graph operations maintain consistency
- Algorithms produce correct results for any valid graph
- Edge cases are handled properly
- Performance scales appropriately
"""

from uuid import uuid4

import pytest
from hypothesis import given, settings, strategies as st

from tessryx.core.entity import Entity
from tessryx.core.relation import Relation
from tessryx.kernel.graph_ops import (
    DependencyGraph,
    find_circular_dependencies,
    find_strongly_connected_components,
    get_transitive_dependencies,
    get_transitive_dependents,
    is_reachable,
    topological_sort,
)


# ============================================================================
# HYPOTHESIS STRATEGIES (Test Data Generators)
# ============================================================================


@st.composite
def entity_strategy(draw: st.DrawFn) -> Entity:
    """Generate random Entity."""
    entity_type = draw(st.sampled_from(["package", "module", "class", "function"]))
    name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    
    return Entity(
        id=uuid4(),
        type=entity_type,
        name=name,
    )


@st.composite
def graph_strategy(
    draw: st.DrawFn,
    min_nodes: int = 1,
    max_nodes: int = 20,
    max_edges_per_node: int = 5,
) -> DependencyGraph:
    """Generate random DependencyGraph.
    
    Args:
        draw: Hypothesis draw function
        min_nodes: Minimum number of nodes
        max_nodes: Maximum number of nodes
        max_edges_per_node: Maximum outgoing edges per node
        
    Returns:
        Random graph with entities and relations
    """
    # Generate entities
    num_nodes = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
    entities = [draw(entity_strategy()) for _ in range(num_nodes)]
    
    # Build graph with entities
    graph = DependencyGraph()
    for entity in entities:
        graph = graph.add_entity(entity)
    
    # Generate random edges (avoiding duplicates)
    edges_added = set()
    
    for entity in entities:
        # Random number of outgoing edges
        num_edges = draw(st.integers(min_value=0, max_value=min(max_edges_per_node, len(entities) - 1)))
        
        # Pick random targets (excluding self)
        possible_targets = [e for e in entities if e.id != entity.id]
        if not possible_targets:
            continue
            
        targets = draw(st.lists(
            st.sampled_from(possible_targets),
            min_size=0,
            max_size=num_edges,
            unique=True,
        ))
        
        for target in targets:
            edge_key = (entity.id, target.id)
            if edge_key not in edges_added:
                relation = Relation(
                    id=uuid4(),
                    type="depends_on",
                    from_entity=entity.id,
                    to_entity=target.id,
                )
                graph = graph.add_relation(relation)
                edges_added.add(edge_key)
    
    return graph


@st.composite
def dag_strategy(
    draw: st.DrawFn,
    min_nodes: int = 1,
    max_nodes: int = 20,
) -> DependencyGraph:
    """Generate random DAG (Directed Acyclic Graph).
    
    Creates a graph with a topological ordering, ensuring no cycles.
    
    Args:
        draw: Hypothesis draw function
        min_nodes: Minimum number of nodes
        max_nodes: Maximum number of nodes
        
    Returns:
        Random DAG
    """
    # Generate entities
    num_nodes = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
    entities = [draw(entity_strategy()) for _ in range(num_nodes)]
    
    # Build graph with entities
    graph = DependencyGraph()
    for entity in entities:
        graph = graph.add_entity(entity)
    
    # Add edges that respect topological order (i -> j where i < j in list)
    # This guarantees a DAG
    for i, source in enumerate(entities):
        # Only connect to entities later in the list
        possible_targets = entities[i + 1:]
        if not possible_targets:
            continue
        
        # Random number of outgoing edges
        num_edges = draw(st.integers(min_value=0, max_value=min(3, len(possible_targets))))
        targets = draw(st.lists(
            st.sampled_from(possible_targets),
            min_size=0,
            max_size=num_edges,
            unique=True,
        ))
        
        for target in targets:
            relation = Relation(
                id=uuid4(),
                type="depends_on",
                from_entity=source.id,
                to_entity=target.id,
            )
            graph = graph.add_relation(relation)
    
    return graph


# ============================================================================
# GRAPH PROPERTIES
# ============================================================================


class TestGraphProperties:
    """Property-based tests for DependencyGraph."""

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_node_count_matches_entities(self, graph: DependencyGraph) -> None:
        """Property: Node count equals number of added entities."""
        # Count unique entities by checking all nodes
        nx_graph = graph.to_networkx()
        assert graph.node_count() == len(nx_graph.nodes())

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_get_entity_returns_correct_entity(self, graph: DependencyGraph) -> None:
        """Property: get_entity returns the same entity that was added."""
        nx_graph = graph.to_networkx()
        
        for node_id in nx_graph.nodes():
            entity = graph.get_entity(node_id)
            assert entity is not None
            assert entity.id == node_id

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_dependencies_are_subset_of_nodes(self, graph: DependencyGraph) -> None:
        """Property: All dependencies are valid nodes in the graph."""
        nx_graph = graph.to_networkx()
        all_node_ids = set(nx_graph.nodes())
        
        for node_id in nx_graph.nodes():
            deps = graph.get_dependencies(node_id)
            dep_ids = {d.id for d in deps}
            
            # All dependencies must be valid nodes
            assert dep_ids.issubset(all_node_ids)

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_dependents_are_subset_of_nodes(self, graph: DependencyGraph) -> None:
        """Property: All dependents are valid nodes in the graph."""
        nx_graph = graph.to_networkx()
        all_node_ids = set(nx_graph.nodes())
        
        for node_id in nx_graph.nodes():
            dependents = graph.get_dependents(node_id)
            dependent_ids = {d.id for d in dependents}
            
            # All dependents must be valid nodes
            assert dependent_ids.issubset(all_node_ids)

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_dependency_relation_symmetry(self, graph: DependencyGraph) -> None:
        """Property: If A depends on B, then B has A as a dependent."""
        nx_graph = graph.to_networkx()
        
        for node_id in nx_graph.nodes():
            deps = graph.get_dependencies(node_id)
            
            for dep in deps:
                # dep should list node_id as a dependent
                dep_dependents = graph.get_dependents(dep.id)
                dependent_ids = {d.id for d in dep_dependents}
                assert node_id in dependent_ids


# ============================================================================
# SCC PROPERTIES
# ============================================================================


class TestSCCProperties:
    """Property-based tests for Strongly Connected Components."""

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_scc_partition_is_complete(self, graph: DependencyGraph) -> None:
        """Property: SCCs partition all nodes (every node in exactly one SCC)."""
        sccs = find_strongly_connected_components(graph)
        nx_graph = graph.to_networkx()
        
        # Flatten SCCs to set of all nodes in SCCs
        nodes_in_sccs = set()
        for scc in sccs:
            nodes_in_sccs.update(scc)
        
        # Should equal all nodes in graph
        assert nodes_in_sccs == set(nx_graph.nodes())

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_scc_no_overlap(self, graph: DependencyGraph) -> None:
        """Property: SCCs don't overlap (node in at most one SCC)."""
        sccs = find_strongly_connected_components(graph)
        
        seen = set()
        for scc in sccs:
            scc_set = set(scc)
            # No overlap with previously seen nodes
            assert len(scc_set & seen) == 0
            seen.update(scc_set)

    @given(dag_strategy())
    @settings(max_examples=50)
    def test_dag_has_only_singleton_sccs(self, dag: DependencyGraph) -> None:
        """Property: DAG has only single-node SCCs."""
        sccs = find_strongly_connected_components(dag)
        
        # All SCCs should be size 1
        for scc in sccs:
            assert len(scc) == 1

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_circular_dependencies_are_sccs(self, graph: DependencyGraph) -> None:
        """Property: Circular dependencies are SCCs with size > 1."""
        sccs = find_strongly_connected_components(graph)
        cycles = find_circular_dependencies(graph)
        
        # All cycles should be SCCs with size > 1
        multi_node_sccs = [scc for scc in sccs if len(scc) > 1]
        
        assert len(cycles) == len(multi_node_sccs)


# ============================================================================
# TOPOLOGICAL SORT PROPERTIES
# ============================================================================


class TestTopologicalSortProperties:
    """Property-based tests for topological sorting."""

    @given(dag_strategy())
    @settings(max_examples=50)
    def test_topological_order_respects_dependencies(self, dag: DependencyGraph) -> None:
        """Property: In topological order, dependencies come before dependents."""
        order = topological_sort(dag)
        
        # Create position map
        position = {node_id: i for i, node_id in enumerate(order)}
        
        # Check all edges respect ordering
        nx_graph = dag.to_networkx()
        for source, target in nx_graph.edges():
            # source depends on target, so target should come first
            assert position[target] < position[source], \
                f"Dependency {target} should come before {source} in topological order"

    @given(dag_strategy())
    @settings(max_examples=50)
    def test_topological_sort_includes_all_nodes(self, dag: DependencyGraph) -> None:
        """Property: Topological sort includes every node exactly once."""
        order = topological_sort(dag)
        nx_graph = dag.to_networkx()
        
        assert len(order) == len(nx_graph.nodes())
        assert set(order) == set(nx_graph.nodes())


# ============================================================================
# REACHABILITY PROPERTIES
# ============================================================================


class TestReachabilityProperties:
    """Property-based tests for reachability queries."""

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_reachability_is_reflexive(self, graph: DependencyGraph) -> None:
        """Property: Every node is reachable from itself."""
        nx_graph = graph.to_networkx()
        
        for node_id in nx_graph.nodes():
            assert is_reachable(graph, node_id, node_id)

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_reachability_is_transitive(self, graph: DependencyGraph) -> None:
        """Property: If A reaches B and B reaches C, then A reaches C."""
        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())
        
        if len(nodes) < 3:
            return  # Need at least 3 nodes
        
        # Find a path A -> B -> C
        for a in nodes:
            for b in nodes:
                if a == b or not is_reachable(graph, a, b):
                    continue
                    
                for c in nodes:
                    if c in (a, b) or not is_reachable(graph, b, c):
                        continue
                    
                    # If A -> B and B -> C, then A -> C
                    assert is_reachable(graph, a, c), \
                        f"Transitivity violated: {a} -> {b} -> {c}"

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_path_implies_reachability(self, graph: DependencyGraph) -> None:
        """Property: If a path exists, is_reachable returns True."""
        from tessryx.kernel.graph_ops import find_path
        
        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())
        
        if len(nodes) < 2:
            return
        
        # Check all pairs
        for source in nodes[:min(5, len(nodes))]:  # Limit to first 5 for performance
            for target in nodes:
                if source == target:
                    continue
                
                path = find_path(graph, source, target)
                reachable = is_reachable(graph, source, target)
                
                if path is not None:
                    # Path exists -> must be reachable
                    assert reachable


# ============================================================================
# TRANSITIVE DEPENDENCIES PROPERTIES
# ============================================================================


class TestTransitiveDependenciesProperties:
    """Property-based tests for transitive dependency queries."""

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_transitive_deps_include_direct_deps(self, graph: DependencyGraph) -> None:
        """Property: Transitive dependencies include all direct dependencies."""
        nx_graph = graph.to_networkx()
        
        for node_id in nx_graph.nodes():
            direct = {d.id for d in graph.get_dependencies(node_id)}
            transitive = get_transitive_dependencies(graph, node_id)
            
            # All direct dependencies should be in transitive set
            assert direct.issubset(transitive) or len(direct) == 0

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_transitive_deps_are_reachable(self, graph: DependencyGraph) -> None:
        """Property: All transitive dependencies are reachable."""
        nx_graph = graph.to_networkx()
        
        for node_id in list(nx_graph.nodes())[:5]:  # Check first 5 for performance
            transitive = get_transitive_dependencies(graph, node_id)
            
            for dep_id in transitive:
                assert is_reachable(graph, node_id, dep_id), \
                    f"{dep_id} in transitive deps but not reachable from {node_id}"

    @given(graph_strategy())
    @settings(max_examples=100)
    def test_transitive_dependents_include_direct_dependents(
        self, graph: DependencyGraph
    ) -> None:
        """Property: Transitive dependents include all direct dependents."""
        nx_graph = graph.to_networkx()
        
        for node_id in nx_graph.nodes():
            direct = {d.id for d in graph.get_dependents(node_id)}
            transitive = get_transitive_dependents(graph, node_id)
            
            # All direct dependents should be in transitive set
            assert direct.issubset(transitive) or len(direct) == 0

    @given(dag_strategy())
    @settings(max_examples=50)
    def test_transitive_deps_with_depth_limit(self, dag: DependencyGraph) -> None:
        """Property: Depth-limited transitive deps are subset of unlimited."""
        nx_graph = dag.to_networkx()
        
        for node_id in list(nx_graph.nodes())[:5]:
            unlimited = get_transitive_dependencies(dag, node_id)
            depth_1 = get_transitive_dependencies(dag, node_id, max_depth=1)
            depth_2 = get_transitive_dependencies(dag, node_id, max_depth=2)
            
            # Depth-limited should be subsets
            assert depth_1.issubset(unlimited)
            assert depth_2.issubset(unlimited)
            
            # Deeper limit should include shallower
            assert depth_1.issubset(depth_2) or len(depth_1) == 0


# ============================================================================
# PERFORMANCE SMOKE TESTS
# ============================================================================


class TestPerformanceSmoke:
    """Smoke tests to ensure algorithms scale reasonably."""

    @given(graph_strategy(max_nodes=100, max_edges_per_node=10))
    @settings(max_examples=10, deadline=5000)  # 5 second timeout
    def test_scc_scales_to_100_nodes(self, graph: DependencyGraph) -> None:
        """Smoke test: SCC detection on 100-node graph completes quickly."""
        sccs = find_strongly_connected_components(graph)
        assert len(sccs) > 0  # Sanity check

    @given(dag_strategy(max_nodes=100))
    @settings(max_examples=10, deadline=5000)
    def test_topological_sort_scales_to_100_nodes(self, dag: DependencyGraph) -> None:
        """Smoke test: Topological sort on 100-node DAG completes quickly."""
        order = topological_sort(dag)
        assert len(order) > 0  # Sanity check

    @given(graph_strategy(max_nodes=100, max_edges_per_node=10))
    @settings(max_examples=10, deadline=5000)
    def test_transitive_queries_scale_to_100_nodes(self, graph: DependencyGraph) -> None:
        """Smoke test: Transitive queries on 100-node graph complete quickly."""
        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())
        
        if not nodes:
            return
        
        # Pick random node
        node_id = nodes[0]
        
        deps = get_transitive_dependencies(graph, node_id)
        dependents = get_transitive_dependents(graph, node_id)
        
        # Sanity check - results are valid
        assert isinstance(deps, set)
        assert isinstance(dependents, set)
