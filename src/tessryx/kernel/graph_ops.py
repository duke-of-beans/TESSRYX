"""Graph Operations - Core graph algorithms for dependency analysis.

This module implements fundamental graph algorithms that power TESSRYX's
dependency intelligence:

- **Strongly Connected Components (SCC):** Tarjan's algorithm for cycle detection
- **Topological Sort:** DAG ordering for build/deployment sequences
- **Reachability:** Fast path existence queries
- **Dependency Impact (S02 from EOS):** Blast radius, critical path analysis

All algorithms operate on the TessIR graph structure (Entity + Relation primitives).

Design Principles:
- Efficient O(V+E) algorithms where possible
- Immutable results (return new data, don't modify graph)
- Comprehensive error handling
- NetworkX integration for complex queries
- Property-based testing for correctness
"""

from collections import defaultdict, deque
from typing import Any
from uuid import UUID

import networkx as nx

from tessryx.core.entity import Entity
from tessryx.core.relation import Relation
from tessryx.core.types import EntityID


# ============================================================================
# GRAPH REPRESENTATION
# ============================================================================


class DependencyGraph:
    """In-memory representation of the dependency graph.
    
    Wraps NetworkX DiGraph with TessIR-specific operations and guarantees.
    
    The graph stores:
    - Nodes: Entity objects (keyed by EntityID)
    - Edges: Relation objects (with metadata)
    
    Thread-safe for read operations. Mutations return new graphs.
    
    Examples:
        >>> graph = DependencyGraph()
        >>> 
        >>> # Add entities
        >>> entity1 = Entity(id=uuid4(), type="package", name="react")
        >>> entity2 = Entity(id=uuid4(), type="package", name="react-dom")
        >>> graph = graph.add_entity(entity1).add_entity(entity2)
        >>> 
        >>> # Add relation
        >>> relation = Relation(
        ...     id=uuid4(),
        ...     type="depends_on",
        ...     from_entity_id=entity2.id,
        ...     to_entity_id=entity1.id,
        ... )
        >>> graph = graph.add_relation(relation)
        >>> 
        >>> # Query
        >>> deps = graph.get_dependencies(entity2.id)
        >>> len(deps)
        1
    """

    def __init__(self, graph: nx.DiGraph | None = None) -> None:
        """Initialize dependency graph.
        
        Args:
            graph: Optional NetworkX DiGraph to wrap (for internal use)
        """
        self._graph = graph if graph is not None else nx.DiGraph()

    def add_entity(self, entity: Entity) -> "DependencyGraph":
        """Add an entity to the graph (immutable operation).
        
        Args:
            entity: Entity to add
            
        Returns:
            New DependencyGraph with entity added
            
        Raises:
            ValueError: If entity with same ID already exists
        """
        if entity.id in self._graph:
            raise ValueError(f"Entity {entity.id} already exists in graph")
        
        # Create new graph with entity
        new_graph = self._graph.copy()
        new_graph.add_node(entity.id, entity=entity)
        
        return DependencyGraph(new_graph)

    def add_relation(self, relation: Relation) -> "DependencyGraph":
        """Add a relation (edge) to the graph (immutable operation).
        
        Args:
            relation: Relation to add
            
        Returns:
            New DependencyGraph with relation added
            
        Raises:
            ValueError: If source or target entity doesn't exist
            ValueError: If relation already exists
        """
        if relation.from_entity not in self._graph:
            raise ValueError(f"Source entity {relation.from_entity} not in graph")
        if relation.to_entity not in self._graph:
            raise ValueError(f"Target entity {relation.to_entity} not in graph")
        
        # Check if edge already exists
        if self._graph.has_edge(relation.from_entity, relation.to_entity):
            raise ValueError(
                f"Relation from {relation.from_entity} to {relation.to_entity} "
                "already exists"
            )
        
        # Create new graph with relation
        new_graph = self._graph.copy()
        new_graph.add_edge(
            relation.from_entity,
            relation.to_entity,
            relation=relation,
        )
        
        return DependencyGraph(new_graph)

    def get_entity(self, entity_id: EntityID) -> Entity | None:
        """Get entity by ID.
        
        Args:
            entity_id: Entity ID to retrieve
            
        Returns:
            Entity if found, None otherwise
        """
        if entity_id not in self._graph:
            return None
        return self._graph.nodes[entity_id]["entity"]

    def get_relation(
        self,
        from_entity_id: EntityID,
        to_entity_id: EntityID,
    ) -> Relation | None:
        """Get relation between two entities.
        
        Args:
            from_entity_id: Source entity ID
            to_entity_id: Target entity ID
            
        Returns:
            Relation if edge exists, None otherwise
        """
        if not self._graph.has_edge(from_entity_id, to_entity_id):
            return None
        return self._graph.edges[from_entity_id, to_entity_id]["relation"]

    def get_dependencies(self, entity_id: EntityID) -> list[Entity]:
        """Get all direct dependencies of an entity (outgoing edges).
        
        Args:
            entity_id: Entity to get dependencies for
            
        Returns:
            List of entities that this entity depends on
        """
        if entity_id not in self._graph:
            return []
        
        # Successors = nodes this entity points to (dependencies)
        dep_ids = list(self._graph.successors(entity_id))
        return [self.get_entity(dep_id) for dep_id in dep_ids if self.get_entity(dep_id)]

    def get_dependents(self, entity_id: EntityID) -> list[Entity]:
        """Get all direct dependents of an entity (incoming edges).
        
        Args:
            entity_id: Entity to get dependents for
            
        Returns:
            List of entities that depend on this entity
        """
        if entity_id not in self._graph:
            return []
        
        # Predecessors = nodes pointing to this entity (dependents)
        dependent_ids = list(self._graph.predecessors(entity_id))
        return [self.get_entity(dep_id) for dep_id in dependent_ids if self.get_entity(dep_id)]

    def node_count(self) -> int:
        """Get number of entities in graph."""
        return self._graph.number_of_nodes()

    def edge_count(self) -> int:
        """Get number of relations in graph."""
        return self._graph.number_of_edges()

    def to_networkx(self) -> nx.DiGraph:
        """Get underlying NetworkX graph (for advanced queries).
        
        Returns:
            NetworkX DiGraph (read-only copy)
        """
        return self._graph.copy()


