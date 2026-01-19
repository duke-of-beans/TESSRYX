# TESSRYX Architecture
**Technical Architecture Overview**

---

## Architecture Philosophy

**Core Principle:** Build a formally specified, constraint-first, evidence-backed, versioned dependency planning kernel with clear separation between:
- Universal primitives (TessIR + Kernel)
- Domain-specific knowledge (Domain Packs)
- Integration surface (Adapters + APIs)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TESSRYX Platform                         │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │              TessIR (Constitution)                 │    │
│  │  - Entities, Relations, Constraints, Contracts    │    │
│  │  - Assumptions, Provenance, Versions              │    │
│  └───────────────────────────────────────────────────┘    │
│                           ↓                                 │
│  ┌───────────────────────────────────────────────────┐    │
│  │              The Kernel (Core Engine)              │    │
│  │                                                    │    │
│  │  GraphOps     PlanOps      ExplainOps            │    │
│  │  (SCC, blast) (Solving)    (Proofs)              │    │
│  └───────────────────────────────────────────────────┘    │
│                           ↓                                 │
│  ┌───────────────────────────────────────────────────┐    │
│  │         Trust + Change Layers                      │    │
│  │  - Evidence Ledger  - Version Graph               │    │
│  │  - Validation       - Diff Engine                 │    │
│  └───────────────────────────────────────────────────┘    │
│                           ↓                                 │
│  ┌───────────────────────────────────────────────────┐    │
│  │              Storage + Persistence                 │    │
│  │  - PostgreSQL (System of Record)                  │    │
│  │  - (Future: Neo4j for graph traversal)            │    │
│  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           ↓
        ┌──────────────────────────────────────────┐
        │         Integration Layer                 │
        │  - REST/GraphQL APIs                      │
        │  - Domain Pack adapters                   │
        │  - External tool connectors               │
        └──────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                             │
│  - SDKs (Python, future: Rust, JS)                         │
│  - CLI tools                                                │
│  - IDE plugins / Dependency linters                         │
│  - GitHub Actions / CI/CD integrations                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: TessIR (The Constitution)

**Purpose:** Formal intermediate representation - the "bytecode" of dependency intelligence.

### Core Primitives:

#### Entities
```python
Entity {
    id: UUID
    type: EntityType  # e.g., "package", "service", "component", "task"
    name: String
    version: String?
    parent: UUID?  # Hierarchical composition
    metadata: Dict[String, Any]
    created_at: DateTime
}
```

#### Relations
```python
Relation {
    id: UUID
    type: RelationType  # "requires", "conflicts", "enables", etc.
    from_entity: UUID
    to_entity: UUID
    strength: Float  # 0.0-1.0 (for probabilistic deps)
    contract: Contract  # See below
    created_at: DateTime
}
```

#### Contracts (Dependencies as Rich Objects)
```python
Contract {
    preconditions: List[Condition]     # What must be true before
    postconditions: List[Condition]    # What will be true after
    invariants: List[Condition]        # What stays constant
    failure_modes: List[FailureMode]   # What can go wrong
    scope: Dict[String, Any]           # Context where contract applies
}
```

#### Constraints (First-Class Objects)
```python
Constraint {
    id: UUID
    type: ConstraintType  # Precedence, Mutex, Choice, TimeWindow, etc.
    entities: List[UUID]  # Entities involved
    parameters: Dict[String, Any]  # Type-specific params
    priority: Priority  # Hard, Soft, Preference
    provenance: Provenance  # See below
}

# Core constraint types (V1):
- Precedence(A, B)           # A before B
- Mutex(A, B)                # A and B cannot co-occur
- RequiresOneOf(A, [B,C,D])  # A needs exactly one alternative
- TimeWindow(A, start, end)  # Temporal bounds
- ResourceCapacity(R, tasks, limit)  # Capacity constraints
- Conditional(if X then Y)   # Context-dependent
```

#### Assumptions (Explicit Unknowns)
```python
Assumption {
    id: UUID
    statement: String  # Human-readable assumption
    confidence: Float  # 0.0-1.0
    evidence: List[Evidence]
    expiry_date: DateTime?
    owner: UUID  # Who made this assumption
    impact_if_false: ImpactAssessment
}
```

