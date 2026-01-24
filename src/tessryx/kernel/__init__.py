"""TESSRYX Kernel - Core execution engine.

The kernel implements the core algorithms and services that power TESSRYX:

- Graph operations (SCC, topological sort, reachability, impact analysis)
- Provenance ledger (confidence scoring, conflict detection, validation)
- Input validation (character forensics, injection prevention)
- Dependency impact analysis (blast radius, critical path, risk assessment)
- Query engine (natural language dependency queries)
- Explanation generator (why, why-not, alternatives)
- Plan operations (constraint solving, optimization) - coming soon

Phase 1 Month 1 Deliverables:
- Provenance Ledger (S01 from Consensus) ✅
- Input Validator (S06 from Eye-of-Sauron) ✅

Phase 1 Month 2 Deliverables:
- Graph Operations (SCC, topological sort, reachability) ✅
- Dependency Impact Analyzer (S02 from Eye-of-Sauron) ✅

Phase 1 Month 3 Deliverables:
- Query Engine (natural language queries) ✅
- Explanation Generator (why/why-not/alternatives) ✅
- Property-based testing (Hypothesis) ✅
- Performance benchmarks (pytest-benchmark) ✅
"""

from tessryx.kernel.explanation_generator import (
    Alternative,
    AlternativesExplanation,
    ConfidenceLevel,
    Explanation,
    ExplanationGenerator,
    ExplanationType,
    Reason,
)
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
from tessryx.kernel.impact_analyzer import (
    ChangeImpactAnalysis,
    CriticalPath,
    DependencyImpactAnalyzer,
    ImpactMetrics,
    ImpactSeverity,
)
from tessryx.kernel.provenance_ledger import ProvenanceLedger
from tessryx.kernel.query_engine import (
    QueryEngine,
    QueryResult,
    QueryType,
)
from tessryx.kernel.validator import (
    InputValidator,
    ValidationLevel,
    ValidationResult,
    ValidationViolation,
)

__all__ = [
    # Graph Operations
    "DependencyGraph",
    "find_strongly_connected_components",
    "find_circular_dependencies",
    "topological_sort",
    "CycleDetectedError",
    "is_reachable",
    "find_path",
    "find_all_paths",
    "get_transitive_dependencies",
    "get_transitive_dependents",
    # Impact Analysis
    "DependencyImpactAnalyzer",
    "ImpactMetrics",
    "ImpactSeverity",
    "CriticalPath",
    "ChangeImpactAnalysis",
    # Query Engine
    "QueryEngine",
    "QueryResult",
    "QueryType",
    # Explanation Generator
    "ExplanationGenerator",
    "Explanation",
    "ExplanationType",
    "Reason",
    "Alternative",
    "AlternativesExplanation",
    "ConfidenceLevel",
    # Provenance
    "ProvenanceLedger",
    # Validation
    "InputValidator",
    "ValidationLevel",
    "ValidationResult",
    "ValidationViolation",
]
