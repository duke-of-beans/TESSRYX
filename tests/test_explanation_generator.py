"""Unit tests for Explanation Generator.

Tests the detailed explanation system for why/why-not/alternatives.
"""

from uuid import uuid4

import pytest

from tessryx.core.entity import Entity
from tessryx.core.relation import Relation
from tessryx.kernel.explanation_generator import (
    Alternative,
    ConfidenceLevel,
    Explanation,
    ExplanationGenerator,
    ExplanationType,
    Reason,
)
from tessryx.kernel.graph_ops import DependencyGraph
from tessryx.kernel.impact_analyzer import DependencyImpactAnalyzer


class TestReasonDataclass:
    """Tests for Reason dataclass."""

    def test_reason_creation(self) -> None:
        """Test creating a reason."""
        reason = Reason(
            description="Test reason",
            evidence={"key": "value"},
            confidence=0.9,
            weight=0.8,
        )

        assert reason.description == "Test reason"
        assert reason.evidence["key"] == "value"
        assert reason.confidence == 0.9
        assert reason.weight == 0.8

    def test_reason_default_evidence(self) -> None:
        """Test reason with default evidence dict."""
        reason = Reason(description="Test")

        assert reason.evidence == {}
        assert reason.confidence == 1.0
        assert reason.weight == 1.0


class TestAlternativeDataclass:
    """Tests for Alternative dataclass."""

    def test_alternative_is_feasible(self) -> None:
        """Test feasibility check."""
        feasible = Alternative(description="Test", feasibility=0.8)
        not_feasible = Alternative(description="Test", feasibility=0.3)

        assert feasible.is_feasible()
        assert not not_feasible.is_feasible()

    def test_alternative_is_highly_feasible(self) -> None:
        """Test highly feasible check."""
        highly = Alternative(description="Test", feasibility=0.9)
        moderately = Alternative(description="Test", feasibility=0.6)

        assert highly.is_highly_feasible()
        assert not moderately.is_highly_feasible()


class TestExplanationDataclass:
    """Tests for Explanation dataclass."""

    def test_confidence_level_derivation(self) -> None:
        """Test auto-derivation of confidence level."""
        certain = Explanation(
            explanation_type=ExplanationType.WHY,
            question="test",
            explanation="test",
            confidence=0.95,
        )
        high = Explanation(
            explanation_type=ExplanationType.WHY,
            question="test",
            explanation="test",
            confidence=0.75,
        )
        medium = Explanation(
            explanation_type=ExplanationType.WHY,
            question="test",
            explanation="test",
            confidence=0.5,
        )
        low = Explanation(
            explanation_type=ExplanationType.WHY,
            question="test",
            explanation="test",
            confidence=0.2,
        )

        assert certain.confidence_level == ConfidenceLevel.CERTAIN
        assert high.confidence_level == ConfidenceLevel.HIGH
        assert medium.confidence_level == ConfidenceLevel.MEDIUM
        assert low.confidence_level == ConfidenceLevel.LOW

    def test_primary_reason(self) -> None:
        """Test getting primary (highest weight) reason."""
        reasons = (
            Reason(description="A", weight=0.5),
            Reason(description="B", weight=0.9),
            Reason(description="C", weight=0.3),
        )

        explanation = Explanation(
            explanation_type=ExplanationType.WHY,
            question="test",
            explanation="test",
            reasons=reasons,
        )

        primary = explanation.primary_reason()
        assert primary is not None
        assert primary.description == "B"
        assert primary.weight == 0.9

    def test_primary_reason_no_reasons(self) -> None:
        """Test primary reason when no reasons exist."""
        explanation = Explanation(
            explanation_type=ExplanationType.WHY,
            question="test",
            explanation="test",
        )

        assert explanation.primary_reason() is None