#### Provenance (Trust Infrastructure)
```python
Provenance {
    source: Source  # user_input, doc_import, measurement, template, community
    evidence: List[Evidence]  # Links to supporting docs/data
    confidence: Float  # 0.0-1.0
    asserted_by: UUID  # User/system that added this
    asserted_at: DateTime
    last_validated: DateTime
    validation_method: ValidationMethod  # manual, automated, cross_reference
    scope: Dict[String, Any]  # Context where this applies
    conflicts: List[UUID]  # Other provenances this contradicts
}
```

#### Versions (Git-Like)
```python
Commit {
    id: UUID
    parent: UUID?  # Parent commit
    author: UUID
    message: String
    timestamp: DateTime
    changeset: ChangeSet  # What changed
    signature: String?  # Cryptographic signature (future)
}

Branch {
    id: UUID
    name: String
    head: UUID  # Current commit
    scenario: Dict[String, Any]  # "What-if" parameters
}

Tag {
    id: UUID
    name: String  # e.g., "automotive-pack-v1.2"
    commit: UUID
    verified: Boolean  # Community verification badge
}
```

---

## Layer 2: The Kernel (Core Engine)

### GraphOps (Deterministic Graph Operations)

**Responsibilities:**
- Cycle detection (Strongly Connected Components)
- Topological ordering (where possible)
- Reachability queries ("Can I get from A to B?")
- Impact analysis ("What's affected if X changes?")
- Critical path calculation (when schedulable)

**Implementation (V1):** Python + NetworkX  
**Implementation (V2):** Rust (performance-critical paths)

**Key Algorithms:**
```python
def detect_cycles(graph: Graph) -> List[SCC]:
    """Tarjan's algorithm for strongly connected components"""
    
def blast_radius(graph: Graph, changed_nodes: Set[UUID]) -> BlastRadius:
    """Forward + backward reachability from changed nodes"""
    
def critical_path(graph: Graph, constraints: List[Constraint]) -> Path:
    """Longest path in DAG (when constraints allow scheduling)"""
```

### PlanOps (Constraint Solving + Optimization)

**Responsibilities:**
- Feasibility checking ("Is this plan valid?")
- Optimal plan generation ("Best sequence given objectives")
- Alternative generation ("Show me 3 different valid plans")
- Minimal unsat core ("Why is this impossible?")

**Solvers (V1):**
- **OR-Tools CP-SAT:** Discrete scheduling, resource allocation, sequencing
- **Z3 (SMT):** Logical constraints, policy enforcement, conflict detection

**Key Operations:**
```python
def solve(
    entities: List[Entity],
    constraints: List[Constraint],
    objectives: List[Objective]
) -> SolutionSet:
    """
    Returns:
    - optimal_plan: Plan
    - alternatives: List[Plan] (top 3)
    - proof_certificate: Certificate
    """

def explain_infeasibility(
    constraints: List[Constraint]
) -> MinimalUnsatCore:
    """
    Returns smallest set of conflicting constraints
    + suggested relaxations
    """
```

### ExplainOps (Human-Readable Proofs)

**Responsibilities:**
- Generate human-readable explanations for every outcome
- Minimal conflict sets (when infeasible)
- "Why-not" explanations ("Why can't I do X?")
- Recommendation narratives (with alternatives)

**Key Outputs:**
```python
Explanation {
    type: ExplanationType  # Success, Failure, Warning
    what: String  # What happened
    why: String  # Root cause
    how_to_fix: List[Recommendation]  # Actionable options
    evidence: List[Evidence]  # Supporting provenance
    visual: Graph?  # Optional graph rendering
}
```

---

## Layer 3: Trust + Change Layers

### Evidence Ledger (Trust Infrastructure)

**Responsibilities:**
- Store all provenance metadata
- Cross-verification ("10K builds confirm this dependency")
- Confidence score propagation through chains
- Community validation workflows

**Schema:**
```sql
CREATE TABLE evidence (
    id UUID PRIMARY KEY,
    relation_id UUID REFERENCES relations(id),
    source TEXT NOT NULL,  -- 'manual', 'doc', 'measurement', etc.
    evidence_links JSONB,  -- Array of URLs/references
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    asserted_by UUID,
    asserted_at TIMESTAMP,
    last_validated TIMESTAMP,
    validation_method TEXT
);
```

### Version Graph (Git for Dependencies)

**Responsibilities:**
- Commit/branch/merge operations
- Diff calculation (structural + semantic)
- Blast radius on changes
- Lockfile generation/comparison

