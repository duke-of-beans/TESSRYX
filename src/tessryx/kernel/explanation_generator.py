"""Explanation Generator - Why, why-not, and alternatives.

This module generates detailed explanations for dependency decisions and
constraints. It answers:
- **Why:** Why does this configuration satisfy the constraints?
- **Why Not:** Why doesn't this alternative work?
- **Alternatives:** What other solutions exist?
- **Trade-offs:** What are the pros/cons of each option?

The explanation generator uses:
- Constraint analysis
- Graph operations
- Impact analysis
- Provenance data

Examples:
    >>> explainer = ExplanationGenerator(graph, analyzer, ledger)
    >>> 
    >>> # Why does this work?
    >>> why = explainer.explain_why(
    ...     entity_id=package_id,
    ...     context="why does this package configuration work"
    ... )
    >>> print(why.explanation)
    "This configuration works because: 1) No circular dependencies..."
    >>> 
    >>> # Why doesn't this work?
    >>> why_not = explainer.explain_why_not(
    ...     entity_id=incompatible_id,
    ...     attempted_action="upgrade to v5.0",
    ...     context="why can't I upgrade"
    ... )
    >>> print(why_not.explanation)
    "Upgrade blocked because: 1) 12 packages require v4.x..."
    >>> 
    >>> # What are alternatives?
    >>> alts = explainer.generate_alternatives(
    ...     entity_id=package_id,
    ...     constraint="must remove this dependency"
    ... )
    >>> for alt in alts.alternatives:
    ...     print(f"- {alt.description} (feasibility: {alt.feasibility:.2f})")
"""

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from tessryx.core.types import EntityID
from tessryx.kernel.graph_ops import (
    DependencyGraph,
    find_circular_dependencies,
    find_path,
    get_transitive_dependencies,
    get_transitive_dependents,
)
from tessryx.kernel.impact_analyzer import DependencyImpactAnalyzer
from tessryx.kernel.provenance_ledger import ProvenanceLedger


# ============================================================================
# EXPLANATION TYPES
# ============================================================================


class ExplanationType(str, Enum):
    """Types of explanations."""

    WHY = "why"  # Why this works/is true
    WHY_NOT = "why_not"  # Why this doesn't work/is false
    ALTERNATIVES = "alternatives"  # What else could work
    TRADE_OFFS = "trade_offs"  # Pros/cons comparison


class ConfidenceLevel(str, Enum):
    """Confidence in explanation."""

    CERTAIN = "certain"  # 0.9-1.0
    HIGH = "high"  # 0.7-0.9
    MEDIUM = "medium"  # 0.4-0.7
    LOW = "low"  # 0.0-0.4


# ============================================================================
# EXPLANATION COMPONENTS
# ============================================================================


@dataclass(frozen=True)
class Reason:
    """A single reason in an explanation.
    
    Attributes:
        description: Human-readable reason
        evidence: Supporting data/metrics
        confidence: Confidence in this reason (0.0-1.0)
        weight: Importance weight (0.0-1.0)
    """

    description: str
    evidence: dict[str, object] = None  # type: ignore[assignment]
    confidence: float = 1.0
    weight: float = 1.0

    def __post_init__(self) -> None:
        """Initialize default evidence dict."""
        if self.evidence is None:
            object.__setattr__(self, "evidence", {})


@dataclass(frozen=True)
class Alternative:
    """An alternative solution or approach.
    
    Attributes:
        description: What this alternative does
        feasibility: How feasible (0.0-1.0)
        impact: Expected impact/changes
        pros: Advantages
        cons: Disadvantages
        steps: Implementation steps
    """

    description: str
    feasibility: float
    impact: str = ""
    pros: tuple[str, ...] = ()
    cons: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()

    def is_feasible(self) -> bool:
        """Check if alternative is feasible (>0.5)."""
        return self.feasibility > 0.5

    def is_highly_feasible(self) -> bool:
        """Check if alternative is highly feasible (>0.8)."""
        return self.feasibility > 0.8


# ============================================================================
# EXPLANATION RESULTS
# ============================================================================