class TestWhyDependencyExplanations:
    """Tests for why dependency explanations."""

    def test_explain_why_direct_dependency(self) -> None:
        """Test explanation for direct dependency."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_dependency(a.id, b.id)

        assert explanation.explanation_type == ExplanationType.WHY
        assert "directly depends" in explanation.explanation
        assert len(explanation.reasons) > 0
        assert explanation.reasons[0].evidence["is_direct"]

    def test_explain_why_transitive_dependency(self) -> None:
        """Test explanation for transitive dependency."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")
        c = Entity(id=uuid4(), type="package", name="c")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_entity(c)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=b.id, to_entity_id=c.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_dependency(a.id, c.id)

        assert explanation.explanation_type == ExplanationType.WHY
        assert "transitively" in explanation.explanation
        assert "a → b → c" in explanation.explanation
        assert not explanation.reasons[0].evidence["is_direct"]

    def test_explain_why_no_dependency(self) -> None:
        """Test explanation when no dependency exists."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = graph.add_entity(a).add_entity(b)

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_dependency(a.id, b.id)

        assert "does not depend" in explanation.explanation


class TestWhySafeExplanations:
    """Tests for why safe explanations."""

    def test_explain_why_safe_leaf(self) -> None:
        """Test explanation for why leaf package is safe."""
        graph = DependencyGraph()
        leaf = Entity(id=uuid4(), type="package", name="leaf")
        graph = graph.add_entity(leaf)

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_safe(leaf.id)

        assert "safe" in explanation.explanation.lower()
        assert any("no dependents" in r.description or "leaf" in r.description for r in explanation.reasons)
        assert explanation.confidence > 0.8

    def test_explain_why_safe_hub(self) -> None:
        """Test explanation for hub package (not safe)."""
        graph = DependencyGraph()
        hub = Entity(id=uuid4(), type="package", name="hub")
        deps = [Entity(id=uuid4(), type="package", name=f"dep_{i}") for i in range(30)]

        graph = graph.add_entity(hub)
        for dep in deps:
            graph = graph.add_entity(dep).add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity_id=dep.id, to_entity_id=hub.id)
            )

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_safe(hub.id)

        assert "requires care" in explanation.explanation.lower() or "⚠" in explanation.explanation
        assert explanation.confidence < 0.5  # High risk = low confidence


class TestWhyNotRemoveExplanations:
    """Tests for why not remove explanations."""

    def test_explain_why_not_remove_can_remove(self) -> None:
        """Test explanation when package can be removed."""
        graph = DependencyGraph()
        leaf = Entity(id=uuid4(), type="package", name="leaf")
        graph = graph.add_entity(leaf)

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_not_remove(leaf.id)

        assert explanation.explanation_type == ExplanationType.WHY_NOT
        assert "can be safely removed" in explanation.explanation
        assert explanation.confidence == 1.0

    def test_explain_why_not_remove_has_dependents(self) -> None:
        """Test explanation when package has dependents."""
        graph = DependencyGraph()
        hub = Entity(id=uuid4(), type="package", name="hub")
        dep1 = Entity(id=uuid4(), type="package", name="dep1")
        dep2 = Entity(id=uuid4(), type="package", name="dep2")

        graph = (
            graph.add_entity(hub)
            .add_entity(dep1)
            .add_entity(dep2)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=dep1.id, to_entity_id=hub.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=dep2.id, to_entity_id=hub.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_not_remove(hub.id)

        assert "Cannot remove" in explanation.explanation
        assert "2 package(s)" in explanation.explanation
        assert len(explanation.reasons) > 0
        assert explanation.reasons[0].evidence["total_dependents"] == 2


class TestWhyNotUpgradeExplanations:
    """Tests for why not upgrade explanations."""

    def test_explain_why_not_upgrade_no_blockers(self) -> None:
        """Test explanation when no upgrade blockers exist."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_not_upgrade(b.id)

        assert "No technical blockers" in explanation.explanation
        assert len(explanation.reasons) == 0

    def test_explain_why_not_upgrade_circular(self) -> None:
        """Test explanation when circular dependency blocks upgrade."""
        graph = DependencyGraph()
        a = Entity(id=uuid4(), type="package", name="a")
        b = Entity(id=uuid4(), type="package", name="b")

        graph = (
            graph.add_entity(a)
            .add_entity(b)
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=a.id, to_entity_id=b.id))
            .add_relation(Relation(id=uuid4(), type="depends_on", from_entity_id=b.id, to_entity_id=a.id))
        )

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_not_upgrade(a.id, "2.0")

        assert "blocked" in explanation.explanation.lower()
        assert any("circular" in r.description for r in explanation.reasons)
        assert explanation.reasons[0].evidence["in_cycle"]

    def test_explain_why_not_upgrade_high_risk(self) -> None:
        """Test explanation when upgrade is high risk."""
        graph = DependencyGraph()
        hub = Entity(id=uuid4(), type="package", name="hub")
        deps = [Entity(id=uuid4(), type="package", name=f"dep_{i}") for i in range(150)]

        graph = graph.add_entity(hub)
        for dep in deps:
            graph = graph.add_entity(dep).add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity_id=dep.id, to_entity_id=hub.id)
            )

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        explanation = explainer.explain_why_not_upgrade(hub.id)

        assert len(explanation.reasons) > 0
        assert any("high-risk" in r.description.lower() for r in explanation.reasons)


