"""Graph operations for TessIR dependency analysis.

Provides algorithms for analyzing dependency graphs including:
- Strongly Connected Component (SCC) detection via Tarjan's algorithm
- Topological sorting via Kahn's algorithm
- Blast radius calculation
- Cycle detection
"""

from collections import defaultdict, deque
from typing import TypeAlias

from ..core.relation import Relation
from ..core.types import EntityID

# Type aliases for clarity
GraphDict: TypeAlias = dict[EntityID, list[EntityID]]
SCCList: TypeAlias = list[list[EntityID]]


class GraphOps:
    """Graph analysis operations for dependency management.
    
    All algorithms are deterministic and produce consistent results for
    the same input graph structure.
    """

    @staticmethod
    def build_graph(relations: list[Relation]) -> GraphDict:
        """Build adjacency list from relations.
        
        Args:
            relations: List of Relation objects
            
        Returns:
            Dictionary mapping entity IDs to lists of dependent entity IDs
        """
        graph: GraphDict = defaultdict(list)
        for rel in relations:
            graph[rel.from_entity].append(rel.to_entity)
        return dict(graph)

    @staticmethod
    def tarjan_scc(graph: GraphDict) -> SCCList:
        """Find strongly connected components using Tarjan's algorithm.
        
        Time complexity: O(V + E) where V is vertices and E is edges
        Space complexity: O(V) for the recursion stack and tracking data
        
        A strongly connected component is a maximal set of vertices where
        every vertex is reachable from every other vertex in the set.
        
        Args:
            graph: Adjacency list representation of the graph
            
        Returns:
            List of SCCs, where each SCC is a list of entity IDs.
            SCCs are returned in reverse topological order.
        """
        index_counter = [0]
        stack: list[EntityID] = []
        lowlinks: dict[EntityID, int] = {}
        index: dict[EntityID, int] = {}
        on_stack: dict[EntityID, bool] = defaultdict(bool)
        sccs: SCCList = []

        def strongconnect(node: EntityID) -> None:
            # Set the depth index for this node to the smallest unused index
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True

            # Consider successors of node
            for successor in graph.get(node, []):
                if successor not in index:
                    # Successor has not yet been visited; recurse on it
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[successor])
                elif on_stack[successor]:
                    # Successor is in stack and hence in the current SCC
                    lowlinks[node] = min(lowlinks[node], index[successor])

            # If node is a root node, pop the stack and generate an SCC
            if lowlinks[node] == index[node]:
                component: list[EntityID] = []
                while True:
                    successor = stack.pop()
                    on_stack[successor] = False
                    component.append(successor)
                    if successor == node:
                        break
                sccs.append(component)

        # Find all nodes (including isolated ones)
        all_nodes = set(graph.keys())
        for successors in graph.values():
            all_nodes.update(successors)

        # Process all nodes
        for node in all_nodes:
            if node not in index:
                strongconnect(node)

        return sccs

    @staticmethod
    def detect_cycles(graph: GraphDict) -> list[list[EntityID]]:
        """Detect all cycles in the graph.
        
        A cycle is a strongly connected component with more than one node,
        or a single node with a self-loop.
        
        Args:
            graph: Adjacency list representation of the graph
            
        Returns:
            List of cycles, where each cycle is a list of entity IDs
        """
        sccs = GraphOps.tarjan_scc(graph)
        cycles = []
        
        for scc in sccs:
            # Multi-node SCC is always a cycle
            if len(scc) > 1:
                cycles.append(scc)
            # Single-node SCC with self-loop is a cycle
            elif len(scc) == 1 and scc[0] in graph.get(scc[0], []):
                cycles.append(scc)
        
        return cycles

    @staticmethod
    def topological_sort(graph: GraphDict) -> list[EntityID] | None:
        """Perform topological sort using Kahn's algorithm.
        
        Time complexity: O(V + E)
        Space complexity: O(V)
        
        Args:
            graph: Adjacency list representation of the graph
            
        Returns:
            List of entity IDs in topological order, or None if graph has cycles
        """
        # Calculate in-degrees
        in_degree: dict[EntityID, int] = defaultdict(int)
        all_nodes = set(graph.keys())
        for successors in graph.values():
            all_nodes.update(successors)
        
        for node in all_nodes:
            if node not in in_degree:
                in_degree[node] = 0
        
        for successors in graph.values():
            for successor in successors:
                in_degree[successor] += 1

        # Queue all nodes with in-degree 0
        queue: deque[EntityID] = deque([node for node in all_nodes if in_degree[node] == 0])
        result: list[EntityID] = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # Reduce in-degree for all successors
            for successor in graph.get(node, []):
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        # If we processed all nodes, no cycle exists
        if len(result) == len(all_nodes):
            return result
        else:
            return None  # Cycle detected

    @staticmethod
    def blast_radius(
        graph: GraphDict,
        entity_id: EntityID,
        max_depth: int | None = None
    ) -> set[EntityID]:
        """Calculate blast radius: all entities affected by changes to entity_id.
        
        Performs breadth-first search to find all downstream dependencies.
        
        Args:
            graph: Adjacency list representation of the graph
            entity_id: ID of the entity to analyze
            max_depth: Optional maximum depth to traverse (None for unlimited)
            
        Returns:
            Set of entity IDs that depend (directly or indirectly) on entity_id
        """
        if entity_id not in graph and entity_id not in set().union(*graph.values()):
            # Entity doesn't exist in graph
            return set()

        visited: set[EntityID] = set()
        queue: deque[tuple[EntityID, int]] = deque([(entity_id, 0)])
        
        while queue:
            current, depth = queue.popleft()
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # Stop if we've reached max depth
            if max_depth is not None and depth >= max_depth:
                continue
            
            # Add all successors to queue
            for successor in graph.get(current, []):
                if successor not in visited:
                    queue.append((successor, depth + 1))
        
        # Remove the original entity from the result
        visited.discard(entity_id)
        return visited

    @staticmethod
    def reverse_graph(graph: GraphDict) -> GraphDict:
        """Create reversed graph (transpose).
        
        Args:
            graph: Adjacency list representation of the graph
            
        Returns:
            Reversed graph where all edges are flipped
        """
        reversed_graph: GraphDict = defaultdict(list)
        
        # Get all nodes
        all_nodes = set(graph.keys())
        for successors in graph.values():
            all_nodes.update(successors)
        
        # Initialize all nodes in reversed graph
        for node in all_nodes:
            if node not in reversed_graph:
                reversed_graph[node] = []
        
        # Reverse all edges
        for node, successors in graph.items():
            for successor in successors:
                reversed_graph[successor].append(node)
        
        return dict(reversed_graph)

    @staticmethod
    def upstream_dependencies(
        graph: GraphDict,
        entity_id: EntityID,
        max_depth: int | None = None
    ) -> set[EntityID]:
        """Calculate all entities that entity_id depends on.
        
        This is the reverse of blast_radius - finds all upstream dependencies.
        
        Args:
            graph: Adjacency list representation of the graph
            entity_id: ID of the entity to analyze
            max_depth: Optional maximum depth to traverse (None for unlimited)
            
        Returns:
            Set of entity IDs that entity_id depends on (directly or indirectly)
        """
        reversed_graph = GraphOps.reverse_graph(graph)
        return GraphOps.blast_radius(reversed_graph, entity_id, max_depth)
