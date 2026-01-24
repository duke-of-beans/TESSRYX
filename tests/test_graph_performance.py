"""Performance benchmarks for Graph Operations.

Measures algorithm performance at various scales to validate O(V+E) complexity
and identify bottlenecks.

Run with: pytest tests/test_graph_performance.py -v --benchmark-only
"""

import time
from uuid import uuid4

import pytest

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
from tessryx.kernel.impact_analyzer import DependencyImpactAnalyzer


# ============================================================================
# GRAPH GENERATION HELPERS
# ============================================================================


def generate_linear_chain(n: int) -> DependencyGraph:
    """Generate linear dependency chain: A -> B -> C -> ... -> N.
    
    Args:
        n: Number of nodes
        
    Returns:
        Graph with n nodes in a linear chain
    """
    entities = [Entity(id=uuid4(), type="package", name=f"pkg_{i}") for i in range(n)]
    
    graph = DependencyGraph()
    for entity in entities:
        graph = graph.add_entity(entity)
    
    # Create chain
    for i in range(len(entities) - 1):
        relation = Relation(
            id=uuid4(),
            type="depends_on",
            from_entity=entities[i].id,
            to_entity=entities[i + 1].id,
        )
        graph = graph.add_relation(relation)
    
    return graph


def generate_star_topology(n: int) -> DependencyGraph:
    """Generate star topology: Hub with N dependents.
    
    Args:
        n: Number of dependents (total nodes = n + 1)
        
    Returns:
        Graph with hub and n dependents
    """
    hub = Entity(id=uuid4(), type="package", name="hub")
    dependents = [Entity(id=uuid4(), type="package", name=f"dep_{i}") for i in range(n)]
    
    graph = DependencyGraph()
    graph = graph.add_entity(hub)
    
    for dependent in dependents:
        graph = graph.add_entity(dependent)
        relation = Relation(
            id=uuid4(),
            type="depends_on",
            from_entity=dependent.id,
            to_entity=hub.id,
        )
        graph = graph.add_relation(relation)
    
    return graph


def generate_binary_tree(depth: int) -> DependencyGraph:
    """Generate binary tree dependency structure.
    
    Args:
        depth: Tree depth (nodes = 2^depth - 1)
        
    Returns:
        Graph structured as binary tree
    """
    entities = []
    total_nodes = 2 ** depth - 1
    
    for i in range(total_nodes):
        entities.append(Entity(id=uuid4(), type="package", name=f"node_{i}"))
    
    graph = DependencyGraph()
    for entity in entities:
        graph = graph.add_entity(entity)
    
    # Create binary tree edges (parent depends on children)
    for i in range(total_nodes):
        left_child = 2 * i + 1
        right_child = 2 * i + 2
        
        if left_child < total_nodes:
            graph = graph.add_relation(
                Relation(
                    id=uuid4(),
                    type="depends_on",
                    from_entity=entities[i].id,
                    to_entity=entities[left_child].id,
                )
            )
        
        if right_child < total_nodes:
            graph = graph.add_relation(
                Relation(
                    id=uuid4(),
                    type="depends_on",
                    from_entity=entities[i].id,
                    to_entity=entities[right_child].id,
                )
            )
    
    return graph


def generate_dense_dag(n: int, density: float = 0.3) -> DependencyGraph:
    """Generate dense DAG with controlled edge density.
    
    Args:
        n: Number of nodes
        density: Edge density (0.0 to 1.0)
        
    Returns:
        Dense DAG
    """
    entities = [Entity(id=uuid4(), type="package", name=f"pkg_{i}") for i in range(n)]
    
    graph = DependencyGraph()
    for entity in entities:
        graph = graph.add_entity(entity)
    
    # Add edges respecting topological order (i -> j where i < j)
    import random
    
    max_edges = (n * (n - 1)) // 2
    target_edges = int(max_edges * density)
    edges_added = 0
    
    for i in range(n):
        for j in range(i + 1, n):
            if edges_added >= target_edges:
                break
            
            if random.random() < density:
                graph = graph.add_relation(
                    Relation(
                        id=uuid4(),
                        type="depends_on",
                        from_entity=entities[i].id,
                        to_entity=entities[j].id,
                    )
                )
                edges_added += 1
    
    return graph


# ============================================================================
# BENCHMARK TESTS
# ============================================================================


class TestSCCPerformance:
    """Benchmark SCC detection at various scales."""

    @pytest.mark.parametrize("n", [10, 50, 100, 500, 1000])
    def test_scc_linear_chain(self, n: int, benchmark: pytest.fixture) -> None:  # type: ignore[valid-type]
        """Benchmark SCC on linear chain (no cycles)."""
        graph = generate_linear_chain(n)
        
        result = benchmark(find_strongly_connected_components, graph)
        
        # Sanity check: linear chain has n singleton SCCs
        assert len(result) == n

    @pytest.mark.parametrize("n", [10, 50, 100, 500])
    def test_scc_binary_tree(self, n: int, benchmark: pytest.fixture) -> None:  # type: ignore[valid-type]
        """Benchmark SCC on binary tree."""
        depth = n.bit_length()  # Approximate depth for ~n nodes
        graph = generate_binary_tree(depth)
        
        result = benchmark(find_strongly_connected_components, graph)
        assert len(result) > 0