**Key Operations:**
```python
def commit(
    message: String,
    changeset: ChangeSet
) -> Commit:
    """Create new commit with changes"""

def diff(
    from_commit: UUID,
    to_commit: UUID
) -> Diff:
    """
    Returns:
    - added: List[Entity | Relation | Constraint]
    - removed: List[UUID]
    - modified: List[ChangeRecord]
    - blast_radius: ImpactAssessment
    """

def lockfile_snapshot() -> Lockfile:
    """Pin current state (entities, relations, constraints, hash)"""
```

---

## Layer 4: Storage + Persistence

### V1 Architecture: Postgres + NetworkX

**PostgreSQL Tables (Core):**
```sql
-- Entities
CREATE TABLE entities (
    id UUID PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    version TEXT,
    parent_id UUID REFERENCES entities(id),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Relations
CREATE TABLE relations (
    id UUID PRIMARY KEY,
    type TEXT NOT NULL,
    from_entity UUID REFERENCES entities(id),
    to_entity UUID REFERENCES entities(id),
    strength FLOAT DEFAULT 1.0,
    contract JSONB,  -- Serialized Contract object
    created_at TIMESTAMP DEFAULT NOW()
);

-- Constraints
CREATE TABLE constraints (
    id UUID PRIMARY KEY,
    type TEXT NOT NULL,
    entities JSONB,  -- Array of UUIDs
    parameters JSONB,
    priority TEXT,
    provenance_id UUID REFERENCES provenance(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Provenance
CREATE TABLE provenance (
    id UUID PRIMARY KEY,
    source TEXT NOT NULL,
    evidence JSONB,
    confidence FLOAT,
    asserted_by UUID,
    asserted_at TIMESTAMP,
    last_validated TIMESTAMP,
    validation_method TEXT
);

-- Commits (Version control)
CREATE TABLE commits (
    id UUID PRIMARY KEY,
    parent_id UUID REFERENCES commits(id),
    author UUID,
    message TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),
    changeset JSONB  -- Serialized ChangeSet
);
```

**NetworkX Usage:**
- Load graph from Postgres into memory
- Run algorithms (SCC, critical path, reachability)
- Cache results for hot paths

### V2 Architecture: Hybrid (Postgres + Neo4j)

**When to migrate:** When traversal queries (50+ level deep hops) dominate workload.

**Division:**
- **Postgres:** Provenance, versioning, metadata, accounts, audit logs
- **Neo4j:** Graph structure, deep traversal, pattern matching
- **Sync strategy:** Event-driven (commits to Postgres → sync to Neo4j)

---

## Layer 5: Integration Layer

### APIs (V1)

**REST API (FastAPI):**
```python
# Core endpoints
POST /api/v1/graphs          # Create new graph
GET  /api/v1/graphs/{id}     # Get graph
POST /api/v1/constraints     # Add constraint
POST /api/v1/solve           # Run solver
POST /api/v1/validate        # Validate plan
GET  /api/v1/diff/{from}/{to}  # Get diff
```

**GraphQL (V2 - Future):**
For complex queries, graph exploration, nested resolution.

### Domain Packs

**Structure:**
```python
DomainPack {
    name: String  # "software-dev-pack", "automotive-pack"
    version: String
    ontology: Ontology  # Entity types, relation types
    constraint_templates: List[ConstraintTemplate]
    scoring_weights: Dict[String, Float]
    validated_library: Dict[String, Relation]  # Pre-verified dependencies
    importers: List[Importer]  # Adapters for external formats
    canonical_examples: List[Example]
}
```

**Example: Software Dev Pack**
```yaml
name: software-dev-pack
version: 1.0.0
ontology:
  entity_types:
    - package
    - service
    - library
  relation_types:
    - depends_on
    - conflicts_with
    - provides
importers:
  - npm_package_json
  - pip_requirements_txt
  - maven_pom_xml
```

---

## Technology Decisions

### V1 (Pragmatic - Months 1-12)
- **Why Python:** Fast iteration, mature ecosystem, AI-assisted development
- **Why NetworkX:** Battle-tested, comprehensive graph algorithms
- **Why OR-Tools:** Best-in-class CP-SAT solver, free, well-documented
- **Why Postgres:** Reliable, JSON support, mature tooling

