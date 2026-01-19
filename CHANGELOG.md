# TESSRYX CHANGELOG
**Version History & Major Decisions**

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Phase 0: The Constitution (Weeks 1-4)
- TessIR v1.0 specification
- Canonical test suite (50 scenarios)
- Architecture Decision Records (ADR-001 through ADR-005)

---

## [0.1.0-genesis] - 2026-01-19

### Added
- **Project Foundation**
  - DNA.md: Project identity, core principles, strategic positioning
  - STATUS.md: Current state tracker
  - CHANGELOG.md: This file
  - SESSION_LOG.md: Detailed session tracking
  - .gitignore: Git ignore patterns
  - README.md: Public-facing documentation
  
- **Documentation Structure**
  - docs/ directory created
  - docs/ARCHITECTURE.md: Technical architecture overview
  - docs/ADR/ directory: Architecture Decision Records
  - docs/TessIR_v1.0_SPEC.md: Core specification (outline)

- **Genius Council Artifacts**
  - GENIUS_COUNCIL_PROMPT.md: Initial review request
  - GCsynth1 - Genius Council Synthesis.md: Round 1 synthesis
  - GCsynth1.5 - Claude Semi-Final Synthesis.md: Round 2 prompt
  - GCsynth2 - Genius Council Synthesis.md: Final synthesis

### Changed
- **Strategic Pivot: Software Development Wedge**
  - Original plan: Automotive as initial wedge
  - Rationale: Data acquisition nightmare (180K relationships manual mapping)
  - New plan: Software Development wedge (data already exists in package managers)
  - Key insight: "Data already exists" > "Unfair advantage"
  - Impact: Faster validation (days vs months), lower cost, technical buyers

### Decided
- **ADR-001 (Implicit):** Python for V1, Rust for V2
  - Rationale: Fast iteration, mature ecosystem, AI-assisted development
  - Alternative considered: Rust from day one
  - Decision: Pragmatic path (Python) → Production path (Rust)

- **ADR-002 (Implicit):** Postgres first, Neo4j maybe later
  - Rationale: Defer database decision until query patterns clear
  - Alternative considered: Neo4j native graph from day one
  - Decision: Hybrid approach (Postgres + NetworkX, measure, migrate if needed)

- **ADR-003 (Implicit):** Open TessIR Specification
  - Rationale: Establish as standard, enable ecosystem, reduce lock-in fear
  - Alternative considered: Proprietary schema
  - Decision: Open core (TessIR) + Paid features (Domain Packs, Enterprise)

- **ADR-004 (Implicit):** Software Development Wedge
  - Rationale: Data immediately available, fast validation, massive market
  - Alternative considered: Automotive, ERP/Manufacturing, IT Operations
  - Decision: Software Dev (Phase 1) → IT Ops (Phase 2) → ERP (Phase 3)

- **ADR-005 (Implicit):** Constraint Solver Strategy
  - Rationale: Use proven solvers (OR-Tools, Z3), don't build custom
  - Alternative considered: Custom constraint solver
  - Decision: Multi-solver orchestration (CP-SAT for scheduling, Z3 for logic)

### Context
This genesis release marks the completion of strategic planning via Genius Council reviews (GPT + Gemini, 2 rounds each). Core architecture validated by 3 independent AI councils with unanimous convergence on:
1. TessIR as formal intermediate representation
2. Constraints as first-class objects
3. Provenance + evidence ledger (trust infrastructure)
4. Versioning + diffs (change-impact prediction)
5. Proof-carrying plans (formal verification)

Project positioned as "AWS of Dependency Intelligence" - open-standard infrastructure layer, not domain-specific application.

---

## Version Naming Convention

**Format:** MAJOR.MINOR.PATCH-LABEL

- **MAJOR:** Breaking changes to TessIR specification or public APIs
- **MINOR:** New features, backward-compatible
- **PATCH:** Bug fixes, documentation updates
- **LABEL:** 
  - `genesis` - Initial foundation
  - `alpha` - Pre-release, unstable
  - `beta` - Feature-complete, testing
  - `rc` - Release candidate
  - (none) - Stable release

**Examples:**
- `0.1.0-genesis` - Initial project setup
- `0.2.0-alpha` - TessIR spec draft
- `1.0.0-beta` - TessIR v1.0 spec complete, implementation testing
- `1.0.0` - TessIR v1.0 stable, production-ready

---

## Decision Log (Chronological)

### 2026-01-19: Foundation Day
1. **Strategic Wedge Decision**
   - Context: Post-Genius Council synthesis
   - Decision: Software Development wedge (not Automotive)
   - Impact: Faster path to validation, lower data acquisition cost
   - Confidence: HIGH (unanimous council recommendation)

2. **Open Standard Decision**
   - Context: Genius Council recommendation (GPT explicit)
   - Decision: Publish TessIR as open standard
   - Impact: Ecosystem formation, reduced lock-in fear, establishes TESSRYX as "the standard"
   - Confidence: HIGH (strong business rationale)

3. **Technology Stack V1**
   - Context: Need for fast iteration, AI-assisted development
   - Decision: Python + NetworkX + OR-Tools + Postgres
   - Impact: Pragmatic, mature ecosystem, well-documented
   - Confidence: MEDIUM (will migrate to Rust V2, but path unclear)

4. **Database Strategy**
   - Context: GPT vs Gemini disagreement (Postgres vs Neo4j)
   - Decision: Postgres first, measure query patterns, migrate if needed
   - Impact: Defers expensive decision, allows evidence-based choice
   - Confidence: MEDIUM (migration path has risks)

5. **Constraint Design Philosophy**
   - Context: Genius Council consensus
   - Decision: Constraints as first-class objects (not edge properties)
   - Impact: Enables versioning, reuse, conflict detection
   - Confidence: HIGH (unanimous, strong technical rationale)

---

## Migration Notes

### Future Migrations Anticipated:
1. **Python → Rust (V2)**
   - When: After V1 validation (Year 2+)
   - Trigger: Performance bottlenecks, need for WASM builds
   - Scope: Rewrite core kernel, maintain Python bindings (PyO3)
   - Risk: HIGH (architectural assumptions may not transfer)

2. **Postgres → Postgres + Neo4j (Hybrid)**
   - When: When traversal queries dominate (TBD based on metrics)
   - Trigger: Deep traversal (50+ levels) performance issues
   - Scope: Add Neo4j for graph structure, keep Postgres for provenance
   - Risk: MEDIUM (cross-database query complexity)

3. **Monolith → Microservices (V3)**
   - When: After enterprise adoption (Year 3+)
   - Trigger: Scale demands, multi-tenancy requirements
   - Scope: Split into services (Graph, Solver, Validation, API)
   - Risk: LOW (designed with service boundaries in mind)

---

## Versioning Philosophy

**Semantic Versioning with Context:**
- Major version changes: Breaking TessIR spec or API changes
- Minor version changes: New features, backward-compatible
- Patch version changes: Bug fixes, documentation
- Pre-release labels: Communicate stability clearly

**Stability Guarantees:**
- `0.x.x`: No stability guarantees, rapid iteration
- `1.x.x`: TessIR spec stable, backward-compatible changes only
- `2.x.x+`: Production-grade, enterprise SLAs

---

**Last Updated:** 2026-01-19  
**Next Update:** After Phase 0 completion (TessIR spec + canonical suite)

---

## Links

- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