class TestTopologicalSortPerformance:
    """Benchmark topological sort at various scales."""

    @pytest.mark.parametrize("n", [10, 50, 100, 500, 1000])
    def test_topo_sort_linear(self, n: int, benchmark: pytest.fixture) -> None:  # type: ignore[valid-type]
        """Benchmark topological sort on linear chain."""
        graph = generate_linear_chain(n)
        
        result = benchmark(topological_sort, graph)
        assert len(result) == n

    @pytest.mark.parametrize("n,density", [(50, 0.1), (50, 0.3), (50, 0.5)])
    def test_topo_sort_dense_dag(  # type: ignore[valid-type]
        self, n: int, density: float, benchmark: pytest.fixture
    ) -> None:
        """Benchmark topological sort on dense DAG."""
        graph = generate_dense_dag(n, density)
        
        result = benchmark(topological_sort, graph)
        assert len(result) == n


class TestReachabilityPerformance:
    """Benchmark reachability queries at various scales."""

    @pytest.mark.parametrize("n", [10, 50, 100, 500, 1000])
    def test_reachability_linear_worst_case(  # type: ignore[valid-type]
        self, n: int, benchmark: pytest.fixture
    ) -> None:
        """Benchmark reachability on linear chain (worst case: start to end)."""
        graph = generate_linear_chain(n)
        
        # Get first and last nodes
        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())
        source = nodes[0]
        target = nodes[-1]
        
        result = benchmark(is_reachable, graph, source, target)
        assert result is True  # Should be reachable

    @pytest.mark.parametrize("n", [10, 50, 100, 500])
    def test_reachability_star_topology(  # type: ignore[valid-type]
        self, n: int, benchmark: pytest.fixture
    ) -> None:
        """Benchmark reachability on star topology."""
        graph = generate_star_topology(n)
        
        # Get hub and a dependent
        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())
        
        # Find hub (node with most dependents)
        hub = max(nodes, key=lambda nid: len(graph.get_dependents(nid)))
        dependent = graph.get_dependents(hub)[0].id
        
        result = benchmark(is_reachable, graph, dependent, hub)
        assert result is True


class TestTransitiveDependenciesPerformance:
    """Benchmark transitive dependency queries."""

    @pytest.mark.parametrize("n", [10, 50, 100, 500, 1000])
    def test_transitive_deps_linear(  # type: ignore[valid-type]
        self, n: int, benchmark: pytest.fixture
    ) -> None:
        """Benchmark transitive dependencies on linear chain."""
        graph = generate_linear_chain(n)
        
        # Get first node (depends on all others)
        nx_graph = graph.to_networkx()
        first_node = list(nx_graph.nodes())[0]
        
        result = benchmark(get_transitive_dependencies, graph, first_node)
        
        # Should have n-1 transitive dependencies
        assert len(result) == n - 1

    @pytest.mark.parametrize("n", [10, 50, 100, 500])
    def test_transitive_dependents_star(  # type: ignore[valid-type]
        self, n: int, benchmark: pytest.fixture
    ) -> None:
        """Benchmark transitive dependents on star topology."""
        graph = generate_star_topology(n)
        
        # Get hub
        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())
        hub = max(nodes, key=lambda nid: len(graph.get_dependents(nid)))
        
        result = benchmark(get_transitive_dependents, graph, hub)
        
        # Should have n transitive dependents
        assert len(result) == n


