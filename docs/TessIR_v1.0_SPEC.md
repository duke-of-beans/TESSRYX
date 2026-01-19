# TessIR v1.0 Specification
**TESSRYX Intermediate Representation - Formal Specification**

**Status:** DRAFT (Phase 0 - Outline)  
**Version:** 1.0.0-draft  
**Last Updated:** 2026-01-19  
**Authors:** David Kirsch, Genius Council (GPT, Gemini, Claude)

---

## Abstract

TessIR (TESSRYX Intermediate Representation) is an open standard for representing dependencies, constraints, and their associated metadata in a domain-agnostic, formally verifiable manner. This specification defines the core primitives, data structures, constraint types, and operations that enable universal dependency intelligence.

**Key Design Goals:**
1. **Domain-Agnostic:** Works for software, hardware, operations, construction, supply chain
2. **Formally Verifiable:** All plans can be proven valid or explained as impossible
3. **Evidence-Based:** Every relationship has provenance and confidence
4. **Versionable:** Git-like operations for dependency state
5. **Composable:** Hierarchical entities, constraint templates, domain packs

---

## Table of Contents

1. [Core Primitives](#core-primitives)
2. [Entity Schema](#entity-schema)
3. [Relation Types](#relation-types)
4. [Constraint System](#constraint-system)
5. [Contract Model](#contract-model)
6. [Assumption Schema](#assumption-schema)
7. [Provenance Model](#provenance-model)
8. [Version Control](#version-control)
9. [Domain Packs](#domain-packs)
10. [Operations](#operations)
11. [Serialization Format](#serialization-format)
12. [Conformance](#conformance)

---

## 1. Core Primitives

TessIR defines seven core primitives that form the foundation of all dependency representations:

### 1.1 Entity
A discrete unit that can participate in dependencies (packages, tasks, components, resources).

### 1.2 Relation
A typed connection between entities that represents a dependency relationship.

### 1.3 Constraint
A first-class rule that governs valid entity states or sequences.

### 1.4 Contract
A rich specification of preconditions, postconditions, and invariants for a relation.

### 1.5 Assumption
An explicit statement about the world that may be uncertain or time-limited.

### 1.6 Provenance
Metadata tracking the source, evidence, and confidence of any assertion.

### 1.7 Version
A snapshot of dependency state with commit/branch/merge semantics.

---

## 2. Entity Schema

### 2.1 Entity Definition

```typescript
interface Entity {
  id: UUID;                    // Unique identifier
  type: EntityType;            // Domain-specific type
  name: string;                // Human-readable name
  version?: string;            // Optional version string
  parent?: UUID;               // Hierarchical composition
  children?: UUID[];           // Child entities (for bundles)
  metadata: Record<string, any>;  // Extensible properties
  created_at: DateTime;
  updated_at: DateTime;
}
```

### 2.2 EntityType System

**Base Types (Universal):**
- `component` - Generic building block
- `resource` - Consumable or capacity-limited
- `task` - Work item or process step
- `gate` - Checkpoint or decision point

**Domain Pack Extension:**
Domain packs extend with specific types:
```yaml
# Software Dev Pack
entity_types:
  - package       # extends: component
  - service       # extends: component
  - database      # extends: resource
  - deployment    # extends: task
  
# Automotive Pack
entity_types:
  - part          # extends: component
  - subsystem     # extends: component
  - tool          # extends: resource
  - installation  # extends: task
```

### 2.3 Hierarchical Composition

Entities can form parent-child relationships:
```
Vehicle (parent)
  ├── Powertrain (child, parent)
  │   ├── Engine (child)
  │   ├── Transmission (child)
  │   └── Driveshaft (child)
  └── Electrical (child, parent)
      ├── Battery (child)
      └── Alternator (child)
```

**Semantics:**
- Changes to parent MAY propagate to children
- Constraints on parent MAY apply to children
- Deleting parent REQUIRES handling children

---

## 3. Relation Types

### 3.1 Relation Definition

```typescript
interface Relation {
  id: UUID;
  type: RelationType;       // Semantic relationship type
  from_entity: UUID;        // Source entity
  to_entity: UUID;          // Target entity
  strength: number;         // 0.0-1.0 (for probabilistic)
  contract?: Contract;      // Rich dependency contract
  provenance: Provenance;   // Evidence and confidence
  created_at: DateTime;
  updated_at: DateTime;
}
```

### 3.2 Core Relation Types (Universal)

**Dependency Relations:**
- `requires` - A needs B to function
- `enables` - A makes B possible
- `blocks` - A prevents B
- `conflicts` - A and B are mutually exclusive

**Temporal Relations:**
- `precedes` - A must happen before B
- `follows` - A must happen after B
- `concurrent` - A and B can/must happen simultaneously

**Compositional Relations:**
- `contains` - A is composed of B
- `part_of` - Inverse of contains
- `replaces` - A is a substitute for B

### 3.3 Relation Strength

**Strength Values:**
- `1.0` - Hard dependency (deterministic)
- `0.5-0.99` - Probabilistic dependency
- `0.01-0.49` - Weak/optional dependency
- `0.0` - No dependency (used for removals)

**Example:**
```json
{
  "type": "requires",
  "from_entity": "turbo_kit",
  "to_entity": "fuel_upgrade",
  "strength": 0.85,
  "provenance": {
    "confidence": 0.85,
    "note": "Most builds need fuel upgrade, some stock OK if boost <8 PSI"
  }
}
```

---

## 4. Constraint System

### 4.1 Constraint Definition

```typescript
interface Constraint {
  id: UUID;
  type: ConstraintType;
  entities: UUID[];              // Entities involved
  parameters: Record<string, any>;  // Type-specific params
  priority: Priority;            // Hard, Soft, Preference
  provenance: Provenance;
  scope?: Scope;                 // Context where this applies
  created_at: DateTime;
}
```

### 4.2 Core Constraint Types (V1)

#### 4.2.1 Precedence Constraint
A must complete before B starts.

```typescript
interface PrecedenceConstraint {
  type: "precedence";
  before: UUID;
  after: UUID;
  min_gap?: Duration;  // Minimum time between
  max_gap?: Duration;  // Maximum time between
}
```

#### 4.2.2 Mutual Exclusion (Mutex)
A and B cannot co-occur.

```typescript
interface MutexConstraint {
  type: "mutex";
  entities: UUID[];  // All mutually exclusive
  scope: "state" | "time" | "space";
}
```

#### 4.2.3 Choice Constraint
Exactly N of M entities must be selected.

```typescript
interface ChoiceConstraint {
  type: "choice";
  entities: UUID[];
  min_select: number;  // At least this many
  max_select: number;  // At most this many
}
```

#### 4.2.4 Time Window Constraint
Entity must occur within temporal bounds.

```typescript
interface TimeWindowConstraint {
  type: "time_window";
  entity: UUID;
  earliest: DateTime;
  latest: DateTime;
}
```

#### 4.2.5 Resource Capacity Constraint
Maximum concurrent usage of a resource.

```typescript
interface ResourceCapacityConstraint {
  type: "resource_capacity";
  resource: UUID;
  tasks: UUID[];
  max_concurrent: number;
}
```

#### 4.2.6 Conditional Constraint
If X then Y (context-dependent).

```typescript
interface ConditionalConstraint {
  type: "conditional";
  condition: Condition;  // Boolean expression
  then_constraint: Constraint;
  else_constraint?: Constraint;
}
```

### 4.3 Constraint Priority

```typescript
enum Priority {
  HARD = "hard",       // MUST be satisfied (infeasible if violated)
  SOFT = "soft",       // SHOULD be satisfied (optimize for)
  PREFERENCE = "pref"  // NICE TO satisfy (lowest priority)
}
```

### 4.4 Constraint Scope

Constraints can be context-dependent:

```typescript
interface Scope {
  applies_when: Condition[];  // Boolean expressions
  domains: string[];          // Which domain packs
  versions: string[];         // Which entity versions
  geographic?: string;        // Regional applicability
  temporal?: TimeRange;       // Time period
}
```

**Example:**
```json
{
  "type": "precedence",
  "before": "painting",
  "after": "sanding",
  "scope": {
    "applies_when": ["ambient_temp > 50F", "humidity < 70%"],
    "geographic": "outdoor_only"
  }
}
```

---

## 5. Contract Model

### 5.1 Contract Definition

Dependencies are contracts with formal specifications:

```typescript
interface Contract {
  preconditions: Condition[];    // Must be true before
  postconditions: Condition[];   // Will be true after
  invariants: Condition[];       // Must stay true throughout
  failure_modes: FailureMode[];  // What can go wrong
  scope: Scope;                  // Context where valid
}
```

### 5.2 Condition System

```typescript
interface Condition {
  expression: string;       // Boolean expression
  language: "python" | "z3" | "custom";
  variables: Record<string, Type>;
}
```

**Example:**
```json
{
  "expression": "engine.torque <= transmission.max_torque",
  "language": "python",
  "variables": {
    "engine.torque": "number",
    "transmission.max_torque": "number"
  }
}
```

### 5.3 Failure Modes

```typescript
interface FailureMode {
  condition: Condition;       // When this fails
  impact: ImpactLevel;        // Severity
  detectability: number;      // 0.0-1.0 (how easily caught)
  mitigation?: string[];      // How to prevent/fix
  blast_radius?: UUID[];      // What else fails
}
```

---

## 6. Assumption Schema

### 6.1 Assumption Definition

Explicit tracking of uncertain beliefs:

```typescript
interface Assumption {
  id: UUID;
  statement: string;              // Human-readable
  confidence: number;             // 0.0-1.0
  evidence: Evidence[];
  expiry_date?: DateTime;         // When to re-validate
  owner: UUID;                    // Who made this assumption
  impact_if_false: ImpactAssessment;
  alternatives?: string[];        // Other possible values
  created_at: DateTime;
}
```

### 6.2 Impact Assessment

```typescript
interface ImpactAssessment {
  affected_entities: UUID[];
  cost_impact?: Money;
  time_impact?: Duration;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  invalidated_plans?: UUID[];
  required_actions?: string[];
}
```

**Example:**
```json
{
  "statement": "Supplier X delivers within 14 days",
  "confidence": 0.85,
  "evidence": ["last_6_months_avg", "supplier_contract_2025"],
  "expiry_date": "2026-06-30",
  "impact_if_false": {
    "time_impact": "+3 weeks",
    "cost_impact": "$12,000",
    "risk_level": "HIGH",
    "required_actions": ["find_alternative_supplier", "expedite_shipping"]
  }
}
```

---

## 7. Provenance Model

### 7.1 Provenance Definition

Trust infrastructure for every assertion:

```typescript
interface Provenance {
  source: Source;
  evidence: Evidence[];
  confidence: number;          // 0.0-1.0
  asserted_by: UUID;           // User/system
  asserted_at: DateTime;
  last_validated?: DateTime;
  validation_method?: ValidationMethod;
  scope?: Scope;
  conflicts?: UUID[];          // Other provenances this contradicts
}
```

### 7.2 Source Types

```typescript
enum Source {
  USER_INPUT = "user_input",           // Manual entry
  DOC_IMPORT = "doc_import",           // Extracted from docs
  MEASUREMENT = "measurement",         // Empirical observation
  TEMPLATE = "template",               // Domain pack default
  COMMUNITY = "community",             // Crowd-sourced
  INFERRED = "inferred",               // Derived by system
  EXTERNAL_API = "external_api"        // Third-party data
}
```

### 7.3 Evidence Structure

```typescript
interface Evidence {
  type: "document" | "measurement" | "historical" | "expert";
  reference: string;           // URL, citation, identifier
  excerpt?: string;            // Relevant quote
  timestamp?: DateTime;
  confidence_contribution: number;  // How much this adds to confidence
}
```

### 7.4 Confidence Propagation

**Rules for confidence through chains:**
- Single path: Use minimum confidence in chain
- Multiple paths: Use maximum confidence across paths
- Conflicts: Reduce confidence based on disagreement

*Note: Detailed propagation algorithm TBD in implementation phase*

---

## 8. Version Control

### 8.1 Commit Model

```typescript
interface Commit {
  id: UUID;
  parent?: UUID;               // Parent commit (null for initial)
  author: UUID;
  message: string;
  timestamp: DateTime;
  changeset: ChangeSet;
  signature?: string;          // Cryptographic (future)
}
```

### 8.2 ChangeSet Structure

```typescript
interface ChangeSet {
  added: {
    entities?: Entity[];
    relations?: Relation[];
    constraints?: Constraint[];
  };
  removed: {
    entity_ids?: UUID[];
    relation_ids?: UUID[];
    constraint_ids?: UUID[];
  };
  modified: {
    entities?: EntityChange[];
    relations?: RelationChange[];
    constraints?: ConstraintChange[];
  };
}
```

### 8.3 Branch and Tag

```typescript
interface Branch {
  id: UUID;
  name: string;
  head: UUID;                  // Current commit
  scenario?: Scenario;         // "What-if" parameters
  created_at: DateTime;
}

interface Tag {
  id: UUID;
  name: string;
  commit: UUID;
  verified: boolean;           // Community verification
  created_at: DateTime;
}
```

### 8.4 Diff Calculation

```typescript
interface Diff {
  from_commit: UUID;
  to_commit: UUID;
  structural_diff: ChangeSet;
  impact_assessment: ImpactAssessment;
  blast_radius: UUID[];        // Affected entities
  invalidated_plans?: UUID[];
}
```

---

## 9. Domain Packs

### 9.1 Domain Pack Structure

```typescript
interface DomainPack {
  name: string;
  version: string;
  description: string;
  ontology: Ontology;
  constraint_templates: ConstraintTemplate[];
  scoring_weights: ScoringWeights;
  validated_library: ValidatedLibrary;
  importers: Importer[];
  exporters: Exporter[];
  canonical_examples: Example[];
}
```

### 9.2 Ontology Definition

```typescript
interface Ontology {
  entity_types: EntityTypeDefinition[];
  relation_types: RelationTypeDefinition[];
  constraint_types?: ConstraintTypeDefinition[];  // Domain-specific
}
```

### 9.3 Validated Library

Pre-verified dependencies with provenance:

```typescript
interface ValidatedLibrary {
  relations: Map<string, Relation>;     // Key: "from_id:to_id"
  confidence_threshold: number;         // Minimum to include
  verification_method: string;
  last_updated: DateTime;
  contributors: UUID[];
}
```

---

## 10. Operations

### 10.1 Core Operations (Must Support)

#### Create
```
create_entity(entity: Entity) -> UUID
create_relation(relation: Relation) -> UUID
create_constraint(constraint: Constraint) -> UUID
```

#### Read
```
get_entity(id: UUID) -> Entity
get_relations(entity_id: UUID, direction: "in" | "out" | "both") -> Relation[]
get_constraints(entity_ids: UUID[]) -> Constraint[]
```

#### Update
```
update_entity(id: UUID, changes: Partial<Entity>) -> Entity
update_relation(id: UUID, changes: Partial<Relation>) -> Relation
```

#### Delete
```
delete_entity(id: UUID) -> boolean
delete_relation(id: UUID) -> boolean
delete_constraint(id: UUID) -> boolean
```

### 10.2 Graph Operations

```
detect_cycles() -> SCC[]
topological_sort() -> UUID[] | Error
blast_radius(changed: UUID[]) -> UUID[]
critical_path(start: UUID, end: UUID) -> Path | null
```

### 10.3 Solver Operations

```
solve(
  entities: Entity[],
  constraints: Constraint[],
  objectives: Objective[]
) -> Solution | Error

validate_plan(plan: Plan) -> ValidationResult

explain_infeasibility(
  constraints: Constraint[]
) -> MinimalUnsatCore
```

### 10.4 Version Operations

```
commit(message: string, changeset: ChangeSet) -> Commit
branch(name: string, scenario?: Scenario) -> Branch
merge(from_branch: UUID, to_branch: UUID) -> Commit | Conflict
diff(from_commit: UUID, to_commit: UUID) -> Diff
lockfile_snapshot() -> Lockfile
```

---

## 11. Serialization Format

### 11.1 Primary Format: JSON

All TessIR objects MUST be serializable to JSON.

**Example Entity:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "package",
  "name": "express",
  "version": "4.18.2",
  "metadata": {
    "language": "javascript",
    "license": "MIT"
  },
  "created_at": "2026-01-19T10:30:00Z"
}
```

### 11.2 Compact Binary Format (Future)

For high-performance scenarios, define Protocol Buffers schema.

### 11.3 Human-Readable Format (YAML)

For documentation and hand-editing:
```yaml
entity:
  type: package
  name: express
  version: 4.18.2
  metadata:
    language: javascript
    license: MIT
```

---

## 12. Conformance

### 12.1 Conformance Levels

**Level 1 (Minimal):**
- Entities, Relations, Basic Constraints
- Core operations (CRUD)
- JSON serialization

**Level 2 (Standard):**
- Full constraint system (20+ types)
- Provenance tracking
- Graph operations
- Version control (commits, branches)

**Level 3 (Full):**
- Solver integration
- Proof certificates
- Domain packs
- All operations

### 12.2 Conformance Testing

Implementations MUST pass canonical test suite (50 scenarios).

---

## Status & Next Steps

**Current Status:** DRAFT (Outline complete, details TBD)

**Phase 0 Deliverables:**
- [ ] Complete constraint type taxonomy (20-30 types)
- [ ] Finalize confidence propagation algorithm
- [ ] Define all core operations precisely
- [ ] Write 10 complete examples
- [ ] Peer review + public feedback

**Future Versions:**
- **v1.1:** Add probabilistic constraints, stochastic solving
- **v1.2:** Add temporal logic, time-series dependencies
- **v2.0:** Add machine learning integration, pattern inference

---

## References

- [DNA.md](../DNA.md) - Project principles
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [Genius Council Synthesis](../GCsynth2%20-%20Genius%20Council%20Synthesis.md) - Strategic reviews

---

**Contributors:**
- David Kirsch (Author)
- GPT-4 (Genius Council - Architecture review)
- Gemini 2.0 (Genius Council - Technical recommendations)
- Claude (Anthropic - Synthesis and refinement)

**Last Updated:** 2026-01-19  
**Next Review:** After canonical test suite creation