# ============================================================================
# STRONGLY CONNECTED COMPONENTS (Tarjan's Algorithm)
# ============================================================================


def find_strongly_connected_components(graph: DependencyGraph) -> list[list[EntityID]]:
    """Find all strongly connected components using Tarjan's algorithm.
    
    A strongly connected component (SCC) is a maximal set of nodes where
    every node is reachable from every other node. In dependency graphs,
    SCCs represent circular dependencies.
    
    Complexity: O(V + E) where V = nodes, E = edges
    
    Args:
        graph: Dependency graph to analyze
        
    Returns:
        List of SCCs, each SCC is a list of entity IDs
        Sorted by size (largest SCCs first)
        
    Examples:
        >>> # Graph with circular dependency: A -> B -> C -> A
        >>> sccs = find_strongly_connected_components(graph)
        >>> len(sccs)
        1
        >>> len(sccs[0])  # All three nodes in one SCC
        3
    """
    nx_graph = graph.to_networkx()
    
    # Use NetworkX's optimized Tarjan implementation
    sccs = list(nx.strongly_connected_components(nx_graph))
    
    # Convert sets to lists and sort by size (largest first)
    result = [list(scc) for scc in sccs]
    result.sort(key=len, reverse=True)
    
    return result


def find_circular_dependencies(graph: DependencyGraph) -> list[list[EntityID]]:
    """Find all circular dependency chains in the graph.
    
    Returns only SCCs with size > 1 (actual cycles).
    Single-node SCCs are filtered out.
    
    Args:
        graph: Dependency graph to analyze
        
    Returns:
        List of circular dependency chains
        Each chain is a list of entity IDs forming a cycle
        
    Examples:
        >>> cycles = find_circular_dependencies(graph)
        >>> for cycle in cycles:
        ...     print(f"Circular dependency: {' -> '.join(str(id) for id in cycle)}")
    """
    sccs = find_strongly_connected_components(graph)
    
    # Filter to only SCCs with > 1 node (actual cycles)
    cycles = [scc for scc in sccs if len(scc) > 1]
    
    return cycles