class TestImpactAnalyzerPerformance:
    """Benchmark impact analyzer at various scales."""

    @pytest.mark.parametrize("n", [10, 50, 100, 500])
    def test_impact_metrics_star(self, n: int, benchmark: pytest.fixture) -> None:  # type: ignore[valid-type]
        """Benchmark impact metrics calculation on star topology."""
        graph = generate_star_topology(n)
        analyzer = DependencyImpactAnalyzer(graph)
        
        # Get hub
        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())
        hub = max(nodes, key=lambda nid: len(graph.get_dependents(nid)))
        
        result = benchmark(analyzer.calculate_impact_metrics, hub)
        assert result.blast_radius() == n

    @pytest.mark.parametrize("n", [10, 50, 100, 500])
    def test_change_impact_analysis(  # type: ignore[valid-type]
        self, n: int, benchmark: pytest.fixture
    ) -> None:
        """Benchmark full change impact analysis."""
        graph = generate_linear_chain(n)
        analyzer = DependencyImpactAnalyzer(graph)
        
        # Analyze impact on middle node
        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())
        middle_node = nodes[n // 2]
        
        result = benchmark(analyzer.analyze_change_impact, middle_node)
        assert result.risk_score >= 0.0

    @pytest.mark.parametrize("n", [10, 50, 100])
    def test_critical_path_analysis(  # type: ignore[valid-type]
        self, n: int, benchmark: pytest.fixture
    ) -> None:
        """Benchmark critical path analysis."""
        graph = generate_linear_chain(n)
        analyzer = DependencyImpactAnalyzer(graph)
        
        result = benchmark(analyzer.find_critical_path)
        assert result is not None
        assert result.length == n


# ============================================================================
# SCALABILITY TESTS (Longer running)
# ============================================================================


@pytest.mark.slow
class TestScalability:
    """Scalability tests for large graphs (marked as slow)."""

    def test_scc_5k_nodes(self) -> None:
        """Test SCC detection on 5,000 node graph."""
        graph = generate_linear_chain(5000)
        
        start = time.time()
        sccs = find_strongly_connected_components(graph)
        elapsed = time.time() - start
        
        assert len(sccs) == 5000
        assert elapsed < 5.0, f"SCC on 5K nodes took {elapsed:.2f}s (should be < 5s)"

    def test_topological_sort_5k_nodes(self) -> None:
        """Test topological sort on 5,000 node DAG."""
        graph = generate_dense_dag(1000, density=0.05)  # ~25K edges
        
        start = time.time()
        order = topological_sort(graph)
        elapsed = time.time() - start
        
        assert len(order) == 1000
        assert elapsed < 5.0, f"Topo sort on 1K nodes took {elapsed:.2f}s (should be < 5s)"

    def test_transitive_deps_large_fan_out(self) -> None:
        """Test transitive dependencies with large fan-out."""
        graph = generate_star_topology(1000)
        
        # Get hub
        nx_graph = graph.to_networkx()
        nodes = list(nx_graph.nodes())
        hub = max(nodes, key=lambda nid: len(graph.get_dependents(nid)))
        
        start = time.time()
        dependents = get_transitive_dependents(graph, hub)
        elapsed = time.time() - start
        
        assert len(dependents) == 1000
        assert elapsed < 1.0, f"Transitive dependents took {elapsed:.2f}s (should be < 1s)"


# ============================================================================
# MEMORY PROFILING HELPERS
# ============================================================================


@pytest.mark.slow
class TestMemoryUsage:
    """Memory usage tests (requires memory_profiler)."""

    def test_graph_memory_footprint(self) -> None:
        """Measure memory footprint of large graph."""
        try:
            from memory_profiler import memory_usage
        except ImportError:
            pytest.skip("memory_profiler not installed")
        
        def create_large_graph() -> None:
            graph = generate_dense_dag(1000, density=0.1)
            # Force evaluation
            _ = graph.node_count()
            _ = graph.edge_count()
        
        mem_usage = memory_usage(create_large_graph, interval=0.1)
        peak_memory = max(mem_usage)
        
        # Should use < 100 MB for 1K node graph
        assert peak_memory < 100, f"Peak memory: {peak_memory:.1f} MB (should be < 100 MB)"


# ============================================================================
# COMPLEXITY VERIFICATION
# ============================================================================


class TestComplexityVerification:
    """Verify O(V+E) complexity empirically."""

    def test_scc_scales_linearly_with_edges(self) -> None:
        """Verify SCC time scales linearly with edges (O(V+E))."""
        timings = []
        
        # Test at different scales
        for n in [50, 100, 200]:
            graph = generate_dense_dag(n, density=0.3)
            
            start = time.time()
            find_strongly_connected_components(graph)
            elapsed = time.time() - start
            
            edge_count = graph.edge_count()
            timings.append((edge_count, elapsed))
        
        # Check that doubling edges roughly doubles time
        # (allowing for overhead and variance)
        ratio_1 = timings[1][1] / timings[0][1]  # time ratio
        edge_ratio_1 = timings[1][0] / timings[0][0]  # edge ratio
        
        # Time ratio should be proportional to edge ratio (within 2x tolerance)
        assert ratio_1 < edge_ratio_1 * 2, "SCC does not scale linearly"

    def test_transitive_deps_scales_linearly(self) -> None:
        """Verify transitive dependencies scale linearly."""
        timings = []
        
        for n in [100, 200, 400]:
            graph = generate_linear_chain(n)
            nx_graph = graph.to_networkx()
            first_node = list(nx_graph.nodes())[0]
            
            start = time.time()
            get_transitive_dependencies(graph, first_node)
            elapsed = time.time() - start
            
            timings.append((n, elapsed))
        
        # Check linear scaling
        ratio = timings[1][1] / timings[0][1]
        n_ratio = timings[1][0] / timings[0][0]
        
        assert ratio < n_ratio * 2, "Transitive deps do not scale linearly"
