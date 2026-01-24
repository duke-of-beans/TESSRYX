"""Query Engine - Natural language dependency queries.

This module provides a high-level query interface for asking questions about
dependencies. It translates intent into graph operations and returns
human-readable results.

The query engine supports:
- **What queries:** What depends on X? What does X depend on?
- **Why queries:** Why can't I upgrade X? Why does X depend on Y?
- **Impact queries:** What breaks if I change X? How risky is upgrading X?
- **Path queries:** How does X reach Y? What's between X and Y?
- **Circular queries:** What circular dependencies exist? Is X in a cycle?

Examples:
    >>> engine = QueryEngine(graph, analyzer)
    >>> 
    >>> # What depends on this package?
    >>> result = engine.query("what depends on react")
    >>> print(result.answer)
    "147 packages depend on react, including react-dom, next, gatsby..."
    >>> 
    >>> # Why can't I upgrade?
    >>> result = engine.query("why can't I upgrade lodash to 5.0")
    >>> print(result.answer)
    "12 packages in your project require lodash ^4.0.0. Breaking changes..."
    >>> 
    >>> # Impact analysis
    >>> result = engine.query("what breaks if I remove webpack")
    >>> print(result.answer)
    "Removing webpack would affect 23 packages. Risk: HIGH..."
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
    find_path,
    get_transitive_dependencies,
    get_transitive_dependents,
)
from tessryx.kernel.impact_analyzer import DependencyImpactAnalyzer


# ============================================================================
# QUERY TYPES
# ============================================================================


class QueryType(str, Enum):
    """Types of queries the engine can handle."""

    WHAT_DEPENDS_ON = "what_depends_on"  # What depends on X?
    WHAT_DEPENDENCIES = "what_dependencies"  # What does X depend on?
    WHY_DEPENDENCY = "why_dependency"  # Why does X depend on Y?
    WHY_CANT_UPGRADE = "why_cant_upgrade"  # Why can't I upgrade X?
    IMPACT_ANALYSIS = "impact_analysis"  # What breaks if I change X?
    PATH_QUERY = "path_query"  # How does X reach Y?
    CIRCULAR_CHECK = "circular_check"  # Is X in a circular dependency?
    LIST_CYCLES = "list_cycles"  # What circular dependencies exist?
    RISK_ASSESSMENT = "risk_assessment"  # How risky is changing X?
    UNKNOWN = "unknown"  # Could not determine query type


# ============================================================================
# QUERY RESULTS
# ============================================================================


@dataclass(frozen=True)
class QueryResult:
    """Result of a dependency query.
    
    Attributes:
        query: Original query string
        query_type: Detected query type
        answer: Human-readable answer
        entities: Relevant entities (if applicable)
        evidence: Supporting data/metrics
        confidence: Confidence in the answer (0.0-1.0)
        suggestions: Follow-up suggestions
    """

    query: str
    query_type: QueryType
    answer: str
    entities: tuple[EntityID, ...] = ()
    evidence: dict[str, Any] = None  # type: ignore[assignment]
    confidence: float = 1.0
    suggestions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Initialize default evidence dict."""
        if self.evidence is None:
            object.__setattr__(self, "evidence", {})

    def has_entities(self) -> bool:
        """Check if result includes entity references."""
        return len(self.entities) > 0

    def entity_count(self) -> int:
        """Get number of entities in result."""
        return len(self.entities)


# ============================================================================
# QUERY ENGINE
# ============================================================================


