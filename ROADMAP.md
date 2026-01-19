# TESSRYX ROADMAP
**Strategic Timeline & Milestones**

---

## Timeline Overview

```
Phase 0: Specification    [Weeks 1-4]     ████░░░░░░░░░░░░░░░░
Phase 1: Core Kernel      [Months 1-3]    ░░░░████████░░░░░░░░
Phase 2: Solver + Scale   [Months 4-6]    ░░░░░░░░░░░░████████
Phase 3: Versioning       [Months 7-8]    ░░░░░░░░░░░░░░░░████
Phase 4: API + Storage    [Months 9-10]   ░░░░░░░░░░░░░░░░░░██
Phase 5: Domain Pack      [Months 11-12]  ░░░░░░░░░░░░░░░░░░░█
```

---

## Phase 0: The Constitution (Weeks 1-4) [CURRENT]

**Objective:** Complete TessIR v1.0 specification + canonical test suite

### Week 1: Constraint Taxonomy
- [ ] Complete 20-30 core constraint type definitions
  - Temporal: Precedence, TimeWindow, Duration
  - Resource: Capacity, Allocation, Sharing
  - Logical: Mutex, Choice, Conditional
  - Structural: Hierarchy, Composition, Encapsulation
- [ ] Define constraint priority system (Hard, Soft, Preference)
- [ ] Write 5 complete constraint examples

**Steals Applied:**
- S02: Study EOS Dependency Impact Analyzer algorithms
- S11: Port Gregore's test framework structure

### Week 2: Operations & Provenance
- [ ] Define all GraphOps operations (SCC, topo sort, reachability, blast radius)
- [ ] Define all PlanOps operations (solve, validate, explain, optimize)
- [ ] Define all ExplainOps operations (why, why-not, alternatives)
- [ ] Complete provenance model specification
- [ ] Complete confidence score propagation algorithm

**Steals Applied:**
- S01: Reference Consensus provenance schema design

### Week 3: Versioning & Domain Packs
- [ ] Complete version control model (commit, branch, merge, diff)
- [ ] Define Domain Pack structure and interface
- [ ] Write serialization format specification
- [ ] Complete conformance requirements

### Week 4: Test Suite & ADRs
- [ ] Create 10 software development test scenarios
- [ ] Create 10 IT operations test scenarios
- [ ] Create 10 automotive test scenarios
- [ ] Create 10 construction/AEC test scenarios
- [ ] Create 10 adversarial test scenarios
- [ ] Write ADR-001 through ADR-005
- [ ] Set up GitHub remote + push all commits

**Deliverables:**
- TessIR v1.0 specification (complete, peer-reviewed)
- 50 canonical test scenarios with expected outputs
- 5 Architecture Decision Records
- Public GitHub repository

**Success Criteria:**
- Specification is unambiguous (can implement without questions)
- Test scenarios cover 80% of real-world use cases
- Community feedback incorporated
- Ready to begin Phase 1 implementation

---

## Phase 1: The Kernel (Months 1-3)

**Objective:** Implement core TessIR + GraphOps + basic ExplainOps

### Month 1: TessIR Implementation + Provenance
**Goals:**
- Set up Python project structure
- Implement TessIR core primitives
- Implement provenance ledger
- Unit tests for all primitives

**Key Tasks:**
- [ ] Python 3.12+ virtual environment
- [ ] Dependencies: NetworkX, Pydantic, Pytest
- [ ] `tessryx_core/tessir/` - Entity, Relation, Constraint classes
- [ ] `tessryx_core/provenance/` - **Port S01 from Consensus**
  - Ledger implementation
  - Confidence scoring (G-Score)
  - Validation history
- [ ] `tessryx_core/tessir/validator.py` - **Port S06 from EOS**
  - Character forensics
  - Input sanitization
- [ ] Unit tests (Pytest)
- [ ] Type checking (mypy --strict)

**Steals Applied:**
- **S01:** Provenance Ledger (Consensus) - Direct port
- **S06:** Character Forensics (EOS) - Port for input validation

**Deliverables:**
- Working TessIR implementation
- Provenance system with confidence scoring
- 100% test coverage for core primitives
- Zero type errors (mypy --strict)

### Month 2: GraphOps + Dependency Impact
**Goals:**
- Implement graph algorithm primitives
- Port dependency impact analysis
- Integration tests with NetworkX

