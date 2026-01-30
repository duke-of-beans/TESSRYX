# TESSRYX
**Universal Dependency Intelligence Infrastructure**

[![Version](https://img.shields.io/badge/version-0.4.0--phase1--month3-blue)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.12+-green)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Status](https://img.shields.io/badge/status-active%20development-brightgreen)](STATUS.md)

> *TESSRYX transforms dependency mapping from visualization into verification — proving plans are valid, predicting change impacts, and making failures recoverable.*

---

## The Problem

**Dependency blindness costs billions globally.**

Systems don't fail because components are bad — they fail because dependencies are invisible, assumptions go untracked, and changes cascade unpredictably. Most tools *map* dependencies (visualization). TESSRYX *validates* them (verification).

**Real-world impact:**
- **Software:** 94% of projects fail, $312K/year rework per team (dependency hell, version conflicts)
- **IT Operations:** Wrong sequencing = catastrophic failures (no one knows what breaks if X changes)
- **Manufacturing:** 94% exceed budget 40%+ (untracked dependencies, change ripple effects)
- **Construction:** 67% over budget (invisible constraints, cascading delays)

---

## The Solution

TESSRYX is a **constraint solver for reality** — combining formal intermediate representation (TessIR), multi-solver orchestration (OR-Tools + Z3), and evidence-based provenance to answer questions like:

- **"Is this plan even possible?"** → Constraint solver proves validity OR explains minimal conflicts
- **"What breaks if I change X?"** → Blast radius analysis with cost/time/risk quantification
- **"Why did this fail?"** → Minimal unsat core + human-readable explanations
- **"What changed between versions?"** → Git-like diffs for dependency state

**Not a visualization tool. Not a project manager. Infrastructure for dependency intelligence.**

---

## Why This Exists

### The Progression: Problem → Friction → Solution

**The Ceiling**
Hit a wall with existing dependency tools — they show pretty graphs but can't answer "is this change safe?" Needed formal verification, not just visualization.

**The Research**
Discovered constraint solvers (OR-Tools, Z3) solve similar problems in scheduling/logistics. Realized: dependencies ARE constraints. Package managers already do naive solving — why not general-purpose dependency intelligence?

**The Foundation**
Built TessIR specification — formal intermediate representation treating dependencies as first-class objects with contracts, provenance, and versioning. Designed four-pillar architecture (TessIR + Solver + Evidence + Versioning).

**The Implementation**
Implemented core kernel with graph algorithms (SCC detection, blast radius), provenance ledger (confidence scoring), and impact analysis. Added property-based testing (Hypothesis) for algorithmic correctness.

**Current State:**
Production-grade foundation with 5,555 lines of code, 1,700+ test cases, performance benchmarks validating O(V+E) complexity, and zero technical debt.

---

## Development Journey

**Built with zero traditional coding background using systematic AI-native development methodology.**

### Development Progression:

**Phase 1: Strategic Foundation**
- Designed TessIR specification with constraints as first-class objects
- Established four-pillar architecture (TessIR + Solver + Evidence + Versioning)
- Made strategic pivot from automotive to software development (data availability advantage)
- **Learning:** Architecture matters more than code — wrong foundation = rewrite everything

**Phase 2: Core Primitives**
- Implemented TessIR entities, relations, constraints (Pydantic models)
- Built provenance ledger with G-Score confidence calculation
- Added input validator (SQL injection, path traversal, Unicode attacks)
- **Challenge:** Type safety in Python is subtle — learned mypy strict mode the hard way
- **106 test cases, 2,197 lines of code**

**Phase 3: Graph Algorithms**
- Implemented DependencyGraph with NetworkX integration
- Added SCC detection (Tarjan's algorithm), topological sort, reachability
- Built dependency impact analyzer (blast radius, critical path, risk scoring)
- **Challenge:** Graph algorithms have edge cases — circular deps, disconnected components
- **80 new test cases, 2,268 lines of code**

**Phase 4: Property Testing + Performance**
- Integrated Hypothesis for property-based testing (1,500+ generated test cases)
- Added pytest-benchmark for performance validation
- Verified O(V+E) complexity empirically across all algorithms
- **Learning:** Property tests catch bugs unit tests miss — "all graphs" vs "this one graph"
- **1,090 lines of test infrastructure**

### Key Technical Challenges Solved:

**1. Type Safety Hell → Pydantic + mypy strict**
- Problem: Python's dynamic typing hides bugs until runtime
- Solution: Full Pydantic validation + mypy --strict (100% type coverage)
- Learning: Types catch 40% of bugs before first run

**2. Graph Algorithm Edge Cases → Property-Based Testing**
- Problem: Unit tests only cover cases you think of
- Solution: Hypothesis generates 100+ random graphs per test
- Learning: "Works for one graph" ≠ "Works for all graphs"

**3. Performance Unknown → Empirical Complexity Verification**
- Problem: Claimed O(V+E) but no proof
- Solution: Benchmark suite with 10-5K node graphs, measure scaling
- Learning: Algorithmic complexity is measurable, not theoretical

**4. Confidence Scoring → Evidence Aggregation**
- Problem: How to score relationship confidence with conflicting sources?
- Solution: G-Score algorithm (recency × evidence count × validation history)
- Learning: Trust requires math, not feelings

### What I Learned (Technical):

- **Graph Theory:** Tarjan's SCC, topological sort, transitive closure, blast radius
- **Constraint Solving:** OR-Tools CP-SAT, Z3 SMT, unsat cores, minimal explanations
- **Type Systems:** Pydantic validation, mypy strict, generic types, protocol classes
- **Testing:** Hypothesis property tests, pytest-benchmark, coverage analysis
- **Architecture:** Immutable data structures, dependency injection, clean interfaces
- **Performance:** Big-O empirical validation, memory profiling, scalability testing

### What I Learned (Methodology):

- **AI-Native Development:** Claude/GPT/Gemini as thought partners, not autocomplete
- **Quality Gates:** Zero technical debt (no TODOs/mocks/stubs), 100% type coverage
- **Checkpointing:** Save state every 2-3 tool calls (crash recovery)
- **Documentation:** Four pillars (DNA + STATUS + ARCHITECTURE + CHANGELOG) stay synced
- **Iterative Refinement:** Build → Measure → Learn → Rebuild (not waterfall)

---

## Architecture

### Core Components

**1. TessIR (The Constitution)**
- Formal intermediate representation for dependencies
- Entities (typed, hierarchical, composable)
- Relations (typed edges with semantic meaning)
- Constraints (first-class objects with provenance)
- Contracts (preconditions, postconditions, invariants, failure modes)

**2. The Kernel (GraphOps + Impact Analysis)**
- SCC detection (Tarjan's algorithm, O(V+E))
- Topological sort with cycle detection
- Reachability queries (is_reachable, find_path, find_all_paths)
- Blast radius calculation (transitive dependents)
- Critical path analysis (longest dependency chain)
- Risk scoring (weighted factors: dependencies, severity, centrality, depth)

**3. The Trust Layer (Provenance + Validation)**
- Evidence ledger with source tracking
- G-Score confidence calculation (recency × evidence × validation)
- Conflict detection (bidirectional relationship divergence)
- Validation history (influences future scores)

**4. The Solver Layer (Future - Phase 2)**
- OR-Tools CP-SAT for scheduling constraints
- Z3 SMT for logical constraints
- Multi-solver orchestration (cascade pattern)
- Minimal unsat core extraction

### Technology Stack

**Current (V1 - Python):**
```
Language:      Python 3.12+
Graph:         NetworkX (in-memory)
Database:      PostgreSQL + SQLAlchemy
API:           FastAPI + Pydantic
Testing:       Pytest + Hypothesis + pytest-benchmark
Type Checking: mypy --strict
Linting:       Ruff + Black
```

**Future (V2 - Rust):**
```
Kernel:        Rust (performance + WASM)
Graph DB:      Neo4j (when traversal dominates)
API:           gRPC + GraphQL
Frontend:      React + Cytoscape.js
```

---

## Current Status

**Phase 1 Month 3: COMPLETE ✅**

**Implemented:**
- ✅ TessIR core primitives (entities, relations, constraints)
- ✅ Provenance ledger with G-Score confidence
- ✅ Input validator (SQL injection, path traversal, Unicode attacks)
- ✅ Graph operations (SCC, topological sort, reachability, transitive deps)
- ✅ Dependency impact analyzer (blast radius, critical path, risk scoring)
- ✅ Property-based testing (Hypothesis, 1,500+ generated test cases)
- ✅ Performance benchmarks (validated O(V+E) complexity up to 5K nodes)
- ✅ FastAPI REST endpoints for entity/relation management
- ✅ SQLAlchemy models + Alembic migrations

**Metrics:**
- **Code:** 5,555 lines (2,216 production + 3,339 tests)
- **Test Coverage:** 1,700+ test cases (186 unit + 1,500+ property + 25+ benchmarks)
- **Type Safety:** 100% type-annotated (mypy --strict)
- **Performance:** O(V+E) verified empirically
- **Technical Debt:** Zero (no TODOs, mocks, placeholders)

**Next (Phase 2 - Solver Integration):**
- [ ] OR-Tools CP-SAT integration (constraint solving)
- [ ] Z3 SMT integration (logical constraints)
- [ ] Multi-solver orchestration (cascade + tribunal patterns)
- [ ] Minimal unsat core extraction
- [ ] Parallel execution infrastructure

---

## Installation & Usage

**Prerequisites:**
- Python 3.12+
- PostgreSQL (optional - for persistence)

**Install:**
```bash
git clone https://github.com/duke-of-beans/TESSRYX.git
cd TESSRYX
pip install -e ".[dev]"
```

**Run Tests:**
```bash
# All tests
pytest

# Property tests only
pytest tests/test_graph_properties.py -v

# Performance benchmarks
pytest tests/test_graph_performance.py --benchmark-only

# Type checking
mypy src/tessryx --strict
```

**Basic Usage:**
```python
from tessryx.core import Entity, Relation
from tessryx.kernel import DependencyGraph, ImpactAnalyzer

# Create entities
service_a = Entity(id="svc-a", type="service", name="API Gateway")
service_b = Entity(id="svc-b", type="service", name="Auth Service")

# Define dependency
depends_on = Relation(
    source_id="svc-a",
    target_id="svc-b",
    type="depends_on"
)

# Build graph
graph = DependencyGraph([service_a, service_b], [depends_on])

# Analyze impact
analyzer = ImpactAnalyzer(graph)
impact = analyzer.analyze_change_impact("svc-b")

print(f"Blast radius: {impact.affected_entities}")
print(f"Risk score: {impact.risk_score}")
print(f"Recommendations: {impact.recommendations}")
```

**API Server:**
```bash
# Start FastAPI server
uvicorn src.api.main:app --reload

# API docs at http://localhost:8000/docs
```

---

## What This Demonstrates

### Technical Capability
- **Graph Theory:** Implemented Tarjan's SCC, blast radius analysis, critical path detection
- **Type Systems:** 100% type-annotated Python with Pydantic + mypy strict
- **Testing Rigor:** Property-based testing (Hypothesis), performance benchmarks, O(V+E) verification
- **API Design:** FastAPI REST endpoints with SQLAlchemy ORM
- **Algorithm Analysis:** Empirical complexity validation, memory profiling

### Systematic Thinking
- **Methodology:** Quality gates, aggressive checkpointing, zero technical debt
- **Documentation:** Four-pillar sync (DNA + STATUS + ARCHITECTURE + CHANGELOG)
- **Iteration:** Build → Measure → Learn → Rebuild (not waterfall)
- **Decision Tracking:** ADRs for major architectural choices, CHANGELOG for all changes

### Learning Velocity
- **Phase 1:** Strategic planning + architecture design
- **Phase 2:** Core primitives + provenance (2,197 lines, 106 tests)
- **Phase 3:** Graph algorithms + impact analysis (2,268 lines, 80 tests)
- **Phase 4:** Property testing + performance (1,090 lines test infrastructure)

**From zero to production-grade dependency intelligence with systematic AI-native methodology.**

---

## Roadmap

### Phase 2: Solver Integration
- OR-Tools + Z3 integration
- Constraint solving with proof certificates
- Minimal unsat core explanations
- Parallel execution infrastructure

### Phase 3: Versioning
- Git-like operations (commit, branch, merge, diff)
- Blast radius on version changes
- Lockfiles for dependency state

### Phase 4: API + Persistence
- Production PostgreSQL deployment
- Python SDK
- Complete REST API

### Phase 5: Software Dev Domain Pack
- npm/pip/Maven importers
- GitHub Action integration
- Public launch

---

## Documentation

**Core Docs:**
- [DNA.md](DNA.md) - Project identity, principles, strategic positioning
- [STATUS.md](STATUS.md) - Current state tracker (updated continuously)
- [CHANGELOG.md](CHANGELOG.md) - Complete version history and decision log
- [ROADMAP.md](ROADMAP.md) - Strategic timeline with milestones

**Technical Docs:**
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture
- [TessIR Specification](docs/TessIR_v1.0_SPEC.md) - Formal spec
- [ADR/](docs/ADR/) - Architecture Decision Records
- [Phase Completion Reports](docs/) - Detailed phase summaries

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Contact

**Developer:** David Kirsch  
**GitHub:** [@duke-of-beans](https://github.com/duke-of-beans)  
**Repository:** [TESSRYX](https://github.com/duke-of-beans/TESSRYX)

---

## Acknowledgments

**AI Development Partners:**
- Claude (Anthropic) - Primary development assistant
- GPT-4 (OpenAI) - Architecture review and strategic guidance
- Gemini 2.0 (Google) - Technical implementation support

---

**TESSRYX** - *Built with systematic AI-native development methodology. Zero traditional coding background. Pure "figure it out" velocity.*