class QueryEngine:
    """High-level query interface for dependency questions.
    
    Translates natural language-ish queries into graph operations and
    returns human-readable answers.
    
    Examples:
        >>> engine = QueryEngine(graph, analyzer)
        >>> 
        >>> # What queries
        >>> result = engine.what_depends_on(react_id)
        >>> result = engine.what_dependencies(next_id)
        >>> 
        >>> # Why queries
        >>> result = engine.why_dependency(app_id, old_lib_id)
        >>> result = engine.why_cant_upgrade(lodash_id)
        >>> 
        >>> # Impact queries
        >>> result = engine.impact_of_change(webpack_id)
        >>> result = engine.risk_assessment(critical_lib_id)
        >>> 
        >>> # Path queries
        >>> result = engine.how_does_reach(app_id, deep_dep_id)
        >>> 
        >>> # Circular queries
        >>> result = engine.is_circular(package_id)
        >>> result = engine.list_all_cycles()
    """

    def __init__(
        self,
        graph: DependencyGraph,
        analyzer: DependencyImpactAnalyzer,
    ) -> None:
        """Initialize query engine.
        
        Args:
            graph: Dependency graph to query
            analyzer: Impact analyzer for risk assessment
        """
        self.graph = graph
        self.analyzer = analyzer

    # ========================================================================
    # WHAT QUERIES
    # ========================================================================

    def what_depends_on(self, entity_id: EntityID) -> QueryResult:
        """What packages depend on this entity?
        
        Args:
            entity_id: Entity to find dependents for
            
        Returns:
            Query result with dependents and counts
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return QueryResult(
                query=f"what depends on {entity_id}",
                query_type=QueryType.WHAT_DEPENDS_ON,
                answer=f"Entity {entity_id} not found in graph",
                confidence=0.0,
            )

        # Get direct and transitive dependents
        direct = self.graph.get_dependents(entity_id)
        transitive = get_transitive_dependents(self.graph, entity_id)

        # Build answer
        if len(transitive) == 0:
            answer = f"Nothing depends on {entity.name} (it's a leaf package)"
        else:
            answer = (
                f"{len(transitive)} package(s) depend on {entity.name}. "
                f"{len(direct)} direct, {len(transitive) - len(direct)} transitive."
            )

        # Add top dependents
        if direct:
            top_names = [d.name for d in direct[:5]]
            answer += f" Direct dependents include: {', '.join(top_names)}"
            if len(direct) > 5:
                answer += f", and {len(direct) - 5} more"

        return QueryResult(
            query=f"what depends on {entity.name}",
            query_type=QueryType.WHAT_DEPENDS_ON,
            answer=answer,
            entities=tuple(transitive),
            evidence={
                "direct_count": len(direct),
                "transitive_count": len(transitive),
                "is_leaf": len(transitive) == 0,
            },
            suggestions=(
                f"Run impact analysis to see what breaks if {entity.name} changes",
                f"Check if {entity.name} is on the critical path",
            ),
        )

    def what_dependencies(self, entity_id: EntityID) -> QueryResult:
        """What does this entity depend on?
        
        Args:
            entity_id: Entity to find dependencies for
            
        Returns:
            Query result with dependencies and counts
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return QueryResult(
                query=f"what dependencies {entity_id}",
                query_type=QueryType.WHAT_DEPENDENCIES,
                answer=f"Entity {entity_id} not found in graph",
                confidence=0.0,
            )

        # Get direct and transitive dependencies
        direct = self.graph.get_dependencies(entity_id)
        transitive = get_transitive_dependencies(self.graph, entity_id)

        # Build answer
        if len(transitive) == 0:
            answer = f"{entity.name} has no dependencies (it's a root package)"
        else:
            answer = (
                f"{entity.name} depends on {len(transitive)} package(s). "
                f"{len(direct)} direct, {len(transitive) - len(direct)} transitive."
            )

        # Add top dependencies
        if direct:
            top_names = [d.name for d in direct[:5]]
            answer += f" Direct dependencies: {', '.join(top_names)}"
            if len(direct) > 5:
                answer += f", and {len(direct) - 5} more"

        return QueryResult(
            query=f"what does {entity.name} depend on",
            query_type=QueryType.WHAT_DEPENDENCIES,
            answer=answer,
            entities=tuple(transitive),
            evidence={
                "direct_count": len(direct),
                "transitive_count": len(transitive),
                "is_root": len(transitive) == 0,
            },
            suggestions=(
                f"Check for circular dependencies involving {entity.name}",
                f"See the full dependency tree with 'show tree for {entity.name}'",
            ),
        )

    # ========================================================================
    # WHY QUERIES
    # ========================================================================

    def why_dependency(
        self,
        dependent_id: EntityID,
        dependency_id: EntityID,
    ) -> QueryResult:
        """Why does X depend on Y?
        
        Args:
            dependent_id: Entity that has the dependency
            dependency_id: Entity being depended on
            
        Returns:
            Query result explaining the dependency
        """
        dependent = self.graph.get_entity(dependent_id)
        dependency = self.graph.get_entity(dependency_id)

        if not dependent or not dependency:
            return QueryResult(
                query="why dependency",
                query_type=QueryType.WHY_DEPENDENCY,
                answer="One or both entities not found",
                confidence=0.0,
            )

        # Find path
        path = find_path(self.graph, dependent_id, dependency_id)

        if not path:
            answer = f"{dependent.name} does not depend on {dependency.name}"
            suggestions = (
                f"Check if {dependency.name} depends on {dependent.name} instead",
                "Verify both packages are in the same dependency graph",
            )
        elif len(path) == 2:
            # Direct dependency
            relation = self.graph.get_relation(dependent_id, dependency_id)
            answer = (
                f"{dependent.name} directly depends on {dependency.name}. "
                f"Relation type: {relation.type if relation else 'unknown'}"
            )
            suggestions = (
                f"Check {dependent.name}'s package.json or requirements.txt",
                f"See why {dependent.name} was added to the project",
            )
        else:
            # Transitive dependency
            path_entities = [self.graph.get_entity(eid) for eid in path]
            path_names = [e.name for e in path_entities if e]
            chain = " → ".join(path_names)

            answer = (
                f"{dependent.name} depends on {dependency.name} transitively. "
                f"Dependency chain ({len(path)} hops): {chain}"
            )
            suggestions = (
                f"Consider if you can remove the intermediate dependencies",
                f"Check if {dependency.name} can be upgraded independently",
            )

        return QueryResult(
            query=f"why does {dependent.name} depend on {dependency.name}",
            query_type=QueryType.WHY_DEPENDENCY,
            answer=answer,
            entities=tuple(path) if path else (),
            evidence={
                "is_direct": len(path) == 2 if path else False,
                "hops": len(path) - 1 if path else 0,
                "path": path,
            },
            suggestions=suggestions,
        )

    def why_cant_upgrade(self, entity_id: EntityID) -> QueryResult:
        """Why can't I upgrade this package?
        
        Checks for:
        - Circular dependencies that prevent upgrade
        - Critical path dependencies
        - High-risk blast radius
        
        Args:
            entity_id: Entity to check for upgrade blockers
            
        Returns:
            Query result with blockers and recommendations
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return QueryResult(
                query="why can't upgrade",
                query_type=QueryType.WHY_CANT_UPGRADE,
                answer="Entity not found",
                confidence=0.0,
            )

        # Check for blockers
        blockers = []

        # Check circular dependencies
        cycles = find_circular_dependencies(self.graph)
        in_cycle = any(entity_id in cycle for cycle in cycles)
        if in_cycle:
            blockers.append(
                f"{entity.name} is involved in a circular dependency - "
                "resolve the cycle first"
            )

        # Check impact
        impact = self.analyzer.analyze_change_impact(entity_id)
        if impact.metrics.is_high_risk():
            blockers.append(
                f"High blast radius: {impact.metrics.blast_radius()} packages affected"
            )

        if impact.metrics.is_critical_path:
            blockers.append(
                f"{entity.name} is on the critical path - delays will bottleneck deployment"
            )

        # Build answer
        if not blockers:
            answer = (
                f"No technical blockers for upgrading {entity.name}. "
                f"Risk score: {impact.risk_score:.2f}"
            )
            if impact.is_safe_to_change():
                answer += " ✅ Safe to upgrade."
            else:
                answer += f" ⚠️ Affects {len(impact.affected_entities)} packages."
        else:
            answer = f"Blockers for upgrading {entity.name}:\n"
            for i, blocker in enumerate(blockers, 1):
                answer += f"  {i}. {blocker}\n"

        return QueryResult(
            query=f"why can't I upgrade {entity.name}",
            query_type=QueryType.WHY_CANT_UPGRADE,
            answer=answer.strip(),
            entities=tuple(impact.affected_entities),
            evidence={
                "has_blockers": len(blockers) > 0,
                "blocker_count": len(blockers),
                "risk_score": impact.risk_score,
                "in_circular": in_cycle,
            },
            suggestions=tuple(impact.recommendations),
        )

    # ========================================================================
    # IMPACT QUERIES
    # ========================================================================

    def impact_of_change(self, entity_id: EntityID) -> QueryResult:
        """What breaks if I change/remove this package?
        
        Args:
            entity_id: Entity being changed
            
        Returns:
            Query result with impact analysis
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return QueryResult(
                query="impact of change",
                query_type=QueryType.IMPACT_ANALYSIS,
                answer="Entity not found",
                confidence=0.0,
            )

        impact = self.analyzer.analyze_change_impact(entity_id)

        # Build answer
        answer = f"Impact of changing {entity.name}:\n"
        answer += f"  • Blast radius: {len(impact.affected_entities)} packages\n"
        answer += f"  • Severity: {impact.metrics.severity.value.upper()}\n"
        answer += f"  • Risk score: {impact.risk_score:.2f}/1.00\n"

        if impact.is_safe_to_change():
            answer += "\n✅ Safe to proceed with changes"
        elif impact.requires_coordination():
            answer += "\n⚠️ Requires team coordination (>20 packages affected)"
        else:
            answer += "\n⚠️ Review recommendations before proceeding"

        return QueryResult(
            query=f"what breaks if I change {entity.name}",
            query_type=QueryType.IMPACT_ANALYSIS,
            answer=answer.strip(),
            entities=tuple(impact.affected_entities),
            evidence={
                "blast_radius": len(impact.affected_entities),
                "severity": impact.metrics.severity.value,
                "risk_score": impact.risk_score,
                "is_safe": impact.is_safe_to_change(),
            },
            suggestions=tuple(impact.recommendations),
        )

    def risk_assessment(self, entity_id: EntityID) -> QueryResult:
        """How risky is changing this package?
        
        Args:
            entity_id: Entity to assess
            
        Returns:
            Query result with risk assessment
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return QueryResult(
                query="risk assessment",
                query_type=QueryType.RISK_ASSESSMENT,
                answer="Entity not found",
                confidence=0.0,
            )

        impact = self.analyzer.analyze_change_impact(entity_id)
        metrics = impact.metrics

        # Risk level
        if impact.risk_score < 0.3:
            risk_level = "LOW"
            emoji = "✅"
        elif impact.risk_score < 0.6:
            risk_level = "MEDIUM"
            emoji = "⚠️"
        else:
            risk_level = "HIGH"
            emoji = "🚨"

        answer = f"{emoji} Risk assessment for {entity.name}: {risk_level}\n\n"
        answer += f"Risk Score: {impact.risk_score:.2f}/1.00\n"
        answer += f"Blast Radius: {metrics.blast_radius()} packages\n"
        answer += f"Severity: {metrics.severity.value.upper()}\n"

        if metrics.is_hub():
            answer += f"Hub Package: {metrics.direct_dependents} direct dependents\n"

        if metrics.is_critical_path:
            answer += "On Critical Path: Delays will bottleneck deployment\n"

        if metrics.circular_dependencies > 0:
            answer += f"Circular Dependencies: {metrics.circular_dependencies} cycle(s)\n"

        return QueryResult(
            query=f"how risky is {entity.name}",
            query_type=QueryType.RISK_ASSESSMENT,
            answer=answer.strip(),
            entities=tuple(impact.affected_entities),
            evidence={
                "risk_score": impact.risk_score,
                "risk_level": risk_level,
                "blast_radius": metrics.blast_radius(),
                "is_hub": metrics.is_hub(),
                "is_critical": metrics.is_critical_path,
            },
            suggestions=tuple(impact.recommendations),
        )

    # ========================================================================
    # PATH QUERIES
    # ========================================================================

    def how_does_reach(
        self,
        source_id: EntityID,
        target_id: EntityID,
    ) -> QueryResult:
        """How does X reach Y? (Dependency path)
        
        Args:
            source_id: Starting entity
            target_id: Target entity
            
        Returns:
            Query result with dependency path(s)
        """
        source = self.graph.get_entity(source_id)
        target = self.graph.get_entity(target_id)

        if not source or not target:
            return QueryResult(
                query="how does reach",
                query_type=QueryType.PATH_QUERY,
                answer="One or both entities not found",
                confidence=0.0,
            )

        path = find_path(self.graph, source_id, target_id)

        if not path:
            answer = f"{source.name} does not reach {target.name}"
            suggestions = (
                f"Check if {target.name} reaches {source.name} instead",
                "They may be in separate dependency subgraphs",
            )
        else:
            path_entities = [self.graph.get_entity(eid) for eid in path]
            path_names = [e.name for e in path_entities if e]
            chain = " → ".join(path_names)

            answer = (
                f"{source.name} reaches {target.name} in {len(path) - 1} hop(s):\n"
                f"{chain}"
            )
            suggestions = (
                "Find all paths to see alternative dependency routes",
                "Check if this path includes any circular dependencies",
            )

        return QueryResult(
            query=f"how does {source.name} reach {target.name}",
            query_type=QueryType.PATH_QUERY,
            answer=answer,
            entities=tuple(path) if path else (),
            evidence={
                "has_path": path is not None,
                "hops": len(path) - 1 if path else 0,
                "path": path,
            },
            suggestions=suggestions,
        )

    # ========================================================================
    # CIRCULAR DEPENDENCY QUERIES
    # ========================================================================

    def is_circular(self, entity_id: EntityID) -> QueryResult:
        """Is this package in a circular dependency?
        
        Args:
            entity_id: Entity to check
            
        Returns:
            Query result indicating circular dependency status
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return QueryResult(
                query="is circular",
                query_type=QueryType.CIRCULAR_CHECK,
                answer="Entity not found",
                confidence=0.0,
            )

        cycles = find_circular_dependencies(self.graph)
        entity_cycles = [cycle for cycle in cycles if entity_id in cycle]

        if not entity_cycles:
            answer = f"✅ {entity.name} is not in any circular dependencies"
            suggestions = ("Continue with normal dependency management",)
        else:
            answer = f"🔄 {entity.name} is in {len(entity_cycles)} circular dependency chain(s)"

            # Show first cycle
            first_cycle = entity_cycles[0]
            cycle_entities = [self.graph.get_entity(eid) for eid in first_cycle]
            cycle_names = [e.name for e in cycle_entities if e]
            chain = " → ".join(cycle_names + [cycle_names[0]])  # Close the loop

            answer += f"\n\nCycle: {chain}"

            suggestions = (
                "Resolve circular dependencies before making breaking changes",
                f"Investigate why {entity.name} has circular dependencies",
            )

        return QueryResult(
            query=f"is {entity.name} circular",
            query_type=QueryType.CIRCULAR_CHECK,
            answer=answer,
            entities=tuple(entity_cycles[0]) if entity_cycles else (),
            evidence={
                "is_circular": len(entity_cycles) > 0,
                "cycle_count": len(entity_cycles),
            },
            suggestions=suggestions,
        )

    def list_all_cycles(self) -> QueryResult:
        """List all circular dependencies in the graph.
        
        Returns:
            Query result with all circular dependencies
        """
        cycles = find_circular_dependencies(self.graph)

        if not cycles:
            answer = "✅ No circular dependencies found in the graph"
            suggestions = ("Dependency graph is a DAG (Directed Acyclic Graph)",)
        else:
            answer = f"🔄 Found {len(cycles)} circular dependency chain(s):\n\n"

            for i, cycle in enumerate(cycles[:5], 1):  # Show first 5
                cycle_entities = [self.graph.get_entity(eid) for eid in cycle]
                cycle_names = [e.name for e in cycle_entities if e]
                chain = " → ".join(cycle_names + [cycle_names[0]])

                answer += f"{i}. {chain}\n"

            if len(cycles) > 5:
                answer += f"\n... and {len(cycles) - 5} more cycles"

            suggestions = (
                "Resolve circular dependencies to enable safe upgrades",
                "Use topological sort to identify dependency order",
            )

        return QueryResult(
            query="list all circular dependencies",
            query_type=QueryType.LIST_CYCLES,
            answer=answer.strip(),
            entities=tuple(eid for cycle in cycles for eid in cycle),
            evidence={
                "cycle_count": len(cycles),
                "total_entities_in_cycles": len(
                    set(eid for cycle in cycles for eid in cycle)
                ),
            },
            suggestions=suggestions,
        )
