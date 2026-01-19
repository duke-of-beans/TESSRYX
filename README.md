# TESSRYX
**Universal Dependency Intelligence Infrastructure**

[![Status](https://img.shields.io/badge/status-pre--alpha-red)](https://github.com/yourusername/tessryx)
[![Version](https://img.shields.io/badge/version-0.1.0--genesis-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-TBD-lightgrey)](LICENSE)

> *TESSRYX transforms dependency mapping from visualization into verification — enabling proof-carrying plans, change-impact prediction, and resilience testing for any complex system.*

---

## What is TESSRYX?

TESSRYX is the **open-standard intermediate representation (TessIR) + constraint solver + evidence ledger** that makes dependencies visible, verifiable, and versionable.

### The Problem

Dependency blindness costs $500B+ globally:
- **Software:** 94% of projects fail, $312K/year rework per team
- **Manufacturing:** 94% exceed budget 40%+, $18.4K avg overrun
- **Construction:** 67% over budget, delays cascade unpredictably
- **Operations:** Wrong sequencing = catastrophic failures

Most tools **map** dependencies (visualization). TESSRYX **validates** them (verification).

### The Solution

- **TessIR:** Formal intermediate representation (the "bytecode" of dependency intelligence)
- **Constraint Solver:** Proves plans are valid OR explains why they're impossible
- **Evidence Ledger:** Every relationship has provenance, confidence, validation history
- **Version Graph:** Git-like commits/branches/diffs for dependency state
- **Explanation Engine:** Every failure returns what/why/how-to-fix

---

## Key Features

### 🔍 **Dependency Validation**
Not just "A requires B" — TESSRYX models dependencies as **contracts** with preconditions, postconditions, invariants, and failure modes.

### 🧩 **Constraint Solving**
Proves plans are feasible OR provides **minimal unsat core** (exactly which constraints conflict and why).

### 📜 **Proof-Carrying Plans**
Every plan comes with a machine-checkable certificate. Disputes resolved by proof, not argument.

### 🔄 **Change-Impact Prediction**
"If I change X, what breaks?" — Blast radius analysis, cost/time/risk quantification.

### 🌳 **Version Control**
Git-like operations (commit, branch, merge, diff) for dependency state. Lockfiles for reality.

### 🔬 **Evidence-Based Trust**
Every relationship has provenance, confidence score, validation history. Community-verified libraries.

---

## Quick Start

**Note:** TESSRYX is in pre-alpha (Phase 0: Foundation). No implementation yet.

### Phase 0 (Current - Weeks 1-4)
- [ ] TessIR v1.0 specification
- [ ] Canonical test suite (50 scenarios)
- [ ] Architecture Decision Records

### Phase 1 (Months 1-3)
- [ ] Core implementation (Python)
- [ ] GraphOps primitives
- [ ] Explanation engine

### Phase 2 (Months 4-6)
- [ ] Constraint solver integration
- [ ] Proof certificates
- [ ] Minimal unsat explanations

---

## Example Use Cases

### Software Development
```
TESSRYX: "If you upgrade package X to v2.0..."
  → 3 downstream packages will break
  → 12 services affected
  → Estimated migration: 40 hours
  → Alternative: Use X v1.9 (compatible with all)
  
  [One-click: show migration plan]
```

### IT Operations
```
TESSRYX: "Pre-validating change request #4521..."
  ✗ CONSTRAINT VIOLATION: Circular dependency detected
  
  Root cause: Server A depends on Server B (new) + Server B depends on Server A (existing)
  
  Fix options:
  1. Break circular dep (add load balancer)
  2. Stagger rollout (A first, then B)
  3. Reject change (violates architecture policy)
```

### Manufacturing / ERP
```
TESSRYX: "Engineering Change Order #2401 impact analysis..."
  Blast radius: 47 components, 12 work orders
  Cost impact: +$18K
  Time impact: +7 days
  Risk: MEDIUM (reversible if caught at assembly step 14)
  
  Recommendation: Supplier C alternative (comparable spec, -$12K, -5 days)
```

---

## Architecture

### Core Components:
1. **TessIR (The Constitution):** Formal intermediate representation
2. **The Kernel:** GraphOps + PlanOps + ExplainOps
3. **The Trust Layer:** Evidence Ledger + Validation History
4. **The Change Layer:** Version Graph + Diff Engine

### Technology Stack (V1):
- **Language:** Python 3.12+
- **Graph:** NetworkX
- **Solver:** OR-Tools (CP-SAT) + Z3 (SMT)
- **Database:** PostgreSQL
- **API:** FastAPI + Pydantic
- **Testing:** Pytest + Hypothesis

### Technology Stack (V2 - Future):
- **Kernel:** Rust (performance + WASM)
- **Graph DB:** Neo4j/Neptune (when traversal dominates)
- **API:** gRPC + GraphQL
- **Frontend:** React + Cytoscape.js

---

## Positioning

**What TESSRYX Is:**
- The "AWS of Dependency Intelligence" (infrastructure, not application)
- The "Git for Dependencies" (version control for complex systems)
- The "Constraint Solver for Reality" (formal verification)

**What TESSRYX Is NOT:**
- A project management tool (not competing with Jira/Asana)
- A visualization tool (graphs are output, not product)
- A domain-specific tool (we're infrastructure)
- An AI hallucination engine (we prove, not guess)

---

## Roadmap

### Phase 0: The Constitution (Weeks 1-4)
- TessIR v1.0 specification (public open standard)
- Canonical test suite (50 scenarios)
- Architecture Decision Records

### Phase 1: The Kernel (Months 1-3)
- TessIR implementation (Python)
- GraphOps (SCC, blast radius, reachability)
- Explanation engine scaffolding

### Phase 2: Solver Integration (Months 4-6)
- OR-Tools + Z3 integration
- Constraint solving
- Proof certificates

### Phase 3: Versioning + Diff (Months 7-8)
- Git-like operations
- Blast radius analysis
- Lockfiles

### Phase 4: API + Persistence (Months 9-10)
- FastAPI implementation
- PostgreSQL schema
- SDK (Python)

### Phase 5: Software Dev Domain Pack (Months 11-12)
- Package manager adapters
- GitHub Action integration
- Freemium launch

### Phase 6+: Expansion (Year 2+)
- IT Operations (ServiceNow integration)
- ERP/Manufacturing (SAP/Oracle connectors)
- Construction/AEC (BIM integration)
- Rust V2 kernel (performance + WASM)

---

## Documentation

- [DNA.md](DNA.md) - Project identity, core principles, strategic positioning
- [STATUS.md](STATUS.md) - Current state tracker
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [SESSION_LOG.md](SESSION_LOG.md) - Detailed session tracking
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Technical architecture (coming soon)
- [TessIR Specification](docs/TessIR_v1.0_SPEC.md) - Core specification (coming soon)
- [Architecture Decision Records](docs/ADR/) - Major decisions (coming soon)

---

## Contributing

**Note:** TESSRYX is in pre-alpha. Not yet ready for contributions.

Once Phase 1 is complete, we'll welcome:
- Bug reports
- Feature requests
- Documentation improvements
- Domain Pack contributions
- Test scenario submissions

---

## License

**TBD** - Will be determined before Phase 1 release.

Planned approach:
- **Open:** TessIR specification, core implementations, basic tools
- **Paid:** Domain Packs (verified), Enterprise connectors, SaaS hosting

---

## Project Philosophy

**"We don't prevent failures. We make them predictable, detectable, and recoverable."**

**"Dependency mapping is not the product. Dependency TRUTH is the product."**

**"Build once, build right. No technical debt. No shortcuts."**

---

## Contact

- **Developer:** David Kirsch
- **Project Repository:** [Coming soon]
- **Issues:** [Coming soon]
- **Discussions:** [Coming soon]

---

## Acknowledgments

**Genius Council (Strategic Architecture Reviews):**
- GPT-4 (OpenAI) - Comprehensive architecture critique
- Gemini 2.0 (Google) - Technical implementation recommendations
- Claude (Anthropic) - Synthesis and refinement

Special thanks to the AI councils for their rigorous, unfiltered feedback that shaped TESSRYX's foundational architecture.

---

## Status

**Current Phase:** Foundation (Phase 0)  
**Version:** 0.1.0-genesis  
**Status:** Pre-Alpha (Architecture & Planning)  
**Last Updated:** 2026-01-19  

**Next Milestone:** TessIR v1.0 specification complete (Target: Week 4)

---

**TESSRYX** - *Selling the courage to build complex things*
