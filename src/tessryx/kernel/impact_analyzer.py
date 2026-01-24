"""Dependency Impact Analyzer - Blast radius and critical path analysis.

This module implements the S02 steal from Eye-of-Sauron: sophisticated dependency
impact analysis for answering "what breaks if X changes?"

Key capabilities:
- **Blast Radius:** How many entities affected by a change
- **Critical Path:** Longest dependency chain (deployment bottleneck)
- **Impact Metrics:** Quantify change risk and scope
- **Change Propagation:** Track how changes flow through the graph

Used for:
- Risk assessment before upgrades
- Change impact analysis
- Deployment planning
- Breaking change detection
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID

from tessryx.core.entity import Entity
from tessryx.core.types import EntityID
from tessryx.kernel.graph_ops import (
    DependencyGraph,
    find_circular_dependencies,
    get_transitive_dependencies,
    get_transitive_dependents,
    topological_sort,
)


# ============================================================================
# IMPACT SEVERITY
# ============================================================================


class ImpactSeverity(str, Enum):
    """Severity classification for dependency impact."""

    MINIMAL = "minimal"  # <5 entities affected
    LOW = "low"  # 5-20 entities affected
    MEDIUM = "medium"  # 21-100 entities affected
    HIGH = "high"  # 101-500 entities affected
    CRITICAL = "critical"  # >500 entities affected


# ============================================================================
# IMPACT ANALYSIS RESULTS
# ============================================================================


@dataclass(frozen=True)
class ImpactMetrics:
    """Quantified impact of a change to an entity.
    
    Attributes:
        entity_id: Entity being analyzed
        direct_dependents: Count of direct dependents
        total_dependents: Count of all transitive dependents (blast radius)
        direct_dependencies: Count of direct dependencies
        total_dependencies: Count of all transitive dependencies
        severity: Impact severity classification
        is_critical_path: Whether entity is on critical path
        circular_dependencies: Number of circular dependencies involving this entity
        max_depth_to_dependents: Longest path to a dependent (deployment depth)
        max_depth_from_dependencies: Longest path from a dependency
    """

    entity_id: EntityID
    direct_dependents: int
    total_dependents: int
    direct_dependencies: int
    total_dependencies: int
    severity: ImpactSeverity
    is_critical_path: bool
    circular_dependencies: int
    max_depth_to_dependents: int
    max_depth_from_dependencies: int

    def blast_radius(self) -> int:
        """Get blast radius (total entities affected by change).
        
        Returns:
            Number of entities that could be impacted
        """
        return self.total_dependents

    def is_high_risk(self) -> bool:
        """Check if changes to this entity are high risk.
        
        Returns:
            True if severity is HIGH or CRITICAL
        """
        return self.severity in (ImpactSeverity.HIGH, ImpactSeverity.CRITICAL)

    def is_hub(self) -> bool:
        """Check if entity is a hub (many dependents).
        
        Returns:
            True if has > 10 direct dependents
        """
        return self.direct_dependents > 10

    def is_leaf(self) -> bool:
        """Check if entity is a leaf (no dependents).
        
        Returns:
            True if has no dependents
        """
        return self.direct_dependents == 0

    def deployment_depth(self) -> int:
        """Get deployment depth (how deep in deployment sequence).
        
        Returns:
            Maximum depth to any dependent
        """
        return self.max_depth_to_dependents


@dataclass(frozen=True)
class CriticalPath:
    """Longest dependency path in the graph.
    
    The critical path represents the deployment bottleneck - the longest
    sequence of dependencies that must be satisfied in order.
    
    Attributes:
        path: List of entity IDs forming the critical path
        length: Number of entities in the path
        total_weight: Sum of weights along path (if weighted)
    """

    path: tuple[EntityID, ...]
    length: int
    total_weight: float = 0.0

    def get_bottleneck(self) -> EntityID:
        """Get the bottleneck entity (start of critical path).
        
        Returns:
            Entity ID at the start of the critical path
        """
        return self.path[0] if self.path else None  # type: ignore[return-value]

    def entities_on_path(self) -> list[EntityID]:
        """Get all entities on the critical path.
        
        Returns:
            List of entity IDs in path order
        """
        return list(self.path)


@dataclass(frozen=True)
class ChangeImpactAnalysis:
    """Complete impact analysis for a proposed change.
    
    Attributes:
        entity_id: Entity being changed
        metrics: Impact metrics for the entity
        affected_entities: Set of all entities affected by the change
        critical_paths: Critical paths involving this entity
        circular_dependency_chains: Circular dependencies involving this entity
        recommendations: Human-readable recommendations
        risk_score: Overall risk score (0.0-1.0)
    """

    entity_id: EntityID
    metrics: ImpactMetrics
    affected_entities: frozenset[EntityID]
    critical_paths: tuple[CriticalPath, ...]
    circular_dependency_chains: tuple[tuple[EntityID, ...], ...]
    recommendations: tuple[str, ...]
    risk_score: float

    def is_safe_to_change(self) -> bool:
        """Check if change is relatively safe.
        
        Returns:
            True if risk_score < 0.3 and no critical violations
        """
        return (
            self.risk_score < 0.3
            and not self.metrics.is_high_risk()
            and len(self.circular_dependency_chains) == 0
        )

    def requires_coordination(self) -> bool:
        """Check if change requires coordination across teams.
        
        Returns:
            True if affects > 20 entities
        """
        return len(self.affected_entities) > 20


# ============================================================================
# IMPACT ANALYZER
# ============================================================================


class DependencyImpactAnalyzer:
    """Analyzes dependency impact for changes and upgrades.
    
    Implements the S02 steal from Eye-of-Sauron: blast radius calculation,
    critical path identification, and comprehensive impact metrics.
    
    Examples:
        >>> analyzer = DependencyImpactAnalyzer(graph)
        >>> 
        >>> # Analyze impact of changing an entity
        >>> impact = analyzer.analyze_change_impact(entity_id)
        >>> print(f"Blast radius: {impact.metrics.blast_radius()} entities")
        >>> print(f"Risk score: {impact.risk_score:.2f}")
        >>> 
        >>> # Check if safe to upgrade
        >>> if impact.is_safe_to_change():
        ...     print("Safe to upgrade")
        >>> else:
        ...     print("High risk - requires careful planning")
        ...     for rec in impact.recommendations:
        ...         print(f"  - {rec}")
    """

    def __init__(self, graph: DependencyGraph) -> None:
        """Initialize analyzer with dependency graph.
        
        Args:
            graph: Dependency graph to analyze
        """
        self.graph = graph

    def calculate_impact_metrics(self, entity_id: EntityID) -> ImpactMetrics:
        """Calculate comprehensive impact metrics for an entity.
        
        Args:
            entity_id: Entity to analyze
            
        Returns:
            Impact metrics including blast radius, severity, critical path status
            
        Raises:
            ValueError: If entity not in graph
        """
        if self.graph.get_entity(entity_id) is None:
            raise ValueError(f"Entity {entity_id} not found in graph")

        # Direct counts
        direct_deps = self.graph.get_dependencies(entity_id)
        direct_dependents = self.graph.get_dependents(entity_id)

        # Transitive counts (blast radius)
        transitive_deps = get_transitive_dependencies(self.graph, entity_id)
        transitive_dependents = get_transitive_dependents(self.graph, entity_id)

        # Circular dependencies
        cycles = find_circular_dependencies(self.graph)
        circular_count = sum(1 for cycle in cycles if entity_id in cycle)

        # Calculate severity based on blast radius
        blast_radius = len(transitive_dependents)
        if blast_radius < 5:
            severity = ImpactSeverity.MINIMAL
        elif blast_radius < 21:
            severity = ImpactSeverity.LOW
        elif blast_radius < 101:
            severity = ImpactSeverity.MEDIUM
        elif blast_radius < 501:
            severity = ImpactSeverity.HIGH
        else:
            severity = ImpactSeverity.CRITICAL

        # Check if on critical path
        critical_path = self.find_critical_path()
        is_on_critical = entity_id in critical_path.path if critical_path else False

        # Calculate depths (for deployment planning)
        max_depth_to_dependents = self._calculate_max_depth(
            entity_id, direction="dependents"
        )
        max_depth_from_deps = self._calculate_max_depth(entity_id, direction="dependencies")

        return ImpactMetrics(
            entity_id=entity_id,
            direct_dependents=len(direct_dependents),
            total_dependents=len(transitive_dependents),
            direct_dependencies=len(direct_deps),
            total_dependencies=len(transitive_deps),
            severity=severity,
            is_critical_path=is_on_critical,
            circular_dependencies=circular_count,
            max_depth_to_dependents=max_depth_to_dependents,
            max_depth_from_dependencies=max_depth_from_deps,
        )

    def analyze_change_impact(self, entity_id: EntityID) -> ChangeImpactAnalysis:
        """Perform complete impact analysis for a proposed change.
        
        Args:
            entity_id: Entity being changed
            
        Returns:
            Complete change impact analysis with recommendations
            
        Examples:
            >>> impact = analyzer.analyze_change_impact(package_id)
            >>> if impact.is_safe_to_change():
            ...     deploy(package_id)
            >>> else:
            ...     print(f"Risk score: {impact.risk_score}")
            ...     print("Recommendations:")
            ...     for rec in impact.recommendations:
            ...         print(f"  - {rec}")
        """
        # Calculate basic metrics
        metrics = self.calculate_impact_metrics(entity_id)

        # Get affected entities (all transitive dependents)
        affected = get_transitive_dependents(self.graph, entity_id)
        affected_set = frozenset(affected)

        # Find critical paths involving this entity
        critical_paths = self._find_critical_paths_involving(entity_id)

        # Find circular dependencies involving this entity
        cycles = find_circular_dependencies(self.graph)
        circular_chains = tuple(
            tuple(cycle) for cycle in cycles if entity_id in cycle
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, circular_chains)

        # Calculate risk score (0.0-1.0)
        risk_score = self._calculate_risk_score(metrics, circular_chains)

        return ChangeImpactAnalysis(
            entity_id=entity_id,
            metrics=metrics,
            affected_entities=affected_set,
            critical_paths=critical_paths,
            circular_dependency_chains=circular_chains,
            recommendations=recommendations,
            risk_score=risk_score,
        )

    def find_critical_path(self) -> CriticalPath | None:
        """Find the critical path (longest dependency chain) in the graph.
        
        The critical path represents the deployment bottleneck - the longest
        sequence of dependencies that must be built/deployed in order.
        
        Returns:
            Critical path, or None if graph is empty or has cycles
            
        Examples:
            >>> path = analyzer.find_critical_path()
            >>> if path:
            ...     print(f"Critical path length: {path.length}")
            ...     print(f"Bottleneck: {path.get_bottleneck()}")
        """
        # Can only find critical path in DAG
        if len(find_circular_dependencies(self.graph)) > 0:
            return None

        # Use topological sort to process in dependency order
        try:
            topo_order = topological_sort(self.graph)
        except Exception:
            return None

        # Dynamic programming: track longest path to each node
        longest_path_to: dict[EntityID, list[EntityID]] = {}

        for node_id in reversed(topo_order):  # Process in reverse topological order
            # Get dependencies
            deps = self.graph.get_dependencies(node_id)

            if not deps:
                # Leaf node - path is just itself
                longest_path_to[node_id] = [node_id]
            else:
                # Find longest path through any dependency
                best_path: list[EntityID] = []
                for dep in deps:
                    dep_path = longest_path_to.get(dep.id, [dep.id])
                    if len(dep_path) > len(best_path):
                        best_path = dep_path

                # Prepend current node
                longest_path_to[node_id] = [node_id] + best_path

        # Find overall longest path
        if not longest_path_to:
            return None

        longest = max(longest_path_to.values(), key=len)

        return CriticalPath(
            path=tuple(longest),
            length=len(longest),
            total_weight=float(len(longest)),
        )

    def find_blast_radius(self, entity_id: EntityID) -> set[EntityID]:
        """Find blast radius (all entities affected by changes).
        
        Convenience method - equivalent to metrics.total_dependents
        
        Args:
            entity_id: Entity being changed
            
        Returns:
            Set of all entity IDs affected by the change
        """
        return get_transitive_dependents(self.graph, entity_id)

    def find_bottlenecks(self, min_dependents: int = 10) -> list[tuple[EntityID, int]]:
        """Find bottleneck entities (high-impact nodes).
        
        Bottlenecks are entities with many dependents - changes to these
        require careful coordination.
        
        Args:
            min_dependents: Minimum number of dependents to be considered a bottleneck
            
        Returns:
            List of (entity_id, dependent_count) tuples, sorted by dependent count
            
        Examples:
            >>> bottlenecks = analyzer.find_bottlenecks(min_dependents=20)
            >>> for entity_id, count in bottlenecks[:5]:
            ...     print(f"Entity {entity_id}: {count} dependents")
        """
        bottlenecks: list[tuple[EntityID, int]] = []

        # Check each node
        nx_graph = self.graph.to_networkx()
        for node_id in nx_graph.nodes():
            dependents = self.graph.get_dependents(node_id)
            if len(dependents) >= min_dependents:
                bottlenecks.append((node_id, len(dependents)))

        # Sort by dependent count (descending)
        bottlenecks.sort(key=lambda x: x[1], reverse=True)

        return bottlenecks

    # Private helper methods

    def _calculate_max_depth(
        self, entity_id: EntityID, direction: str = "dependents"
    ) -> int:
        """Calculate maximum depth in a given direction.
        
        Args:
            entity_id: Entity to calculate from
            direction: "dependents" or "dependencies"
            
        Returns:
            Maximum depth (number of hops)
        """
        visited: set[EntityID] = set()
        max_depth = 0

        def dfs(current_id: EntityID, depth: int) -> None:
            nonlocal max_depth

            if current_id in visited:
                return

            visited.add(current_id)
            max_depth = max(max_depth, depth)

            # Get next nodes based on direction
            if direction == "dependents":
                next_nodes = self.graph.get_dependents(current_id)
            else:
                next_nodes = self.graph.get_dependencies(current_id)

            for node in next_nodes:
                dfs(node.id, depth + 1)

        dfs(entity_id, 0)
        return max_depth

    def _find_critical_paths_involving(
        self, entity_id: EntityID, max_paths: int = 3
    ) -> tuple[CriticalPath, ...]:
        """Find critical paths that involve the given entity.
        
        Args:
            entity_id: Entity to find paths for
            max_paths: Maximum number of paths to return
            
        Returns:
            Tuple of critical paths
        """
        # For now, just return the single critical path if entity is on it
        critical = self.find_critical_path()

        if critical and entity_id in critical.path:
            return (critical,)

        return ()

    def _generate_recommendations(
        self, metrics: ImpactMetrics, circular_chains: tuple[tuple[EntityID, ...], ...]
    ) -> tuple[str, ...]:
        """Generate human-readable recommendations based on metrics.
        
        Args:
            metrics: Impact metrics
            circular_chains: Circular dependency chains
            
        Returns:
            Tuple of recommendation strings
        """
        recs: list[str] = []

        # High blast radius
        if metrics.total_dependents > 100:
            recs.append(
                f"High blast radius ({metrics.total_dependents} dependents) - "
                "coordinate with teams before deploying"
            )

        # Circular dependencies
        if circular_chains:
            recs.append(
                f"Entity involved in {len(circular_chains)} circular dependency "
                "chain(s) - resolve cycles before making breaking changes"
            )

        # Critical path
        if metrics.is_critical_path:
            recs.append(
                "Entity is on critical path - delays here will bottleneck entire deployment"
            )

        # Hub warning
        if metrics.is_hub():
            recs.append(
                f"{metrics.direct_dependents} direct dependents - "
                "consider gradual rollout or feature flags"
            )

        # Safe change
        if metrics.severity == ImpactSeverity.MINIMAL:
            recs.append("Low impact change - safe to proceed")

        return tuple(recs)

    def _calculate_risk_score(
        self, metrics: ImpactMetrics, circular_chains: tuple[tuple[EntityID, ...], ...]
    ) -> float:
        """Calculate overall risk score (0.0-1.0).
        
        Factors:
        - Blast radius (40% weight)
        - Circular dependencies (30% weight)
        - Critical path status (20% weight)
        - Hub status (10% weight)
        
        Args:
            metrics: Impact metrics
            circular_chains: Circular dependency chains
            
        Returns:
            Risk score from 0.0 (safe) to 1.0 (very risky)
        """
        score = 0.0

        # Blast radius contribution (40%)
        blast_score = min(metrics.total_dependents / 1000.0, 1.0)
        score += blast_score * 0.4

        # Circular dependency contribution (30%)
        if circular_chains:
            score += 0.3

        # Critical path contribution (20%)
        if metrics.is_critical_path:
            score += 0.2

        # Hub contribution (10%)
        if metrics.is_hub():
            score += 0.1

        return min(score, 1.0)