# ============================================================================
# TOPOLOGICAL SORT
# ============================================================================


class CycleDetectedError(Exception):
    """Raised when topological sort is attempted on a graph with cycles."""
    
    def __init__(self, cycle: list[EntityID]) -> None:
        """Initialize with the detected cycle.
        
        Args:
            cycle: List of entity IDs forming the cycle
        """
        self.cycle = cycle
        super().__init__(f"Cycle detected: {' -> '.join(str(id) for id in cycle)}")


def topological_sort(graph: DependencyGraph) -> list[EntityID]:
    """Perform topological sort on the dependency graph.
    
    Returns a linear ordering where dependencies come before dependents.
    Useful for:
    - Build order determination
    - Deployment sequencing
    - Install order calculation
    
    Complexity: O(V + E)
    
    Args:
        graph: Dependency graph to sort (must be a DAG)
        
    Returns:
        List of entity IDs in topological order
        
    Raises:
        CycleDetectedError: If graph contains cycles (use find_circular_dependencies first)
        
    Examples:
        >>> # A depends on B, B depends on C
        >>> # Topological order: [C, B, A]
        >>> order = topological_sort(graph)
        >>> # C must be built before B, B before A
    """
    nx_graph = graph.to_networkx()
    
    try:
        # Use NetworkX's optimized topological sort
        # NetworkX returns dependents-first order, but we want dependencies-first (build order)
        # So we reverse the result
        order = list(reversed(list(nx.topological_sort(nx_graph))))
        return order
    except nx.NetworkXError:
        # Cycle detected - find it and report
        cycles = find_circular_dependencies(graph)
        if cycles:
            raise CycleDetectedError(cycles[0])
        else:
            # Shouldn't happen, but handle gracefully
            raise CycleDetectedError([])


# ============================================================================
# REACHABILITY QUERIES
# ============================================================================


def is_reachable(
    graph: DependencyGraph,
    source_id: EntityID,
    target_id: EntityID,
) -> bool:
    """Check if target is reachable from source (path exists).
    
    Uses BFS for efficiency.
    Complexity: O(V + E) worst case, but often much faster
    
    Args:
        graph: Dependency graph
        source_id: Starting entity
        target_id: Target entity
        
    Returns:
        True if path exists from source to target
        
    Examples:
        >>> # Check if upgrading A will affect B
        >>> if is_reachable(graph, a_id, b_id):
        ...     print("Upgrading A may impact B")
    """
    if source_id == target_id:
        return True
    
    if source_id not in graph._graph or target_id not in graph._graph:
        return False
    
    nx_graph = graph.to_networkx()
    return nx.has_path(nx_graph, source_id, target_id)


def find_path(
    graph: DependencyGraph,
    source_id: EntityID,
    target_id: EntityID,
) -> list[EntityID] | None:
    """Find shortest path from source to target.
    
    Uses BFS to find shortest path.
    Complexity: O(V + E)
    
    Args:
        graph: Dependency graph
        source_id: Starting entity
        target_id: Target entity
        
    Returns:
        List of entity IDs forming shortest path, or None if no path exists
        Path includes both source and target
        
    Examples:
        >>> path = find_path(graph, a_id, d_id)
        >>> if path:
        ...     print(f"Dependency chain: {' -> '.join(str(id) for id in path)}")
    """
    if source_id == target_id:
        return [source_id]
    
    if source_id not in graph._graph or target_id not in graph._graph:
        return None
    
    nx_graph = graph.to_networkx()
    
    try:
        path = nx.shortest_path(nx_graph, source_id, target_id)
        return path
    except nx.NetworkXNoPath:
        return None