@dataclass(frozen=True)
class Explanation:
    """Complete explanation with reasons and confidence.
    
    Attributes:
        explanation_type: Type of explanation
        question: Original question
        explanation: Main explanation text
        reasons: Individual reasons
        confidence: Overall confidence
        confidence_level: Categorized confidence
        suggestions: Follow-up suggestions
    """

    explanation_type: ExplanationType
    question: str
    explanation: str
    reasons: tuple[Reason, ...] = ()
    confidence: float = 1.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.CERTAIN
    suggestions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Derive confidence level from confidence score."""
        if self.confidence_level == ConfidenceLevel.CERTAIN:
            # Auto-compute confidence level
            if self.confidence >= 0.9:
                level = ConfidenceLevel.CERTAIN
            elif self.confidence >= 0.7:
                level = ConfidenceLevel.HIGH
            elif self.confidence >= 0.4:
                level = ConfidenceLevel.MEDIUM
            else:
                level = ConfidenceLevel.LOW

            object.__setattr__(self, "confidence_level", level)

    def reason_count(self) -> int:
        """Get number of reasons."""
        return len(self.reasons)

    def primary_reason(self) -> Reason | None:
        """Get most important reason (highest weight)."""
        if not self.reasons:
            return None
        return max(self.reasons, key=lambda r: r.weight)


@dataclass(frozen=True)
class AlternativesExplanation:
    """Explanation with multiple alternatives.
    
    Attributes:
        question: Original question
        explanation: Overview of alternatives
        alternatives: Available alternatives
        recommended: Most feasible alternative (if any)
        confidence: Overall confidence
    """

    question: str
    explanation: str
    alternatives: tuple[Alternative, ...] = ()
    recommended: Alternative | None = None
    confidence: float = 1.0

    def has_feasible_alternatives(self) -> bool:
        """Check if any alternatives are feasible."""
        return any(alt.is_feasible() for alt in self.alternatives)

    def feasible_alternatives(self) -> tuple[Alternative, ...]:
        """Get only feasible alternatives."""
        return tuple(alt for alt in self.alternatives if alt.is_feasible())


# ============================================================================
# EXPLANATION GENERATOR
# ============================================================================


class ExplanationGenerator:
    """Generate detailed explanations for dependency decisions.
    
    Combines graph analysis, impact metrics, and provenance data to
    explain why things work or don't work.
    
    Examples:
        >>> explainer = ExplanationGenerator(graph, analyzer, ledger)
        >>> 
        >>> # Why does X depend on Y?
        >>> why = explainer.explain_why_dependency(app_id, lib_id)
        >>> 
        >>> # Why can't I remove X?
        >>> why_not = explainer.explain_why_not_remove(package_id)
        >>> 
        >>> # What are alternatives to X?
        >>> alts = explainer.generate_dependency_alternatives(package_id)
    """

    def __init__(
        self,
        graph: DependencyGraph,
        analyzer: DependencyImpactAnalyzer,
        ledger: ProvenanceLedger | None = None,
    ) -> None:
        """Initialize explanation generator.
        
        Args:
            graph: Dependency graph
            analyzer: Impact analyzer
            ledger: Provenance ledger (optional)
        """
        self.graph = graph
        self.analyzer = analyzer
        self.ledger = ledger

    # ========================================================================
    # WHY EXPLANATIONS
    # ========================================================================

    def explain_why_dependency(
        self,
        dependent_id: EntityID,
        dependency_id: EntityID,
    ) -> Explanation:
        """Explain why X depends on Y.
        
        Args:
            dependent_id: Dependent entity
            dependency_id: Dependency entity
            
        Returns:
            Explanation with reasons for dependency
        """
        dependent = self.graph.get_entity(dependent_id)
        dependency = self.graph.get_entity(dependency_id)

        if not dependent or not dependency:
            return Explanation(
                explanation_type=ExplanationType.WHY,
                question=f"why does {dependent_id} depend on {dependency_id}",
                explanation="One or both entities not found",
                confidence=0.0,
            )

        reasons = []

        # Find path
        path = find_path(self.graph, dependent_id, dependency_id)

        if not path:
            return Explanation(
                explanation_type=ExplanationType.WHY,
                question=f"why does {dependent.name} depend on {dependency.name}",
                explanation=f"{dependent.name} does not depend on {dependency.name}",
                confidence=1.0,
            )

        # Direct vs transitive
        if len(path) == 2:
            relation = self.graph.get_relation(dependent_id, dependency_id)
            reasons.append(
                Reason(
                    description=f"Direct dependency: {dependent.name} → {dependency.name}",
                    evidence={
                        "relation_type": relation.type if relation else "unknown",
                        "is_direct": True,
                    },
                    weight=1.0,
                )
            )

            # Check provenance if available
            if self.ledger:
                prov = self.ledger.get_provenance(dependent_id)
                if prov:
                    reasons.append(
                        Reason(
                            description=f"Added by {prov[-1].asserted_by} with confidence {prov[-1].confidence:.2f}",
                            evidence={"source": prov[-1].source.value},
                            confidence=prov[-1].confidence,
                            weight=0.5,
                        )
                    )

            explanation = (
                f"{dependent.name} directly depends on {dependency.name}. "
                f"This is an explicit dependency defined in the project."
            )
        else:
            # Transitive dependency
            reasons.append(
                Reason(
                    description=f"Transitive dependency through {len(path) - 2} intermediate package(s)",
                    evidence={
                        "path_length": len(path),
                        "is_direct": False,
                    },
                    weight=1.0,
                )
            )

            # Show path
            path_entities = [self.graph.get_entity(eid) for eid in path]
            path_names = [e.name for e in path_entities if e]
            chain = " → ".join(path_names)

            explanation = (
                f"{dependent.name} depends on {dependency.name} transitively. "
                f"Dependency chain: {chain}"
            )

        return Explanation(
            explanation_type=ExplanationType.WHY,
            question=f"why does {dependent.name} depend on {dependency.name}",
            explanation=explanation,
            reasons=tuple(reasons),
            confidence=1.0,
            suggestions=(
                f"Check if {dependency.name} is actually needed",
                "Consider if dependency can be made optional",
            ),
        )

    def explain_why_safe(self, entity_id: EntityID) -> Explanation:
        """Explain why changing this entity is safe.
        
        Args:
            entity_id: Entity to analyze
            
        Returns:
            Explanation of safety (or lack thereof)
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return Explanation(
                explanation_type=ExplanationType.WHY,
                question="why safe",
                explanation="Entity not found",
                confidence=0.0,
            )

        impact = self.analyzer.analyze_change_impact(entity_id)
        reasons = []

        # Build reasons based on metrics
        if impact.metrics.blast_radius() == 0:
            reasons.append(
                Reason(
                    description=f"{entity.name} has no dependents (leaf package)",
                    evidence={"blast_radius": 0},
                    weight=1.0,
                )
            )

        if impact.metrics.blast_radius() < 5:
            reasons.append(
                Reason(
                    description=f"Minimal blast radius ({impact.metrics.blast_radius()} packages)",
                    evidence={"blast_radius": impact.metrics.blast_radius()},
                    weight=0.8,
                )
            )

        if impact.metrics.circular_dependencies == 0:
            reasons.append(
                Reason(
                    description="No circular dependencies",
                    evidence={"circular_count": 0},
                    weight=0.6,
                )
            )

        if not impact.metrics.is_critical_path:
            reasons.append(
                Reason(
                    description="Not on critical path",
                    evidence={"is_critical": False},
                    weight=0.5,
                )
            )

        # Build explanation
        if impact.is_safe_to_change():
            explanation = (
                f"✅ Changing {entity.name} is safe. "
                f"Risk score: {impact.risk_score:.2f}/1.00. "
            )
            explanation += " ".join(r.description for r in reasons[:2])
        else:
            explanation = (
                f"⚠️ Changing {entity.name} requires care. "
                f"Risk score: {impact.risk_score:.2f}/1.00. "
            )
            if not reasons:
                explanation += f"Affects {len(impact.affected_entities)} packages."

        return Explanation(
            explanation_type=ExplanationType.WHY,
            question=f"why is {entity.name} safe to change",
            explanation=explanation,
            reasons=tuple(reasons),
            confidence=1.0 - impact.risk_score,  # Higher risk = lower confidence
            suggestions=tuple(impact.recommendations),
        )

    # ========================================================================
    # WHY NOT EXPLANATIONS
    # ========================================================================

    def explain_why_not_remove(self, entity_id: EntityID) -> Explanation:
        """Explain why this entity can't be removed.
        
        Args:
            entity_id: Entity to check
            
        Returns:
            Explanation of removal blockers
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return Explanation(
                explanation_type=ExplanationType.WHY_NOT,
                question="why not remove",
                explanation="Entity not found",
                confidence=0.0,
            )

        reasons = []
        dependents = get_transitive_dependents(self.graph, entity_id)

        if len(dependents) == 0:
            return Explanation(
                explanation_type=ExplanationType.WHY_NOT,
                question=f"why not remove {entity.name}",
                explanation=f"✅ {entity.name} can be safely removed (no dependents)",
                confidence=1.0,
            )

        # Blocker: has dependents
        direct = self.graph.get_dependents(entity_id)
        reasons.append(
            Reason(
                description=f"{len(dependents)} package(s) depend on {entity.name}",
                evidence={
                    "direct_dependents": len(direct),
                    "total_dependents": len(dependents),
                },
                weight=1.0,
            )
        )

        # List top dependents
        if direct:
            top_names = [d.name for d in direct[:3]]
            reasons.append(
                Reason(
                    description=f"Direct dependents: {', '.join(top_names)}",
                    evidence={"top_dependents": top_names},
                    weight=0.8,
                )
            )

        # Check if on critical path
        impact = self.analyzer.analyze_change_impact(entity_id)
        if impact.metrics.is_critical_path:
            reasons.append(
                Reason(
                    description=f"{entity.name} is on the critical deployment path",
                    evidence={"is_critical": True},
                    weight=0.9,
                )
            )

        explanation = (
            f"❌ Cannot remove {entity.name}. "
            f"{len(dependents)} package(s) would break. "
        )
        if direct:
            top_names = [d.name for d in direct[:3]]
            explanation += f"Direct dependents: {', '.join(top_names)}"
            if len(direct) > 3:
                explanation += f", and {len(direct) - 3} more"

        return Explanation(
            explanation_type=ExplanationType.WHY_NOT,
            question=f"why can't I remove {entity.name}",
            explanation=explanation,
            reasons=tuple(reasons),
            confidence=1.0,
            suggestions=(
                f"Migrate dependents away from {entity.name} first",
                "Or deprecate gradually with a migration path",
            ),
        )

    def explain_why_not_upgrade(
        self,
        entity_id: EntityID,
        target_version: str | None = None,
    ) -> Explanation:
        """Explain why entity can't be upgraded.
        
        Args:
            entity_id: Entity to upgrade
            target_version: Target version (optional)
            
        Returns:
            Explanation of upgrade blockers
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return Explanation(
                explanation_type=ExplanationType.WHY_NOT,
                question="why not upgrade",
                explanation="Entity not found",
                confidence=0.0,
            )

        reasons = []

        # Check circular dependencies
        cycles = find_circular_dependencies(self.graph)
        in_cycle = any(entity_id in cycle for cycle in cycles)

        if in_cycle:
            reasons.append(
                Reason(
                    description=f"{entity.name} is in a circular dependency",
                    evidence={"in_cycle": True},
                    weight=1.0,
                )
            )

        # Check impact
        impact = self.analyzer.analyze_change_impact(entity_id)

        if impact.metrics.is_high_risk():
            reasons.append(
                Reason(
                    description=f"High-risk change: {impact.metrics.blast_radius()} packages affected",
                    evidence={
                        "blast_radius": impact.metrics.blast_radius(),
                        "severity": impact.metrics.severity.value,
                    },
                    weight=0.9,
                )
            )

        if impact.metrics.is_hub():
            reasons.append(
                Reason(
                    description=f"Hub package: {impact.metrics.direct_dependents} direct dependents",
                    evidence={"is_hub": True},
                    weight=0.7,
                )
            )

        # Build explanation
        if not reasons:
            version_str = f" to {target_version}" if target_version else ""
            explanation = (
                f"✅ No technical blockers for upgrading {entity.name}{version_str}. "
                f"Risk score: {impact.risk_score:.2f}/1.00"
            )
        else:
            version_str = f" to {target_version}" if target_version else ""
            explanation = (
                f"⚠️ Upgrade of {entity.name}{version_str} blocked:\n"
            )
            for i, reason in enumerate(reasons, 1):
                explanation += f"  {i}. {reason.description}\n"
            explanation = explanation.strip()

        return Explanation(
            explanation_type=ExplanationType.WHY_NOT,
            question=f"why can't I upgrade {entity.name}",
            explanation=explanation,
            reasons=tuple(reasons),
            confidence=1.0,
            suggestions=tuple(impact.recommendations) if reasons else (),
        )

    # ========================================================================
    # ALTERNATIVES
    # ========================================================================

    def generate_dependency_alternatives(
        self,
        entity_id: EntityID,
    ) -> AlternativesExplanation:
        """Generate alternatives for removing/replacing a dependency.
        
        Args:
            entity_id: Dependency to replace
            
        Returns:
            Alternative solutions
        """
        entity = self.graph.get_entity(entity_id)
        if not entity:
            return AlternativesExplanation(
                question="alternatives",
                explanation="Entity not found",
                confidence=0.0,
            )

        alternatives = []
        dependents = get_transitive_dependents(self.graph, entity_id)

        # Alternative 1: Direct removal
        if len(dependents) == 0:
            alternatives.append(
                Alternative(
                    description=f"Remove {entity.name} directly (no dependents)",
                    feasibility=1.0,
                    impact="No packages affected",
                    pros=("Clean removal", "No migration needed"),
                    cons=(),
                    steps=(f"1. Delete {entity.name} from dependencies",),
                )
            )
        else:
            # Alternative 2: Migrate dependents first
            alternatives.append(
                Alternative(
                    description=f"Migrate {len(dependents)} dependent(s) away from {entity.name}",
                    feasibility=0.6,
                    impact=f"{len(dependents)} packages need updates",
                    pros=("Complete removal", "Clean dependency tree"),
                    cons=(
                        f"Requires updating {len(dependents)} packages",
                        "May introduce breaking changes",
                    ),
                    steps=(
                        "1. Identify alternative package",
                        f"2. Update {len(dependents)} dependents",
                        "3. Test all affected packages",
                        f"4. Remove {entity.name}",
                    ),
                )
            )

        # Alternative 3: Gradual deprecation
        if len(dependents) > 5:
            alternatives.append(
                Alternative(
                    description=f"Gradual deprecation of {entity.name}",
                    feasibility=0.8,
                    impact="Phased migration over time",
                    pros=(
                        "Lower risk",
                        "Controlled rollout",
                        "Time for testing",
                    ),
                    cons=(
                        "Longer timeline",
                        "Temporary dual dependencies",
                    ),
                    steps=(
                        "1. Announce deprecation",
                        "2. Provide migration guide",
                        "3. Support both old and new",
                        "4. Migrate packages in phases",
                        "5. Remove after all migrated",
                    ),
                )
            )

        # Alternative 4: Mark as optional
        alternatives.append(
            Alternative(
                description=f"Make {entity.name} an optional dependency",
                feasibility=0.5,
                impact="Dependents continue working",
                pros=(
                    "No breaking changes",
                    "Reduces footprint for new users",
                ),
                cons=(
                    "Doesn't remove dependency",
                    "May still have version conflicts",
                ),
                steps=(
                    "1. Move to optionalDependencies",
                    "2. Add runtime checks",
                    "3. Document optional usage",
                ),
            ),
        )

        # Pick recommendation (most feasible)
        recommended = max(alternatives, key=lambda a: a.feasibility)

        explanation = f"Found {len(alternatives)} alternatives for {entity.name}:"

        return AlternativesExplanation(
            question=f"alternatives to {entity.name}",
            explanation=explanation,
            alternatives=tuple(alternatives),
            recommended=recommended if recommended.is_feasible() else None,
            confidence=0.8,
        )