**Key Tasks:**
- [ ] `tessryx_core/kernel/graph_ops/` module
  - SCC detection (Tarjan's algorithm)
  - Topological sorting
  - Reachability queries
  - **Port S02 from EOS: Impact Analyzer**
    - Blast radius calculation
    - Circular dependency detection
    - Critical path identification
- [ ] Integration with NetworkX
- [ ] Property-based tests (Hypothesis)
- [ ] Performance benchmarking

**Steals Applied:**
- **S02:** Dependency Impact Analyzer (EOS) - Port algorithms

**Deliverables:**
- Complete GraphOps module
- Dependency impact analysis working
- Benchmark suite showing performance

### Month 3: ExplainOps Scaffolding
**Goals:**
- Build explanation engine foundation
- Human-readable output generation
- Test against canonical suite

**Key Tasks:**
- [ ] `tessryx_core/kernel/explain_ops/` module
  - Explanation templates
  - Output formatters (text, JSON, HTML)
  - Why/Why-not logic (basic)
- [ ] Run canonical suite (software dev scenarios)
- [ ] Validate against expected outputs
- [ ] Refine explanations based on results

**Deliverables:**
- Basic explanation engine
- All software dev test scenarios passing
- Explainable outputs for every operation

**Phase 1 Exit Criteria:**
- [ ] TessIR fully implemented
- [ ] GraphOps complete and tested
- [ ] Provenance system working
- [ ] 10/50 test scenarios passing (software dev)
- [ ] Zero type errors, zero lint errors
- [ ] Ready for solver integration

---

## Phase 2: Solver Integration + Orchestration (Months 4-6)

**Objective:** Integrate OR-Tools + Z3, parallel execution, multi-solver orchestration

### Month 4: OR-Tools Integration + Cache
**Goals:**
- Integrate OR-Tools CP-SAT solver
- Constraint translation layer
- Incremental caching

**Key Tasks:**
- [ ] `tessryx_core/kernel/plan_ops/` module
  - Constraint → OR-Tools translation
  - Solver invocation
  - Solution extraction
- [ ] **Port S07 from EOS: Incremental Cache**
  - Hash-based caching
  - Invalidation logic
- [ ] Test with resource allocation scenarios
- [ ] Benchmark solver performance

**Steals Applied:**
- **S07:** Incremental Scan Cache (EOS)

**Deliverables:**
- OR-Tools solving basic constraints
- Cached results for unchanged sets
- 20/50 test scenarios passing

### Month 5: Z3 Integration + Multi-Solver Orchestration
**Goals:**
- Integrate Z3 SMT solver
- Multi-solver orchestration
- Parallel execution infrastructure

**Key Tasks:**
- [ ] Z3 integration for logical constraints
- [ ] **Port S03 from Consensus: Multi-Solver Orchestration**
  - Cascade pattern (cheap → expensive)
  - Tribunal pattern (parallel voting)
  - Ensemble synthesis
- [ ] **Port S04 from Gregore: BullMQ Parallel Execution**
  - Or use Celery (Python equivalent)
  - Worker pool management
  - Progress tracking
- [ ] **Port S05 from Gregore: Session Checkpoints**
  - For long-running solves (>1 min)
- [ ] **Port S13 from Gregore: Greg Gate (G-Score)**
  - Confidence communication to users
- [ ] **Port S15 from EOS: Pattern Recognition**
  - Circular constraint detection
  - Anti-pattern identification
- [ ] Cross-cutting patterns:
  - **S21:** Homeostasis (adaptive solver strategy)
  - **S23:** Diversity Preserver (multiple solver strategies)

**Steals Applied:**
- **S03:** Multi-Solver Orchestration (Consensus)
- **S04:** BullMQ Parallel Execution (Gregore)
- **S05:** Session Checkpoints (Gregore)
- **S13:** Greg Gate (Gregore)
- **S15:** Pattern Recognition (EOS)
- **S21:** Homeostasis (Gregore)
- **S23:** Diversity Preserver (Consensus)

**Deliverables:**
- OR-Tools + Z3 coordinated solving
- Parallel execution working (3-5x speedup)
- Checkpoint recovery tested
- 35/50 test scenarios passing

### Month 6: Advanced Explanation + Pattern Detection
**Goals:**
- Enhanced explanation engine
- Minimal unsat core
- Recommendation system

**Key Tasks:**
- [ ] Minimal unsat core extraction (from Z3)
- [ ] Relaxation suggestions
- [ ] Alternative plan generation (top 3)
- [ ] Pattern recognition for anti-patterns
- [ ] Enhanced human-readable proofs

**Deliverables:**
- Explainable failures with fix suggestions
- Alternative plans when multiple solutions exist
- 45/50 test scenarios passing

**Phase 2 Exit Criteria:**
- [ ] OR-Tools + Z3 integrated and coordinated
- [ ] Parallel execution scaling on multi-core
- [ ] Pattern recognition catching anti-patterns
- [ ] Explanations include "how to fix"
- [ ] 45/50 canonical scenarios passing
- [ ] Ready for versioning layer

---

## Phase 3: Versioning + Diff Engine (Months 7-8)

**Objective:** Git-like operations, blast radius, change impact

### Month 7: Version Control + Trust Tiers (Design)
**Goals:**
- Implement commit/branch/merge
- Diff calculation
- Trust tier system design

**Key Tasks:**
- [ ] `tessryx_core/versioning/` module
  - Commit creation
  - Branch management
  - Tag support
- [ ] Diff engine (structural + semantic)
- [ ] Lockfile generation
- [ ] **S08 Design:** Trust Tier System
  - T0-T5 progressive unlocking
  - Feature gating logic
  - Scoring algorithm
- [ ] **S22:** State Classification Engine
  - Detect user intent (building, exploring, debugging)
  - Adaptive behavior

**Steals Applied:**
- **S08:** Trust Tier System design (Gregore)
- **S14:** The Ghost (Consensus/Gregore) - optional
- **S22:** State Classification (Consensus)

**Deliverables:**
- Version control working (commit, branch, diff)
- Lockfiles generated and comparable
- Trust tier system designed (not implemented yet)
- 48/50 test scenarios passing

### Month 8: Blast Radius + Change Impact
**Goals:**
- Impact assessment on version changes
- Cost/time/risk quantification
- Adversarial scenarios

**Key Tasks:**
- [ ] Blast radius calculation on diffs
- [ ] Impact metrics (entities affected, constraints violated)
- [ ] Risk scoring for proposed changes
- [ ] Test adversarial scenarios (remaining scenarios)

**Deliverables:**
- Change impact analysis working
- "What breaks if X changes?" answered
- All 50/50 canonical scenarios passing

**Phase 3 Exit Criteria:**
- [ ] Git-like operations working
- [ ] Diff engine calculating structural + semantic changes
- [ ] Blast radius accurately predicting impact
- [ ] All 50 test scenarios passing
- [ ] Ready for API layer

---

## Phase 4: API + Persistence (Months 9-10)

**Objective:** FastAPI, PostgreSQL, SDK

### Month 9: Database Schema + Migrations
**Goals:**
- PostgreSQL schema implementation
- Migration system
- Data persistence

**Key Tasks:**
- [ ] **Port S18 from Consensus: PostgreSQL Schema**
  - Entities, Relations, Constraints tables
  - Provenance, Commits tables
  - Optimized indexes
- [ ] Alembic migration system
- [ ] CRUD operations for all primitives
- [ ] Backup and restore utilities

**Steals Applied:**
- **S18:** PostgreSQL + pgvector Schema (Consensus)

**Deliverables:**
- Complete database schema
- Migration system working
- All data persisted reliably

### Month 10: FastAPI + SDK + Trust Tier Implementation
**Goals:**
- REST API implementation
- Python SDK
- Trust tier feature gating

**Key Tasks:**
- [ ] `tessryx_api/` module (FastAPI)
  - POST /graphs, /constraints, /solve, /validate
  - GET /diff/{from}/{to}
  - WebSocket for progress (optional)
- [ ] Python SDK (`tessryx` package)
  - Client library
  - Authentication
  - Examples
- [ ] **S08 Implementation:** Trust Tier System
  - Feature gates active
  - T0-T5 unlocking
- [ ] **S16:** Dependency Visualizer (if time)
  - Basic graph rendering
- [ ] **S19:** WebSocket Infrastructure (if needed)
  - Real-time solver progress
- [ ] **S20:** Token Economy (if monetizing)
  - Cost tracking

**Steals Applied:**
- **S08:** Trust Tier implementation (Gregore)
- **S16:** Dependency Visualizer (EOS) - optional
- **S19:** WebSocket (Consensus) - optional
- **S20:** Token Economy (Gregore) - optional

**Deliverables:**
- REST API working (all endpoints)
- Python SDK published
- Trust tiers gating features
- API documentation complete

**Phase 4 Exit Criteria:**
- [ ] API fully functional and documented
- [ ] SDK working with examples
- [ ] Database persisting all state
- [ ] Trust tiers driving feature access
- [ ] Ready for domain-specific work

---

## Phase 5: Software Dev Domain Pack (Months 11-12)

**Objective:** First domain-specific implementation

### Month 11: Package Manager Adapters
**Goals:**
- npm, pip, Maven importers
- Dependency graph construction
- Constraint generation from lock files

**Key Tasks:**
- [ ] `tessryx_packs/software_dev/` module
  - npm package.json → TessIR
  - pip requirements.txt → TessIR
  - Maven pom.xml → TessIR
- [ ] Constraint template library
  - Version conflicts
  - Security vulnerabilities
  - Breaking changes
- [ ] Validated dependency library (curated)
- [ ] Import/export adapters

**Deliverables:**
- Software Dev Domain Pack working
- npm/pip/Maven graphs importable
- Constraints auto-generated

### Month 12: GitHub Action + CLI + Launch
**Goals:**
- CI/CD integration
- Command-line tool
- Public launch

**Key Tasks:**
- [ ] GitHub Action for dependency validation
- [ ] CLI tool (`tessryx-cli`)
  - `tessryx validate package.json`
  - `tessryx impact --from v1 --to v2`
  - `tessryx lockfile generate`
- [ ] Documentation site
- [ ] Example projects
- [ ] Public announcement
- [ ] Community feedback loop

**Deliverables:**
- GitHub Action published
- CLI tool released
- Documentation complete
- Public launch 🚀

**Phase 5 Exit Criteria:**
- [ ] Software Dev Domain Pack production-ready
- [ ] GitHub Action used by beta testers
- [ ] CLI tool working with examples
- [ ] Positive community feedback
- [ ] Revenue model validated (freemium)

---

## V2 Transition (Year 2)

**When:** After 6-12 months of V1 production use

**Goals:**
- Rewrite kernel in Rust (performance)
- Migrate to hybrid database (Postgres + Neo4j)
- gRPC API (internal), GraphQL (external)
- Expand to IT Operations wedge

**Key Decisions:**
- Port only proven patterns
- Maintain Python bindings (PyO3)
- Keep TessIR spec stable (v1.0)
- Backward compatibility mandatory

---

## Steal Integration Timeline

### Phase 0 (NOW):
- S02 (study), S09, S10, S11, S12

### Phase 1 (Months 1-3):
- S01, S02 (implement), S06

### Phase 2 (Months 4-6):
- S03, S04, S05, S07, S13, S15, S21, S23

### Phase 3 (Months 7-8):
- S08 (design), S14, S22

### Phase 4 (Months 9-10):
- S08 (implement), S16, S18, S19, S20

### Phase 5+ (Months 11-12+):
- S17 (if desktop)

---

## Key Milestones

| Milestone | Target Date | Success Metric |
|-----------|-------------|----------------|
| TessIR Spec Complete | Week 4 | Peer-reviewed, unambiguous |
| Core Kernel Working | Month 3 | 10/50 tests passing |
| Solvers Integrated | Month 6 | 45/50 tests passing |
| Versioning Working | Month 8 | All 50 tests passing |
| API Released | Month 10 | Public SDK available |
| Domain Pack Shipped | Month 12 | GitHub Action in use |
| V2 Kernel | Year 2 | Rust performance gains |

---

## Dependencies & Risks

### Critical Path:
```
TessIR Spec → Core Implementation → Solver Integration → API → Domain Pack
```

### Risks:

**Phase 0 Risks:**
- TessIR spec too complex (Mitigation: Time-box to 4 weeks, iterate)
- Canonical tests insufficient (Mitigation: 50 scenarios covers 80% use cases)

**Phase 1 Risks:**
- Provenance model too heavyweight (Mitigation: Port proven Consensus design)
- NetworkX performance issues (Mitigation: Profile early, optimize or rewrite)

**Phase 2 Risks:**
- OR-Tools + Z3 integration complex (Mitigation: Use proven orchestration patterns)
- Parallel execution overhead (Mitigation: Benchmark, tune worker pool)

**Phase 3 Risks:**
- Diff calculation expensive (Mitigation: Incremental algorithms, caching)

**Phase 4 Risks:**
- API design wrong (Mitigation: Follow REST best practices, iterate)
- Database schema brittle (Mitigation: Alembic migrations, test thoroughly)

**Phase 5 Risks:**
- Domain Pack adoption slow (Mitigation: Solve acute pain, GitHub Action integration)

---

## Success Criteria (Overall)

**Technical:**
- [ ] All 50 canonical scenarios passing
- [ ] API <500ms p95 latency
- [ ] 10K node graphs solvable in <30 seconds
- [ ] Zero technical debt (no TODOs, mocks, stubs)

**Product:**
- [ ] 100+ GitHub stars (community interest)
- [ ] 10+ beta users (validation)
- [ ] 3+ contributed Domain Packs (ecosystem)
- [ ] Positive HN/Reddit feedback (reputation)

**Business:**
- [ ] Freemium model validated (T0→T5 conversion)
- [ ] 1+ enterprise pilot (revenue potential)
- [ ] Clear path to $1M ARR (Year 2 goal)

---

## Version History

- **v1.0.0** (2026-01-19): Initial roadmap with steal integration timeline

---

**Last Updated:** 2026-01-19  
**Next Review:** End of Phase 0 (update with actual progress)