def find_all_paths(
    graph: DependencyGraph,
    source_id: EntityID,
    target_id: EntityID,
    max_paths: int = 10,
) -> list[list[EntityID]]:
    """Find all simple paths from source to target.
    
    A simple path has no repeated nodes.
    Limited to max_paths to prevent combinatorial explosion.
    
    Args:
        graph: Dependency graph
        source_id: Starting entity
        target_id: Target entity
        max_paths: Maximum number of paths to return
        
    Returns:
        List of paths, each path is a list of entity IDs
        Sorted by length (shortest first)
        
    Examples:
        >>> paths = find_all_paths(graph, a_id, z_id, max_paths=5)
        >>> for i, path in enumerate(paths, 1):
        ...     print(f"Path {i}: {len(path)} hops")
    """
    if source_id == target_id:
        return [[source_id]]
    
    if source_id not in graph._graph or target_id not in graph._graph:
        return []
    
    nx_graph = graph.to_networkx()
    
    try:
        # Get all simple paths (no repeated nodes)
        all_paths = nx.all_simple_paths(nx_graph, source_id, target_id)
        
        # Limit to max_paths and convert to list
        paths = []
        for path in all_paths:
            paths.append(path)
            if len(paths) >= max_paths:
                break
        
        # Sort by length (shortest first)
        paths.sort(key=len)
        
        return paths
    except nx.NetworkXNoPath:
        return []


# ============================================================================
# TRANSITIVE DEPENDENCIES
# ============================================================================


def get_transitive_dependencies(
    graph: DependencyGraph,
    entity_id: EntityID,
    max_depth: int | None = None,
) -> set[EntityID]:
    """Get all transitive dependencies (recursive).
    
    Returns all entities reachable from the given entity.
    
    Args:
        graph: Dependency graph
        entity_id: Entity to get dependencies for
        max_depth: Maximum depth to traverse (None = unlimited)
        
    Returns:
        Set of entity IDs that are transitive dependencies
        Does NOT include the entity itself
        
    Examples:
        >>> # Get everything A depends on (directly or indirectly)
        >>> all_deps = get_transitive_dependencies(graph, a_id)
        >>> print(f"A has {len(all_deps)} total dependencies")
    """
    if entity_id not in graph._graph:
        return set()
    
    visited: set[EntityID] = set()
    queue: deque[tuple[EntityID, int]] = deque([(entity_id, 0)])
    
    while queue:
        current_id, depth = queue.popleft()
        
        # Skip if already visited
        if current_id in visited:
            continue
        
        visited.add(current_id)
        
        # Skip adding children if max depth would be exceeded
        if max_depth is not None and depth >= max_depth:
            continue
        
        # Add dependencies to queue
        for dep in graph.get_dependencies(current_id):
            if dep.id not in visited:
                queue.append((dep.id, depth + 1))
    
    # Remove the starting entity
    visited.discard(entity_id)
    
    return visited


def get_transitive_dependents(
    graph: DependencyGraph,
    entity_id: EntityID,
    max_depth: int | None = None,
) -> set[EntityID]:
    """Get all transitive dependents (reverse recursive).
    
    Returns all entities that depend on the given entity (directly or indirectly).
    
    Args:
        graph: Dependency graph
        entity_id: Entity to get dependents for
        max_depth: Maximum depth to traverse (None = unlimited)
        
    Returns:
        Set of entity IDs that are transitive dependents
        Does NOT include the entity itself
        
    Examples:
        >>> # Get everything that depends on A (directly or indirectly)
        >>> all_dependents = get_transitive_dependents(graph, a_id)
        >>> print(f"{len(all_dependents)} packages would be affected by changes to A")
    """
    if entity_id not in graph._graph:
        return set()
    
    visited: set[EntityID] = set()
    queue: deque[tuple[EntityID, int]] = deque([(entity_id, 0)])
    
    while queue:
        current_id, depth = queue.popleft()
        
        # Skip if already visited
        if current_id in visited:
            continue
        
        visited.add(current_id)
        
        # Skip adding children if max depth would be exceeded
        if max_depth is not None and depth >= max_depth:
            continue
        
        # Add dependents to queue
        for dependent in graph.get_dependents(current_id):
            if dependent.id not in visited:
                queue.append((dependent.id, depth + 1))
    
    # Remove the starting entity
    visited.discard(entity_id)
    
    return visited