class TestAlternativesGeneration:
    """Tests for generating alternatives."""

    def test_alternatives_for_leaf(self) -> None:
        """Test alternatives for removing leaf package."""
        graph = DependencyGraph()
        leaf = Entity(id=uuid4(), type="package", name="leaf")
        graph = graph.add_entity(leaf)

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        alts = explainer.generate_dependency_alternatives(leaf.id)

        assert len(alts.alternatives) > 0
        # Should have direct removal alternative
        direct_removal = [a for a in alts.alternatives if "directly" in a.description.lower() or "no dependents" in a.description.lower()]
        assert len(direct_removal) > 0
        assert direct_removal[0].feasibility == 1.0

    def test_alternatives_for_hub(self) -> None:
        """Test alternatives for removing hub package."""
        graph = DependencyGraph()
        hub = Entity(id=uuid4(), type="package", name="hub")
        deps = [Entity(id=uuid4(), type="package", name=f"dep_{i}") for i in range(10)]

        graph = graph.add_entity(hub)
        for dep in deps:
            graph = graph.add_entity(dep).add_relation(
                Relation(id=uuid4(), type="depends_on", from_entity_id=dep.id, to_entity_id=hub.id)
            )

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        alts = explainer.generate_dependency_alternatives(hub.id)

        # Should have migration alternative
        migration = [a for a in alts.alternatives if "migrate" in a.description.lower()]
        assert len(migration) > 0

        # Should have gradual deprecation
        gradual = [a for a in alts.alternatives if "gradual" in a.description.lower()]
        assert len(gradual) > 0

        # Should have optional dependency
        optional = [a for a in alts.alternatives if "optional" in a.description.lower()]
        assert len(optional) > 0

    def test_alternatives_recommended(self) -> None:
        """Test that most feasible alternative is recommended."""
        graph = DependencyGraph()
        leaf = Entity(id=uuid4(), type="package", name="leaf")
        graph = graph.add_entity(leaf)

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        alts = explainer.generate_dependency_alternatives(leaf.id)

        assert alts.recommended is not None
        assert alts.recommended.is_feasible()
        # Should be the most feasible
        assert alts.recommended.feasibility == max(a.feasibility for a in alts.alternatives)

    def test_alternatives_has_feasible(self) -> None:
        """Test checking for feasible alternatives."""
        graph = DependencyGraph()
        leaf = Entity(id=uuid4(), type="package", name="leaf")
        graph = graph.add_entity(leaf)

        analyzer = DependencyImpactAnalyzer(graph)
        explainer = ExplanationGenerator(graph, analyzer)

        alts = explainer.generate_dependency_alternatives(leaf.id)

        assert alts.has_feasible_alternatives()

        feasible = alts.feasible_alternatives()
        assert len(feasible) > 0
        assert all(a.feasibility > 0.5 for a in feasible)