### V2 (Production - Year 2+)
- **Why Rust:** C++-level performance, memory safety, WASM builds
- **Why Neo4j:** Native graph traversal, Cypher query language
- **Why gRPC:** High-performance, streaming support
- **Migration Strategy:** Rewrite kernel in Rust, maintain Python bindings via PyO3

---

## Performance Targets

### V1 Targets:
- Graph size: 10K nodes, 50K edges (in-memory NetworkX)
- Solver time: <10 seconds for typical constraints (100-500)
- API latency: <500ms (p95) for validation queries
- Diff calculation: <5 seconds for 1K changed nodes

### V2 Targets:
- Graph size: 1M+ nodes, 10M+ edges (Neo4j)
- Solver time: <30 seconds for complex constraints (1000+)
- API latency: <200ms (p95) for validation queries
- Deep traversal: <1 second for 50-level hops

---

## Security Considerations

### V1 (Basic):
- API key authentication
- HTTPS only
- Input validation
- SQL injection prevention (parameterized queries)

### V2 (Enterprise):
- SSO (SAML/OIDC)
- RBAC (Role-Based Access Control)
- Audit logging (immutable)
- Encryption at rest + in transit
- Data residency controls
- SOC2 compliance path

---

## Testing Strategy

### Unit Tests (Pytest):
- Every module has >80% coverage
- Property-based testing (Hypothesis) for core algorithms
- Canonical test suite (50 scenarios) as integration tests

### Integration Tests:
- API endpoint tests
- Database round-trip tests
- Solver integration tests

### Performance Tests:
- Benchmark suite for large graphs
- Regression detection (track solver times)
- Load testing for API endpoints

---

## Deployment Architecture

### V1 (Development):
```
Railway.app / Render.com
├── Web service (FastAPI)
├── PostgreSQL (managed)
└── Redis (optional caching)
```

### V2 (Production):
```
Kubernetes cluster
├── API Gateway (gRPC + GraphQL)
├── Graph Service (Neo4j)
├── Solver Service (OR-Tools + Z3)
├── Validation Service
├── PostgreSQL (managed, system of record)
└── Redis (cache + rate limiting)
```

---

## Next Steps

1. **Phase 0 (Current):** Complete TessIR v1.0 specification
2. **Phase 1:** Implement core in Python (TessIR + GraphOps + ExplainOps)
3. **Phase 2:** Integrate solvers (OR-Tools + Z3)
4. **Phase 3:** Add versioning + diff engine
5. **Phase 4:** Build API + persistence layer
6. **Phase 5:** Create Software Dev Domain Pack

---

## Leverage Strategy: Proven Patterns

TESSRYX accelerates development by porting battle-tested implementations from three production projects. See [STEAL_REGISTRY.md](../STEAL_REGISTRY.md) for complete details.

### Key Architectural Steals:

**Phase 1 (Immediate):**
- **S01:** Provenance Ledger from Consensus (~600 LOC) - Direct port for evidence tracking
- **S02:** Dependency Impact Analyzer from Eye-of-Sauron (~600 LOC) - Core algorithms for blast radius
- **S06:** Character Forensics from Eye-of-Sauron (~800 LOC) - Input validation

**Phase 2 (Months 4-6):**
- **S03:** Multi-Solver Orchestration from Consensus (~2,000 LOC) - OR-Tools + Z3 coordination
- **S04:** BullMQ Parallel Execution from Gregore (~1,500 LOC) - Worker pool management
- **S07:** Incremental Cache from Eye-of-Sauron (~400 LOC) - Hash-based result caching

**Phase 4 (Months 9-10):**
- **S18:** PostgreSQL Schema from Consensus (~800 LOC) - Complete database design
- **S08:** Trust Tier System from Gregore (~600 LOC) - Freemium feature gating

### Philosophy: LEAN-OUT
**Don't reinvent infrastructure.** Use proven tools (OR-Tools, Z3, NetworkX, FastAPI). Build only domain-specific INTELLIGENCE.

---

## References

- [DNA.md](../DNA.md) - Project principles
- [TessIR Specification](TessIR_v1.0_SPEC.md) - Formal spec (in progress)
- [ADR Index](ADR/) - Architecture decisions
- [STATUS.md](../STATUS.md) - Current state
- [STEAL_REGISTRY.md](../STEAL_REGISTRY.md) - Proven patterns to leverage
- [ROADMAP.md](../ROADMAP.md) - Timeline and milestones

---

**Last Updated:** 2026-01-19  
**Next Review:** After Phase 1 implementation
